import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import User

logger = logging.getLogger(__name__)


class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def get_user_biometrics(
        cls, session: AsyncSession, user_id: int
    ) -> dict[str, Any] | None:
        """
        Fetch user's biometrics data.

        Args:
            session: Database session
            user_id: User's telegram ID

        Returns:
            Tuple of (has_biometrics, biometrics_data)
        """
        biometrics_data = None
        user: User = await cls.find_one_or_none_by_id(session=session, data_id=user_id)

        if user and user.biometrics is not None:
            biometrics_data = {
                "height": user.biometrics.height,
                "weight": user.biometrics.weight,
                "birthday": user.biometrics.birthday,
            }
        logger.debug(f"Biometrics data: {biometrics_data} for user {user_id}")
        return biometrics_data
