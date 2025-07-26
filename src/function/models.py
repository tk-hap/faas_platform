from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP
from src.models import Base, TimestampMixin


# Pydantic Models
class FunctionCreate(BaseModel):
    language: str
    body: str


class FunctionResponse(BaseModel):
    id: str
    language: str
    url: str
    created_at: datetime


# SQLAlchemy Models
class Function(TimestampMixin, Base):
    id: Mapped[str] = mapped_column(primary_key=True)
    url: Mapped[str]
    expire_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
