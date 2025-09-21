from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import GlobalSettingDAO, UserSettingDAO
from src.database.models import UserSetting


class TestWeekAccessService:
    """
    A logic with access to test week for users.
    """

    def __init__(
            self,
            global_settings_dao: Type[GlobalSettingDAO],
            user_settings_dao: Type[UserSettingDAO],
    ):
        self._global_dao = global_settings_dao
        self._user_settings_dao = user_settings_dao

    async def can_user_access_week(self, user_id: int, session: AsyncSession) -> bool:
        """
        Decide whether the user can view test weeks.

        The logic is:
          1. If global test-week is ON:
               → any user with an ACTIVE subscription may access.
          2. If global test-week is OFF:
               → only users with BOTH an ACTIVE subscription

        """

        if await self._global_dao.is_test_week_enabled(session):
            return True

        user_settings: UserSetting = await self._user_settings_dao.get_for_user(user_id=user_id,
                                                                    session=session)
        return bool(user_settings.test_week_override)


@asynccontextmanager
async def test_weeks_access(session:AsyncSession) -> AsyncGenerator[
    TestWeekAccessService, Any]:
    yield TestWeekAccessService(
        user_settings_dao=UserSettingDAO,
        global_settings_dao=GlobalSettingDAO
    )