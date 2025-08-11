import time
import logging
from kubernetes import client

from .exceptions import PodTimeoutError

log = logging.getLogger(__name__)


def get_knative_route(client: client.CustomObjectsApi, name: str, namespace: str):
    """Get the endpoint of an knative service"""
    return client.get_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace=namespace,
        name=name,
        plural="routes",
    )


def wait_for_succeeded(
    client: client.CoreV1Api, name: str, namespace: str, timeout: int
):
    """Waits for 'Succeeded' status from pod. Raises on timeout with logs"""

    # Could early exit on Error status
    t_start = time.perf_counter()

    while True:
        resp = client.read_namespaced_pod_status(name, namespace)
        phase = resp.status.phase or ""

        if phase == "Succeeded":
            elapsed = round(time.perf_counter() - t_start)
            log.info(f"Succeeded in {elapsed}")
            return

        if time.perf_counter() - t_start >= timeout:
            logs = client.read_namespaced_pod_log(name, namespace)

            raise PodTimeoutError(
                f"Pod {name} did not succeed in {timeout}s.\n" f"Logs:\n {logs}"
            )

        time.sleep(3)
