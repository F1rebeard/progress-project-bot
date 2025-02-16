import enum

from sqlalchemy import BigInteger, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base, Biometric, CuratorUser, Subscription, WorkoutResult


class UserLevel(str, enum.Enum):
    FIRST = "Первый"
    SECOND = "Второй"
    MINKAIFA = "Минкайфа"
    COMPETITION = "Соревнования"
    START = "Старт"


class UserRole(str, enum.Enum):
    ADMIN = "Админ"
    CURATOR = "Куратор"
    USER = "Пользователь"


class Gender(str, enum.Enum):
    MALE = "Мужчина"
    FEMALE = "Женщина"


class User(Base):

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    username: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    e_mail: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=True)
    level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)

    # Relationships

    # one-to-one
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        lazy="joined",
    )
    # one-to-one
    biometrics: Mapped["Biometric"] = relationship(
        "Biometric",
        back_populates="user",
        uselist=False,
        lazy="joined",
    )
    # one-to-many
    workout_results: Mapped[list["WorkoutResult"]] = relationship(
        "WorkoutResult",
        back_populates="users",
        cascade="all, delete, delete-orphan",
    )
    curator: Mapped["CuratorUser | None"] = relationship(
        "CuratorUser",
        back_populates="user",
        foreign_keys="[CuratorUser.user_id]",
        uselist=False,
    )
