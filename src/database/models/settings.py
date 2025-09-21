from sqlalchemy import ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models import Base
from src.database.models.user import User
from src.utils.emojis import CalendarEmoji


class GlobalSetting(Base):
    """
    Global settings for bot and users controlled by admins.
    """

    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_week_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UserSetting(Base):
    """
    Per-user settings: calendar empojis, individual test-week override, etc.
    """

    __tablename__ = "settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), primary_key=True)

    # Test week override for user
    test_week_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Calendar emojis for visualization
    calendar_emoji: Mapped[CalendarEmoji] = mapped_column(
        Enum(CalendarEmoji, name="calendar_emoji"),
        default=CalendarEmoji.CALENDAR,
        nullable=False,
    )
    workout_date_emoji: Mapped[CalendarEmoji] = mapped_column(
        Enum(CalendarEmoji, name="calendar_emoji"),
        default=CalendarEmoji.ATHLETE,
        nullable=False,
    )
    today_with_workout_emoji: Mapped[CalendarEmoji] = mapped_column(
        Enum(CalendarEmoji, name="today_with_workout_emoji"),
        default=CalendarEmoji.RED_CIRCLE,
        nullable=False,
    )
    today_without_workout_emoji: Mapped[CalendarEmoji] = mapped_column(
        Enum(CalendarEmoji, name="today_without_workout_emoji"),
        default=CalendarEmoji.DAY_OFF,
        nullable=False,
    )

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="setting")
