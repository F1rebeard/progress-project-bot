from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import UserSetting, GlobalSetting
from src.utils.emojis import CalendarEmoji

EmojiField = Literal[
    "calendar_emoji",
    "workout_date_emoji",
    "today_with_workout_emoji",
    "today_without_workout_emoji",
]


class GlobalSettingDAO(BaseDAO[GlobalSetting]):

    model = GlobalSetting

    @classmethod
    async def get_settings(cls, session: AsyncSession):
        """
        This method is used to retrieve or create the settings for a specific model in the database.
        It queries the database for an existing settings record, and if none is found, it creates and adds
        a new one. The method ensures there is always a settings object available in the database.

        Args:
            session (AsyncSession): An asynchronous SQLAlchemy session used for executing database
            queries and transactions.

        Returns:
            cls.model: The settings object retrieved from the database or a newly created one.
        """
        statement = select(cls.model)
        result = await session.execute(statement)
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = cls.model()
            session.add(settings)
            await session.flush()
        return settings

    @classmethod
    async def is_test_week_enabled(cls, session: AsyncSession):
        """
        Check whether the test week is globally enabled for all users.
        """
        settings: GlobalSetting = await cls.get_settings(session)
        return settings.test_week_enabled

    @classmethod
    async def set_test_week_status(cls, status: bool, session: AsyncSession):
        """
        Globally enable/disable test week for all users.
        """
        settings: GlobalSetting = await cls.get_settings(session)
        settings.test_week_enabled = status
        await session.flush()


class UserSettingDAO(BaseDAO[UserSetting]):

    model = UserSetting

    @classmethod
    async def get_for_user(
        cls,
        user_id: int,
        session: AsyncSession,
    ) -> UserSetting:
        """
        This method retrieves or creates a `Setting` instance for a given user.

        It first attempts to fetch an existing `Setting` instance from the database
        associated with the given `user_id`. If no such instance is found, it creates a
        new `Setting` object, associates it with the specified `user_id`, adds it to
        the session, and flushes the changes to prepare it for persistence.

        Parameters:
            user_id (int): The unique identifier of the user for whom the `Setting`
                instance is retrieved or created.
            session (AsyncSession): The asynchronous database session used for querying
                and persisting data.

        Returns:
            UserSetting: The existing or newly created `Setting` instance associated with
                the given `user_id`.

        Raises:
            None
        """
        setting: UserSetting = await cls.find_one_or_none_by_id(
            data_id=user_id,
            session=session
        )
        if setting is None:
            setting = UserSetting(user_id=user_id)
            session.add(setting)
            await session.flush()
        return setting

    @classmethod
    async def set_emoji(
            cls,
            user_id: int,
            field: str,
            emoji: str,
            session: AsyncSession,
    ):
        """
        Updates an emoji setting for a specific user and field in the database. This is an
        asynchronous class method that performs validation of the emoji provided and sets
        the corresponding field of the user's settings to the given emoji.

        Parameters:
            user_id (int): The unique identifier of the user whose setting is to be updated.
            field (str): The field in the user's settings that needs to be updated with the new emoji.
            emoji (str): The emoji to set for the given field. Must be a valid emoji from
                CalendarEmoji.list().
            session (AsyncSession): The database session used to perform the operation.

        Raises:
            ValueError: Raised if the provided emoji is not in the supported list of emojis.
        """
        if emoji not in CalendarEmoji.list():
            raise ValueError(f"Unsupported emoji {emoji!r}")

        setting = await cls.get_for_user(user_id, session)
        setattr(setting, field, CalendarEmoji(emoji))

    @classmethod
    async def set_user_test_week_override(
            cls,
            user_id: int,
            enabled: bool,
            session: AsyncSession,
    ):
        """
        Sets the test week override for a specific user.

        Args:
            user_id (int): The ID of the user whose test week override is being updated.
            enabled (bool): A boolean indicating whether the test week override is enabled or
                disabled.
            session (AsyncSession): The database session used to retrieve and update the user's
                settings.

        Returns:
            None
        """
        setting = await cls.get_for_user(user_id, session)
        setting.test_week_override = enabled

