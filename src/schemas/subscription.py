from datetime import date

from pydantic import BaseModel, Field

from src.database.models.subscription import SubscriptionStatus, SubscriptionType


class SubscriptionCreateSchema(BaseModel):
    user_id: int
    subscription_type: SubscriptionType
    status: SubscriptionStatus
    registered_date: date = Field(default_factory=date.today)
    end_date: date
