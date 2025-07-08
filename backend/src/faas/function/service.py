import time
import yaml
from typing import Any
from kubernetes import utils

from faas.container.models import ContainerImage
from faas.k8s.service import get_knative_route, get_k8s_custom_objects_client

def build_kn_service_manifest(container_image: ContainerImage) -> dict:
    """Constructs knative service manifest"""

    with open("templates/service.yaml") as f:
        manifest = yaml.safe_load(f)
    
    manifest["metadata"]["name"] = container_image.tag
    manifest["spec"]["template"]["spec"]["containers"]["image"] = f"{container_image.registry}:{container_image.tag}"

    return manifest


def create(k8s_client: Any, container_image: ContainerImage) -> str:
    """Creates the knative service"""

    service =  build_kn_service_manifest(container_image)

    status = utils.create_from_dict(k8s_client, service, verbose=True, apply=True)

    # TODO: Wait for route to come up
    time.sleep(5)

    route = get_knative_route(
        f"{container_image.tag}", "default"
    )
    url = route["status"]["url"]
    return url 


def delete(function_id: str):
    """Deletes knative function"""

    k8s_client = get_k8s_custom_objects_client()

    status = k8s_client.delete_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace="default",
        name=function_id,
        plural="services",
    )