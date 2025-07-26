from typing import AsyncIterator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends

from src.config import config


async def get_db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(config.DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as error:
            await session.rollback()
            raise


# Annotation to keep depedency injection DRY
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
