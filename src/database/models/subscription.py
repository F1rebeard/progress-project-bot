import enum

from sqlalchemy import Date, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base, Payment, User


class SubscriptionType(str, enum.Enum):
    STANDARD = "Базовая"
    WITH_CURATOR = "С куратором" # noqa: RUF001
    START_PROGRAM = "Полный Старт"
    ONE_MONTH_START = "Месяц Старт"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "Активна"
    FROZEN = "Заморожена"
    EXPIRED = "Истекла"


class Subscription(Base):
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
        nullable=False,
    )
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), nullable=False)
    registered_date: Mapped[Date] = mapped_column(Date, server_default=func.now(), nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscription",
        uselist=False,
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="subscription",
        cascade="all, delete, delete-orphan",
    )
