# Start glueing together some stuff to see how it works
import yaml
import time
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from kubernetes import client, utils

from .utils import k8s_client


class ContainerImage:
    def __init__(self, language: str, tag: str = None):
        self.language = language
        self.tag =  tag if tag else str(uuid4())
        self.registry = "docker.io/tkhap/faas-func"

    def Build(self, context_path: str, k8s: client.ApiClient):
        builder_dict = render_manifest(
            "app/templates/",
            "kaniko.yaml.j2",
            {
                "tag": self.tag,
                "registry": self.registry,
                "context_sub_path": context_path,
            },
        )

        utils.create_from_dict(k8s, builder_dict, verbose=True)

        k8s_client.wait_for_completed(f"kaniko-{self.tag}", "default", 35)
        return



def render_manifest(dir_path: str, file_name: str, template_args: dict) -> dict:
    environment = Environment(loader=FileSystemLoader(dir_path))
    template = environment.get_template(file_name)
    rendered_manifest = template.render(template_args)

    return yaml.safe_load(rendered_manifest)


def create_knative_service(k8s: client.ApiClient, container: ContainerImage):
    service_dict = render_manifest(
        "app/templates/",
        "kn_service.yaml.j2",
        {
            "tag": container.tag,
            "language": container.language,
            "registry": container.registry,
        }
    )

    status = utils.create_from_dict(k8s, service_dict, verbose=True, apply=True)

    # Wait for route to come up, could possibly get the status of the service
    time.sleep(5)

    route = k8s_client.get_knative_route(f"{container.language}-{container.tag}", "default")
    url = route["status"]["url"]
    return url
