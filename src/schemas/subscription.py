from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.database.models.subscription import SubscriptionStatus, SubscriptionType


class SubscriptionCreateSchema(BaseModel):
    user_id: int
    subscription_type: SubscriptionType
    status: SubscriptionStatus
    registered_date: date = Field(default_factory=date.today)
    end_date: date


class SubscriptionReadSchema(BaseModel):
    subscription_type: SubscriptionType
    status: SubscriptionStatus
    registered_date: date
    end_date: date

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
