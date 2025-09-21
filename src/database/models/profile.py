import enum
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.config import Base
from src.database.models.user import UserLevel, User


class MeasurementUnit(str, enum.Enum):
    """
    Measurement units for exercises.
    """

    KILOGRAMS = "кг"
    REPS = "пвт"
    METERS = "м"
    SECONDS = "сек"
    MINUTES = "мин"
    CALORIES = "кал"
    WATTS = "ватт"
    COEFFICIENT = "слр"


class ResultType(str, enum.Enum):
    """
    Result types for exercises.
    """

    STM_TIME = "время удержание"
    ASAP_TIME = "время скорость"
    WEIGHT = "вес"
    REPS = "пвт"
    DISTANCE = "дистанция"
    CAPACITY = "мощность"
    CALORIES = "калории"
    COEFFICIENT = "коэффициент Cинклера"


class ProfileCategory(Base):
    """
    Table for storing exercise categories like Strength, Power, Gymnastics, etc.
    """

    __tablename__ = "profile_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relations
    exercises: Mapped[list["ProfileExercise"]] = relationship(
        argument="ProfileExercise",
        back_populates="category",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProfileCategory(name='{self.name}')>"


class ProfileExercise(Base):
    """
    Database table for storing exercise definitions in users profile.
    Exercises can be from different categories of crossfit training (squat, rows, metcons, etc).
    """

    __tablename__ = "profile_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_name: Mapped[str] = mapped_column(
        ForeignKey("profile_categories.name"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    unit: Mapped[MeasurementUnit] = mapped_column(Enum(MeasurementUnit), nullable=False)
    result_type: Mapped[ResultType] = mapped_column(Enum(ResultType), nullable=False)
    is_time_based: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_basic: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relations
    category: Mapped["ProfileCategory"] = relationship(
        argument="ProfileCategory",
        back_populates="exercises",
    )
    standards: Mapped[list["ExerciseStandard"]] = relationship(
        argument="ExerciseStandard",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
    results: Mapped[list["UserProfileResult"]] = relationship(
        argument="UserProfileResult",
        back_populates="exercise",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Exercise(name='{self.name}')>"


class ExerciseStandard(Base):
    """
    Table for exercise standards based on user level and gender.
    """

    __tablename__ = "exercise_standards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("profile_exercises.id"), nullable=False)
    user_level: Mapped["UserLevel"] = mapped_column(Enum(UserLevel), nullable=False)
    male_min_value: Mapped[float] = mapped_column(
        Float, CheckConstraint("min_value >= 0"), nullable=False
    )
    male_max_value: Mapped[float] = mapped_column(
        Float, CheckConstraint("max_value >= 0"), nullable=False
    )
    female_min_value: Mapped[float] = mapped_column(
        Float, CheckConstraint("min_value >= 0"), nullable=False
    )
    female_max_value: Mapped[float] = mapped_column(
        Float, CheckConstraint("max_value >= 0"), nullable=False
    )

    # Relations
    exercise: Mapped["ProfileExercise"] = relationship(
        argument="ProfileExercise",
        back_populates="standards",
    )

    def __repr__(self) -> str:
        return f"<ExerciseStandard(exercise='{self.exercise.name}', level='{self.user_level}'>"


class UserProfileResult(Base):
    """
    Table for storing user exercise results for profile.
    """

    __tablename__ = "user_profile_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[int] = mapped_column(ForeignKey("profile_exercises.id"), nullable=False)
    result_value: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now())

    # Relations
    user: Mapped[User] = relationship("User", back_populates="profile_results")
    exercise: Mapped["ProfileExercise"] = relationship("ProfileExercise", back_populates="results")
