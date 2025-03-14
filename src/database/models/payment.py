from datetime import datetime
import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.subscription import SubscriptionType


if TYPE_CHECKING:
    from src.database.models import Subscription


class PaymentStatus(str, enum.Enum):
    PENDING = "Обработка"
    COMPLETED = "Выполнен"
    FAILED = "Ошибка"


class Payment(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sub_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.user_id", ondelete="NULL"), nullable=False
    )
    sub_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType, create_type=False), nullable=False
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    # Relationsip
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="payments",
    )
