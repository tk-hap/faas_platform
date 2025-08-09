from urllib.parse import urljoin

import aiohttp

from .exceptions import ContainerRegistryError


class ContainerRegistry:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self._auth = aiohttp.BasicAuth(login=self.username, password=self.password)

    async def delete_image(
        self,
        session: aiohttp.ClientSession,
        project: str,
        repository: str,
        tag: str,
    ) -> bool:
        """Deletes container image by via REST API"""
        path = f"/api/v2.0/projects/{project}/repositories/{repository}/artifacts/{tag}"
        api_endpoint = urljoin(self.url, path)

        async with session.delete(auth=self._auth, url=api_endpoint, ssl=False) as resp:
            if resp.status == 200:
                return True
            elif resp.status == 404:
                # Image already deleted or doesnt exist
                return False
            else:
                error_msg = await resp.text()
                raise ContainerRegistryError(
                    f"Failed to delete image {tag}: HTTP {resp.status} - {error_msg}"
                )
