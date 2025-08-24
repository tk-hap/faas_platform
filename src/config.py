import os
from typing import Literal

from kubernetes import client
from kubernetes import config as k8s_config
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    LOGGING_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_JSON: bool

    # K8s configuration
    IN_CLUSTER: bool = bool(os.getenv("KUBERNETES_SERVICE_HOST"))
    FUNCTION_NAMESPACE: str

    # S3 configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET: str
    S3_ENDPOINT_URL: str
    S3_REGION_NAME: str = "apac"

    # Container configuration
    CONTAINER_REGISTRY: str
    CONTAINER_REGISTRY_API_URL: str
    CONTAINER_REGISTRY_USERNAME: str
    CONTAINER_REGISTRY_PASSWORD: str

    # Function lifespan
    FUNCTION_CLEANUP_SECS: int

    model_config = SettingsConfigDict(env_file=".env")

    def get_k8s_client(self) -> client.ApiClient:
        """Get kubernetes client base on running environment"""
        try:
            if self.IN_CLUSTER:
                k8s_config.load_incluster_config()
            else:
                k8s_config.load_config()
            return client.ApiClient()
        except Exception as e:
            raise RuntimeError(f"Failed to load kubernetes configuration: {e}")


config = Settings()
