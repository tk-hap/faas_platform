import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import yaml
from kubernetes import utils
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import config
from src.container.models import ContainerImage
from src.k8s.service import (
    get_k8s_custom_objects_client,
    get_knative_route,
)

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
) -> Function:
    """Creates the knative service"""
    service = build_kn_service_manifest(container_image)

    status = utils.create_from_dict(k8s_api_client, service, verbose=True, apply=True)

    # Wait for route to come up
    time.sleep(1)
    route = get_knative_route(container_image.tag, "default")
    url = route["status"]["url"]

    expire_at = datetime.now(timezone.utc) + timedelta(
        seconds=config.FUNCTION_CLEANUP_SECS
    )
    function = Function(id=container_image.tag, url=url, expire_at=expire_at)

    db_session.add(function)
    await db_session.commit()

    return function


async def get(db_session: AsyncSession, function_id: str) -> Function | None:
    """Returns a function based on the given id."""
    return await db_session.get(Function, function_id)


async def delete(db_session: AsyncSession, function_id: str):
    """Deletes existing function"""
    k8s_client = get_k8s_custom_objects_client()
    function = await db_session.get(Function, function_id)

    status = k8s_client.delete_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace="default",
        name=function.id,
        plural="services",
    )

    await db_session.delete(function)
    await db_session.commit()


async def fetch_status(session: aiohttp.ClientSession, url: str) -> int:
    """Returns HTTP status of endpoint"""
    async with session.get(url) as response:
        return response.status
