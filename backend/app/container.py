import yaml
import os
import tarfile
import time
import boto3
from io import BytesIO
from botocore.exceptions import ClientError
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from kubernetes import client, utils

from .utils import k8s_client
from .config import settings


class ContainerImage:
    def __init__(self, language: str, tag: str = None):
        self.language = language
        self.tag = tag if tag else str(uuid4())
        if not settings.container_registry:
            raise ValueError("The 'container_registry' setting is missing or invalid.")
        self.registry = settings.container_registry
        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.s3_region_name,
        )

    def create_build_context(self, body: str, bucket: str) -> None:
        """Creates and uploads a build context to S3 compatible storage"""

        tar_file = f"{self.tag}.tar.gz"
        template_dir = "app/templates/function_templates/python/"

        with tarfile.open(tar_file, "w:gz") as tar:
            # Write handler
            data = body.encode("utf-8")
            file = BytesIO(data)
            info = tarfile.TarInfo("handler.py")
            info.size = len(data)
            tar.addfile(info, file)

            files = os.listdir(template_dir)
            for file in files:
                file_path = os.path.join(template_dir, file)
                tar.add(file_path, arcname=file)

        try:
            self.s3_client.upload_file(tar_file, bucket, tar_file)
        except ClientError as e:
            raise f"Error uploading {tar_file}: {str(e)}"
        finally:
            if os.path.exists(tar_file):
                os.remove(tar_file)

    def build(self, k8s: client.ApiClient) -> None:
        """Build container image using Kaniko"""
        builder_dict = render_manifest(
            "app/templates/",
            "kaniko.yaml.j2",
            {
                "tag": self.tag,
                "registry": self.registry,
                "bucket": "faas-platform-build-contexts",
                "context_path": f"{self.tag}.tar.gz",
            },
        )

        utils.create_from_dict(k8s, builder_dict, verbose=True)

        k8s_client.wait_for_completed(f"{self.tag}", "kaniko", 35)
        return


def render_manifest(dir_path: str, file_name: str, template_args: dict) -> dict:
    environment = Environment(loader=FileSystemLoader(dir_path))
    template = environment.get_template(file_name)
    rendered_manifest = template.render(template_args)

    return yaml.safe_load(rendered_manifest)


def create_knative_service(k8s: client.ApiClient, container: ContainerImage) -> str:
    service_dict = render_manifest(
        "app/templates/",
        "kn_service.yaml.j2",
        {
            "tag": container.tag,
            "language": container.language,
            "registry": container.registry,
        },
    )

    status = utils.create_from_dict(k8s, service_dict, verbose=True, apply=True)

    # Wait for route to come up, could possibly get the status of the service
    time.sleep(5)

    route = k8s_client.get_knative_route(
        f"{container.language}-{container.tag}", "default"
    )
    url = route["status"]["url"]
    return url


def delete_knative_service(function_id: str):
    k8s = client.CustomObjectsApi()
    status = k8s.delete_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace="default",
        name=function_id,
        plural="services",
    )
    return status
