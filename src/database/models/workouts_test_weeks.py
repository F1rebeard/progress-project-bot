from sqlalchemy import BigInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database.models import Base

class TestWorkouts(Base):
    """
    Represents the TestWorkouts model for handling information about workout days.

    This class is designed for use within a database context, mapping workout days
    and their corresponding details. It includes essential attributes like the
    unique ID, day number, and description of the workout.

    Attributes:
        id: The unique identifier for the test workout (Primary Key).
        day_number: The unique number of the day associated with the workout.
        description: The textual description of the workout for the given day.

    """

    __tablename__ = 'test_workouts'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<TestWorkout(day_number={self.day_number})>"
