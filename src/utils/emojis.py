from enum import Enum


class CalendarEmoji(str, Enum):
    """
    General emojis for calendar UI (used in headers, buttons, etc.)
    """
    CALENDAR = "📅"
    CHECK = "✅"
    ATHLETE = "🏋️"
    FIRE = "🔥"
    FLEX = "💪"
    HEART = "❤️"
    RED_CIRCLE = "🔴"
    GREEN_CIRCLE = "🟢"
    BLUE_DIAMOND = "🔹"
    DAY_OFF = "🏖"

    @classmethod
    def list(cls) -> list[str]:
        """
        All calendar emojis in a list.
        """
        return [emoji.value for emoji in cls]

