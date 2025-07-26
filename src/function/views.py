from datetime import datetime, timezone

from aiohttp import ClientSession as AsyncHttpSession
from fastapi import APIRouter, Depends, HTTPException, status

from src.config import config
from src.container import service as containers_service
from src.container.models import ContainerImageCreate
from src.database import DbSession
from src.dependencies import http_session
from src.k8s import service as k8s_service
from src.scheduler import scheduler

from .enums import FunctionEndpoints
from .models import FunctionCreate, FunctionResponse
from .service import create, delete, fetch_status, get

router = APIRouter()
# TODO: Move to dependency injection
k8s_client = k8s_service.get_k8s_core_client()
k8s_api_client = k8s_service.get_k8s_api_client()


@router.post("", summary="Creates a single function")
async def create_function(
    function_in: FunctionCreate,
    db_session: DbSession,
    http_session: AsyncHttpSession = Depends(http_session),
) -> FunctionResponse:
    container_image_in = ContainerImageCreate(
        language=function_in.language, body=function_in.body
    )
    container = containers_service.create(k8s_api_client, container_image_in)

    function = await create(k8s_api_client, db_session, container)

    # Wait for healthy
    healthy = False
    while not healthy:
        status = await fetch_status(
            http_session, f"{function.url}{FunctionEndpoints.HEALTH}"
        )
        if status == 200:
            healthy = True

    return FunctionResponse(
        id=function.id,
        language=container.language,
        url=function.url,
        created_at=function.created_at,
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
    db_session: DbSession,
    http_session: AsyncHttpSession = Depends(http_session),
) -> bool | None:
    """Checks function health endpoint and returns bool to indicate health"""
    function = await get(db_session, function_id)
    if not function:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    function_status = await fetch_status(
        http_session, f"{function.url}{FunctionEndpoints.HEALTH}"
    )

    if function_status == status.HTTP_200_OK:
        return True
