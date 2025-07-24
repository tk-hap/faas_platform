from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, timedelta

from src.container import service as containers_service
from src.container.models import ContainerImageCreate
from src.k8s import service as k8s_service
from src.config import config
from src.scheduler import scheduler
from src.database import DbSession

from .models import FunctionCreate, FunctionResponse
from .service import create, delete


router = APIRouter()
k8s_client = k8s_service.get_k8s_core_client()
k8s_api_client = k8s_service.get_k8s_api_client()


@router.post("", summary="Creates a single function")
async def create_function(
    function_in: FunctionCreate,
    db_session: DbSession,
) -> FunctionResponse:
    container_image_in = ContainerImageCreate(
        language=function_in.language, body=function_in.body
    )
    container = containers_service.create(k8s_api_client, container_image_in)

    url = await create(k8s_api_client, db_session, container)

    return FunctionResponse(
        id=container.tag,
        language=container.language,
        url=url,
        created_at=datetime.now(timezone.utc),
    )


@router.delete("/{function_id}", summary="Deletes a single function")
async def delete_function(
    function_id: str,
):
    try:
        delete(function_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete function: {str(e)}"
        )

    return {"message": f"Function {function_id} deleted successfully"}


@router.get("/{function_id}/health", summary="Checks function health endpoint")
async def function_health(
    function_id: str,
):
    pass
