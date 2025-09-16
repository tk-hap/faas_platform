import os
import tarfile
from io import BytesIO
from typing import Any
from uuid import uuid4

import boto3
import yaml
import logging
from aiohttp import ClientSession as AsyncHttpSession
from botocore.exceptions import ClientError
from kubernetes import utils
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import config
from src.k8s import service as k8s_service

from .enums import HandlerFiles
from .models import ContainerImage, ContainerImageCreate
from .registry.service import delete_container_image

log = logging.getLogger(__name__)

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=config.S3_ENDPOINT_URL,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    region_name=config.S3_REGION_NAME,
)


def create_build_context(
    s3_client: Any, container_image_in: ContainerImageCreate, tag: str, bucket: str
) -> str:
    """Create & upload build context in memory."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(
        base_dir, "templates", "contexts", container_image_in.language
    )
    handler_file = HandlerFiles[container_image_in.language]
    tar_key = f"{tag}.tar.gz"

    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # Add user handler body
        data = container_image_in.body.encode("utf-8")
        h_info = tarfile.TarInfo(f"src/{handler_file}")
        h_info.size = len(data)
        tar.addfile(h_info, BytesIO(data))

        # Add template files; avoid duplicating handler file if present
        for entry in os.listdir(template_dir):
            entry_path = os.path.join(template_dir, entry)
            if entry == handler_file:
                continue
            if os.path.isdir(entry_path):
                for root, _, files in os.walk(entry_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, template_dir)
                        tar.add(fp, arcname=arcname)
            else:
                tar.add(entry_path, arcname=entry)

    buf.seek(0)
    try:
        s3_client.upload_fileobj(buf, bucket, tar_key)
    except ClientError as e:
        log.exception("Upload failed for %s: %s", tar_key, e)
        raise RuntimeError(f"Error uploading {tar_key}: {e}")
    finally:
        buf.close()

    return f"s3://{bucket}/{tar_key}"


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
        bucket=config.S3_BUCKET,
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
    container = await db_session.get(ContainerImage, container_image_id)

    await delete_container_image(http_session, "library", "functions", container.tag)

    await db_session.delete(container)
    await db_session.commit()

    return
