import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Function
from src.scheduler import scheduler
from src.database import get_db_session

db_session = get_db_session()


@scheduler.scheduled_job("interval", args=[db_session], minutes=1)
async def function_delete_expired(db_session: AsyncSession):
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    query = select(Function).where(Function.expire_at >= utc_now)

    async with db_session as session:
        result = session.execute(query)
        print(result.all())
    return
