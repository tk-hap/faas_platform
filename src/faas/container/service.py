import yaml
import os
import tarfile
import boto3
from io import BytesIO
from uuid import uuid4
from botocore.exceptions import ClientError
from kubernetes import utils
from typing import Any

from faas.config import config
from faas.k8s import service as k8s_service

from .models import ContainerImage, ContainerImageCreate

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=config.s3_endpoint_url,
    aws_access_key_id=config.aws_access_key_id,
    aws_secret_access_key=config.aws_secret_access_key,
    region_name=config.s3_region_name,
)

k8s_client = k8s_service.get_k8s_core_client()


def create_build_context(s3_client: Any, tag: str, body: str, bucket: str) -> str:
    """Creates and uploads a build context to S3 compatible storage"""

    tar_file = f"{tag}.tar.gz"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates", "contexts", "python")

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
        s3_client.upload_file(tar_file, bucket, tar_file)
    except ClientError as e:
        raise f"Error uploading {tar_file}: {str(e)}"
    finally:
        if os.path.exists(tar_file):
            os.remove(tar_file)

    return f"s3://{bucket}/{tar_file}"


def build_kaniko_pod_manifest(
    container_image: ContainerImage, build_context: str
) -> dict:
    """Constructs the builder pod manifest."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    builder_path = os.path.join(base_dir, "templates", "builder.yaml")

    with open(builder_path) as f:
        manifest = yaml.safe_load(f)

    manifest["metadata"]["name"] = container_image.tag

    build_args = manifest["spec"]["containers"][0]["args"]
    build_args[1] = f"--context={build_context}"
    build_args[2] = f"--destination={container_image.registry}:{container_image.tag}"

    return manifest


def create(
    k8s_api_client: Any, container_image_in: ContainerImageCreate
) -> ContainerImage:
    """Creates a new container image."""

    tag = f"{container_image_in.language}-{str(uuid4())}"

    build_context = create_build_context(
        s3_client, tag, container_image_in.body, config.s3_bucket
    )

    image = ContainerImage(
        language=container_image_in.language,
        tag=tag,
        registry=config.container_registry,
    )

    builder = build_kaniko_pod_manifest(image, build_context)
    utils.create_from_dict(k8s_api_client, builder, verbose=True)
    k8s_service.wait_for_completed(f"{tag}", "kaniko", 35)

    return image
