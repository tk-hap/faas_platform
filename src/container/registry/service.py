from aiohttp import ClientSession as AsyncHttpSession

from src.config import config

from .registry import ContainerRegistry

registry_client = ContainerRegistry(
    username=config.CONTAINER_REGISTRY_USERNAME,
    password=config.CONTAINER_REGISTRY_PASSWORD,
    url=config.CONTAINER_REGISTRY_API_URL,
)


async def delete_container_image(
    http_session: AsyncHttpSession, project: str, repository: str, tag: str
) -> bool:
    """Delete container image from registry"""
    return await registry_client.delete_image(http_session, project, repository, tag)
