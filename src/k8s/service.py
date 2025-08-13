import time
import logging

from .exceptions import PodTimeoutError
from .dependencies import k8s_custom_objects_client, k8s_core_client

log = logging.getLogger(__name__)


def get_knative_route(name: str, namespace: str):
    """Get the endpoint of an knative service"""
    client = k8s_custom_objects_client()
    return client.get_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace=namespace,
        name=name,
        plural="routes",
    )


def wait_for_succeeded(name: str, namespace: str, timeout: int):
    """Waits for 'Succeeded' status from pod. Raises on timeout with logs"""
    client = k8s_core_client()
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
