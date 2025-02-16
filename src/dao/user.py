from src.database.dao import BaseDAO
from src.database.models import User


class UserDAO(BaseDAO[User]):
    model = User
