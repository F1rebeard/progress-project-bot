from src.bot.keyboards.utils import create_inline_keyboard


def subscription_selection_btn():
    """Button to start the subscription selection dialog for new user."""
    return create_inline_keyboard([("📋 Выбрать подписку", "new_subscription")])


def renew_or_change_subscription_kb():
    """Inline keyboard to renew or change the subscription."""
    return create_inline_keyboard(
        [
            ("🔄 Обновить подписку", "renew_subscription"),
            ("📋 Изменить подписку", "change_subscription"),
        ]
    )
