from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BiometricDAO, UserDAO
from src.schemas import BiometricUpdateSchema
from src.database.models.user import UserLevel, Gender
from src.schemas.user import UserUpdateSchema


class RegistrationService:
     def __init__(self, session: AsyncSession):
         self.session = session

     async def update_user_profile(
             self,
             telegram_id: int,
             username: str | None,
             first_name: str,
             last_name: str,
             email: str,
             gender: Gender,
             level: UserLevel,
             birthday: date,
             height: int,
             weight: float,
     ):
         """

         """
         user_update_data = UserUpdateSchema(
             username=username,
             first_name=first_name,
             last_name=last_name,
             email=email,
             gender=gender,
             level=level,
         )
         biometrics_update_schema = BiometricUpdateSchema(
             birthday=birthday,
             height=height,
             weight=weight,
         )
         await UserDAO.update_one_by_id(
             session=self.session,
             data_id=telegram_id,
             data=user_update_data
         )
         await BiometricDAO.update_one_by_id(
             session=self.session,
             data_id=telegram_id,
             data=biometrics_update_schema,
         )