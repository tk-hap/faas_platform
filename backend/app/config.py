import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from kubernetes import client, config

class Settings(BaseSettings):
    # K8s configuration
    in_cluster: bool = bool(os.getenv("KUBERNETES_SERVICE_HOST"))

    # ContainerBuilder configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_endpoint_url: str
    s3_region_name: str = "apac"
    container_registry: str

    # Function lifespan
    function_cleanup_secs: int

    model_config = SettingsConfigDict(env_file=".env")

    def get_k8s_client(self) -> client.ApiClient:
        """Get kubernetes client base on running environment"""
        try:
            if self.in_cluster:
                config.load_incluster_config()
            else:
                config.load_config()
            return client.ApiClient()
        except Exception as e:
            raise RuntimeError(f"Failed to load kubernetes configuration: {e}")


settings = Settings() 