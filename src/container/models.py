from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.function.models import Function
from src.models import Base, TimestampMixin
from .enums import LanguageTypes


# Pydantic models
class ContainerImageCreate(BaseModel):
    language: LanguageTypes
    body: str


# SQLAlchemy models
class ContainerImage(TimestampMixin, Base):
    tag: Mapped[int] = mapped_column(primary_key=True)
    language: Mapped[LanguageTypes]
    registry: Mapped[str]
    function: Mapped["Function"] = relationship(
        back_populates="container_image", uselist=False
    )
