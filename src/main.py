from pydantic import BaseModel
from datetime import datetime
from kubernetes import client, config, utils

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .container import ContainerImage, create_knative_service

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#TODO: Auth from within cluster https://github.com/kubernetes-client/python/blob/master/examples/in_cluster_config.py
config.load_config()
k8s_api = client.ApiClient()


class Function(BaseModel):
    """Represents a serverless function"""
    id: str
    language: str
    created_at: datetime 
    url: str


@app.post("/functions/{language}")
async def create_function(language: str) -> Function:
    container = ContainerImage(language)
    container.Build(f"function_templates/{language}/", k8s_api)
    url = create_knative_service(k8s_api, container)

    return Function(
        id=container.tag,
        language=container.language,
        url=url,
        created_at= datetime.now()
    )