import time
from kubernetes import client
from faas.config import config

from .exceptions import PodTimeoutError


def get_k8s_custom_objects_client() -> client.CustomObjectsApi:
    """Get the CustomObjectsApi client with proper config"""
    return client.CustomObjectsApi(config.get_k8s_client())


def get_k8s_core_client() -> client.CoreV1Api:
    """Get the CoreV1Api client with proper config"""
    return client.CoreV1Api(config.get_k8s_client())


def get_k8s_api_client() -> client.ApiClient:
    """Get the ApiClient with the proper config"""
    # TODO: update the client configuration
    return client.ApiClient()


def get_knative_route(name: str, namespace: str):
    """Get the endpoint of an knative service"""
    client = get_k8s_custom_objects_client()
    return client.get_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace=namespace,
        name=name,
        plural="routes",
    )


def wait_for_succeeded(name: str, namespace: str, timeout: int):
    """Waits for 'Succeeded' status from pod. Raises on timeout with logs"""

    # Could early exit on Error status
    client = get_k8s_core_client()
    t_start = time.perf_counter()

    while True:
        resp = client.read_namespaced_pod_status(name, namespace)
        phase = resp.status.phase or ""

        if phase == "Succeeded":
            elapsed = round(time.perf_counter() - t_start)
            print(f"Succeeded in {elapsed}")
            return

        if time.perf_counter() - t_start >= timeout:
            logs = client.read_namespaced_pod_log(name, namespace)

            raise PodTimeoutError(
                f"Pod {name} did not succeed in {timeout}s.\n" f"Logs:\n {logs}"
            )

        time.sleep(3)
