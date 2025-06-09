from pydantic import BaseModel
from datetime import datetime
from kubernetes import client, config, utils

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .container import ContainerImage, create_knative_service, delete_knative_service
from .config import settings

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

k8s_api = settings.get_k8s_client()

class FunctionRequest(BaseModel):
    language: str
    body: str


class FunctionResponse(BaseModel):
    id: str
    language: str
    url: str
    created_at: datetime


@app.post("/functions/")
async def create_function(function: FunctionRequest) -> FunctionResponse:
    container = ContainerImage(function.language)
    container.create_build_context(function.body, "faas-platform-build-contexts") 
    container.build(k8s_api)
    url = create_knative_service(k8s_api, container)

    return FunctionResponse(
        id=container.tag,
        language=container.language,
        url=url,
        created_at=datetime.now()
    )


@app.delete("/functions/{function_id}")
async def delete_function(function_id: str):
    delete_knative_service(function_id)
    return