from typing import AsyncIterator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends

from src.config import config

engine = create_async_engine(config.DATABASE_URL)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as error:
            await session.rollback()
            raise


# Annotation to keep depedency injection DRY
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
