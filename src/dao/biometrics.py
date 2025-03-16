from src.dao import BaseDAO
from src.database.models import Biometric


class BiometricDAO(BaseDAO):
    model = Biometric
