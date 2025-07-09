import time
from kubernetes import client
from faas.config import config

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

def wait_for_completed(name: str, namespace: str, timeout: int):
    """Waits for 'Succeeded' status from pod"""
    client = get_k8s_core_client()
    resp = client.read_namespaced_pod_status(name, namespace)

    t_start = time.perf_counter()

    while resp.status.phase != "Succeeded":
        t_check = time.perf_counter()
        if t_check - t_start >= timeout:
            return "Build timed out"

        time.sleep(3)
        resp = client.read_namespaced_pod_status(name, namespace)

    t_stop = time.perf_counter()
    duration = round(t_stop - t_start)
    return f"Completed in {duration}"
