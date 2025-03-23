import logging
from datetime import date

from aiogram import Router
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import UserDAO
from src.database.models.subscription import SubscriptionType
from src.utils.start_workouts import calculate_next_monday, calculate_start_program_day

logger = logging.getLogger(__name__)

start_program_router = Router()


async def set_start_program_date_for_new_subscription(
    telegram_id: int, subscription_type: SubscriptionType, session: AsyncSession
) -> date | None:
    """
    Set the start_program_begin_date for a new START program subscription.

    Args:
        telegram_id: The user's Telegram ID
        subscription_type: The subscription type
        session: The database session

    Returns:
        date | None: The start date (next Monday) if set, None otherwise
    """
    is_start_program = subscription_type in [
        SubscriptionType.START_PROGRAM,
        SubscriptionType.ONE_MONTH_START,
    ]
    if not is_start_program:
        return None
    user = await UserDAO.find_one_or_none_by_id(data_id=telegram_id, session=session)
    if not user or not user.subscription:
        logger.error(f"User {telegram_id} or subscription not found")
        return None
    next_monday = calculate_next_monday()
    user.subscription.start_program_begin_date = next_monday
    await session.flush()
    logger.info(
        f"START program begin date set to {next_monday} for user {telegram_id}, "
        f"subscription type: {subscription_type}"
    )
    return next_monday


async def get_start_program_day(
    telegram_id: int, selected_date: date, session: AsyncSession
) -> int | None:
    """
    Calculate which day of the START program a selected date corresponds to.

    Args:
        telegram_id: The user's Telegram ID
        selected_date: The date to check
        session: The database session

    Returns:
        int | None: The day number in the START program, or None if not applicable
    """
    user = await UserDAO.find_one_or_none_by_id(data_id=telegram_id, session=session)
    if not user or not user.subscription:
        return None

    is_start_program = user.subscription.subscription_type in [
        SubscriptionType.START_PROGRAM,
        SubscriptionType.ONE_MONTH_START,
    ]
    if not is_start_program or not user.subscription.start_program_begin_date:
        return None
    return calculate_start_program_day(user.subscription.start_program_begin_date, selected_date)
