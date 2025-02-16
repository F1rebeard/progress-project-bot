from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from src.database.models import Base, User


class UserResults(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.telegram_id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    movement: Mapped[str] = mapped_column(String(100), nullable=False)

    @classmethod
    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship("User", back_populates=f"{cls.__tablename__.lower()}_results")


class Strength(UserResults):
    __tablename__ = "strength"

    weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)


class StrengthCapacity(UserResults):
    __tablename__ = "strength_capacity"

    weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    sinkler: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)


class ExplosivePower(UserResults, Base):
    __tablename__ = "explosive_power"

    weight: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)


class Gymnastic(UserResults):
    __tablename__ = "gymnastic"

    result: Mapped[int] = mapped_column(Integer, nullable=False)


class AerobicCapacity(UserResults):
    __tablename__ = "aerobic_capacity"

    result: Mapped[int] = mapped_column(Integer, nullable=False)


class Metcon(UserResults):
    __tablename__ = "metcon"

    result: Mapped[int] = mapped_column(Integer, nullable=False)
