from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import Base


class StartWorkout(Base):
    """
    Model for START program workouts.
    Each workout is associated with a specific day in the program.
    """

    __tablename__ = "start_workouts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<StartWorkout(day_number={self.day_number})>"
