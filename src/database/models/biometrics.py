from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base

if TYPE_CHECKING:
    from src.database.models import User


class Biometric(Base):
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id"),
        primary_key=True,
        unique=True
    )
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    birthday: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="biometrics",
        uselist=False,
    )
