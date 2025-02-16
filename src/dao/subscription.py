from src.database.dao import BaseDAO
from src.database.models import Subscription


class SubscriptionDAO(BaseDAO):
    model = Subscription
