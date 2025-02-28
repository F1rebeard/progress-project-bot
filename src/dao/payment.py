from src.dao import BaseDAO
from src.database.models import Payment


class PaymentDAO(BaseDAO):
    model = Payment
