import os
import tarfile
from io import BytesIO
from typing import Any
from uuid import uuid4

import boto3
import yaml
from aiohttp import ClientSession as AsyncHttpSession
from botocore.exceptions import ClientError
from kubernetes import utils
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import config
from src.k8s import service as k8s_service

from .enums import HandlerFiles
from .models import ContainerImage, ContainerImageCreate
from .registry.service import delete_container_image

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=config.s3_endpoint_url,
    aws_access_key_id=config.aws_access_key_id,
    aws_secret_access_key=config.aws_secret_access_key,
    region_name=config.s3_region_name,
)

k8s_client = k8s_service.get_k8s_core_client()


def create_build_context(
    s3_client: Any, container_image_in: ContainerImageCreate, tag: str, bucket: str
) -> str:
    """Creates and uploads a build context to S3 compatible storage"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    tar_file = f"{tag}.tar.gz"
    template_dir = os.path.join(
        base_dir, "templates", "contexts", container_image_in.language
    )
    handler_file = HandlerFiles[container_image_in.language]

    with tarfile.open(tar_file, "w:gz") as tar:
        # Write handler
        data = container_image_in.body.encode("utf-8")
        file = BytesIO(data)
        info = tarfile.TarInfo(f"src/{handler_file}")
        info.size = len(data)
        tar.addfile(info, file)

        files = os.listdir(template_dir)
        for file in files:
            file_path = os.path.join(template_dir, file)
            tar.add(file_path, arcname=file)

    try:
        s3_client.upload_file(tar_file, bucket, tar_file)
    except ClientError as e:
        raise RuntimeError(f"Error uploading {tar_file}: {str(e)}")
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


async def create(
    k8s_api_client: Any,
    db_session: AsyncSession,
    container_image_in: ContainerImageCreate,
) -> ContainerImage:
    """Creates a new container image."""

    language = container_image_in.language.value
    tag = f"{language}-{str(uuid4())}"

    build_context = create_build_context(
        s3_client=s3_client,
        container_image_in=container_image_in,
        tag=tag,
        bucket=config.s3_bucket,
    )

    container = ContainerImage(
        tag=tag,
        language=language,
        registry=config.CONTAINER_REGISTRY,
    )

    builder = build_kaniko_pod_manifest(container, build_context)
    utils.create_from_dict(k8s_api_client, builder, verbose=True)
    k8s_service.wait_for_succeeded(f"{tag}", "kaniko", 120)

    db_session.add(container)
    await db_session.commit()

    return container


async def delete(
    db_session: AsyncSession, http_session: AsyncHttpSession, container_image_id: str
):
    # Should maybe cascade off function deletion
    container = await db_session.get(ContainerImage, container_image_id)

    await delete_container_image(http_session, "library", "functions", container.tag)

    await db_session.delete(container)
    await db_session.commit()

    return
