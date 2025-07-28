from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models import Base, TimestampMixin
from .enums import LanguageTypes


# Pydantic models
class ContainerImageCreate(BaseModel):
    language: LanguageTypes
    body: str


# SQLAlchemy models
class ContainerImage(TimestampMixin, Base):
    tag: Mapped[str] = mapped_column(primary_key=True)
    language: Mapped[LanguageTypes]
    registry: Mapped[str]
    function: Mapped["Function"] = relationship(  # noqa: F821
        "Function", back_populates="container_image", uselist=False
    )
