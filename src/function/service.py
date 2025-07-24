import time
from datetime import datetime, timezone, timedelta
import yaml
import os
from typing import Any
from kubernetes import utils
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import ClientSession as aiohttp_ClientSession

from src.container.models import ContainerImage
from src.k8s.service import get_knative_route, get_k8s_custom_objects_client
from src.config import config

from .models import Function


def build_kn_service_manifest(container_image: ContainerImage) -> dict:
    """Constructs knative service manifest"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    service_path = os.path.join(base_dir, "templates", "service.yaml")

    with open(service_path) as f:
        manifest = yaml.safe_load(f)

    manifest["metadata"]["name"] = container_image.tag
    manifest["spec"]["template"]["spec"]["containers"][0]["image"] = (
        f"{container_image.registry}:{container_image.tag}"
    )

    return manifest


async def create(
    k8s_api_client: Any, db_session: AsyncSession, container_image: ContainerImage
) -> str:
    """Creates the knative service"""

    service = build_kn_service_manifest(container_image)

    status = utils.create_from_dict(k8s_api_client, service, verbose=True, apply=True)

    # TODO: Wait for route to come up
    time.sleep(5)

    route = get_knative_route(f"{container_image.tag}", "default")
    url = route["status"]["url"]

    expire_at = datetime.now(timezone.utc) + timedelta(
        seconds=config.FUNCTION_CLEANUP_SECS
    )
    function = Function(url=url, expire_at=expire_at)

    db_session.add(function)
    await db_session.commit()

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


async def check_up(session: aiohttp_ClientSession, url: str) -> int:
    """Checks if function healthcheck is returning OK"""
    async with session.get(url) as response:
        return await response.status
