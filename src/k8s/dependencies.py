from kubernetes import client
from typing import Annotated
from src.config import config

from fastapi import Depends


def k8s_custom_objects_client() -> client.CustomObjectsApi:
    """Get the CustomObjectsApi client with proper config"""
    return client.CustomObjectsApi(config.get_k8s_client())


K8sCustomObjectsClient = Annotated[
    client.CustomObjectsApi, Depends(k8s_custom_objects_client)
]


def k8s_core_client() -> client.CoreV1Api:
    """Get the CoreV1Api client with proper config"""
    return client.CoreV1Api(config.get_k8s_client())


K8sCoreClient = Annotated[client.CoreV1Api, Depends(k8s_core_client)]


def k8s_api_client() -> client.ApiClient:
    """Get the ApiClient with the proper config"""
    # TODO: update the client configuration
    return client.ApiClient()


K8sApiClient = Annotated[client.ApiClient, Depends(k8s_api_client)]
