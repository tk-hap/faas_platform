import time
import kubernetes


def get_knative_route(name: str, namespace: str):
    client = kubernetes.client.CustomObjectsApi()
    return client.get_namespaced_custom_object(
        group="serving.knative.dev",
        version="v1",
        namespace=namespace,
        name=name,
        plural="routes",
    )


def wait_for_completed(name: str, namespace: str, timeout: int):
    client = kubernetes.client.CoreV1Api()
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
    return f"Build completed in {duration}"
