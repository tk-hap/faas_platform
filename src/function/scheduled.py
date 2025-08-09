import datetime
import aiohttp

from sqlalchemy import select

from src.database import async_session_factory
from src.scheduler import scheduler
from src.config import config

from .models import Function
from .service import delete


@scheduler.scheduled_job(
    "interval", seconds=config.FUNCTION_CLEANUP_SECS, misfire_grace_time=10
)
async def function_delete_expired():
    utc_now = datetime.datetime.now(datetime.timezone.utc)

    async with async_session_factory() as session:
        query = select(Function).where(Function.expire_at <= utc_now)
        result = await session.scalars(query)
        expired_functions = result.all()

        for function in expired_functions:
            async with async_session_factory() as delete_db_session, aiohttp.ClientSession() as delete_http_session:
                await delete(delete_db_session, delete_http_session, function.id)
                print(f"Deleted {function.id}")
