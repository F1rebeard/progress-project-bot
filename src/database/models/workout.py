from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.user import UserLevel

if TYPE_CHECKING:
    from src.database.models import User


class Workout(Base):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), nullable=False)

    # Relationships
    workout_results: Mapped[list["WorkoutResult"]] = relationship(
        "WorkoutResult",
        back_populates="workout",
        cascade="all, delete-orphan",
    )

class WorkoutResult(Base):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id", ondelete="CASCADE"),
                                            nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    workout: Mapped["Workout"] = relationship(
        "Workout",
        back_populates="workout_results",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workout_results",
    )
