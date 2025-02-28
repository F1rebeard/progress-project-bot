from datetime import datetime

from pydantic import BaseModel, Field

from src.database.models.payment import PaymentStatus
from src.database.models.subscription import SubscriptionType


class PaymentCreateSchema(BaseModel):
    sub_id: int  # User ID associated with the subscription
    sub_type: SubscriptionType  # The type of subscription
    amount: int  # Payment amount
    status: PaymentStatus
    payment_date: datetime = Field(default_factory=datetime.utcnow)  # Set to current date and time

    def __str__(self):
        return (
            f"🆔 Пользователь - {self.sub_id}, Тип подписки - {self.sub_type.value}, "
            f"Сумма - {self.amount}₽, Статус - {self.status.value}, "
            f"Дата - {self.payment_date.strftime('%d.%m.5Y %H:%M:%S')}"
        )
