from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from kubernetes import client, config, utils

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from .container import ContainerImage, create_knative_service, delete_knative_service
from .config import settings

scheduler = AsyncIOScheduler(timezone=timezone.utc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load APScheduler
    scheduler.start()
    yield
    # Cleanup APScheduler
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

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

    try:
        url = create_knative_service(k8s_api, container)
    except Exception:
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    # Schedule function cleanup
    cleanup_time = datetime.now(timezone.utc) + timedelta(seconds=settings.function_cleanup_secs)
    print(cleanup_time)
    scheduler.add_job(
        delete_knative_service,
        "date",
        run_date=cleanup_time,
        args=[f"{container.language}-{container.tag}"],
        misfire_grace_time=None,
    )

    return FunctionResponse(
        id=container.tag,
        language=container.language,
        url=url,
        created_at=datetime.now(timezone.utc),
    )


@app.delete("/functions/{function_id}")
async def delete_function(function_id: str):
    try:
        delete_knative_service(function_id)
    except Exception:
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    return status.HTTP_200_OK
