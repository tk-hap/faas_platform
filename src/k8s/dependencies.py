from kubernetes import client
from src.config import config


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
