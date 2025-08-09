from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
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
    id: Mapped[str] = mapped_column(ForeignKey("container_image.tag"), primary_key=True)
    url: Mapped[str]
    expire_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

    container_image: Mapped["ContainerImage"] = relationship(  # noqa: F821
        "ContainerImage",
        back_populates="function",
        uselist=False,
        lazy="selectin",
    )
