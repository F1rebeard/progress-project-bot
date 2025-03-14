from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base


if TYPE_CHECKING:
    from src.database.models import User


class CuratorUser(Base):
    """Junction table for Curator-User relationship."""

    __tablename__ = "curator_user"

    curator_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    curator: Mapped["User"] = relationship(
        "User", backref="managed_users", foreign_keys=[curator_id]
    )
    user: Mapped["User"] = relationship("User", back_populates="curator", foreign_keys=[user_id])
