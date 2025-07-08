from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone, timedelta

from faas.container import service as containers_service
from faas.container.models import ContainerImageCreate
from faas.k8s import service as k8s_service
from faas.config import config
from faas.scheduler import scheduler

from .models import FunctionCreate, FunctionResponse
from .service import create, delete


router = APIRouter()
k8s_client = k8s_service.get_k8s_core_client()
k8s_api_client = k8s_service.get_k8s_api_client()


@router.post("")
def create_function(function_in: FunctionCreate) -> FunctionResponse:
    container_image_in = ContainerImageCreate(
        language=function_in.language, body=function_in.body
    )
    container = containers_service.create(k8s_api_client, container_image_in)

    try:
        url = create(k8s_api_client, container)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create function: {str(e)}",
        )

    # Schedule function cleanup
    cleanup_time = datetime.now(timezone.utc) + timedelta(
        seconds=config.function_cleanup_secs
    )
    scheduler.add_job(
        delete,
        "date",
        run_date=cleanup_time,
        args=[f"{container.tag}"],
        misfire_grace_time=None,
    )

    return FunctionResponse(
        id=container.tag,
        language=container.language,
        url=url,
        created_at=datetime.now(timezone.utc),
    )


@router.delete("/{function_id}")
async def delete_function(function_id: str, ):
    try:
        delete(function_id)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete function: {str(e)}"
        )

    return {"message": f"Function {function_id} deleted successfully"}
