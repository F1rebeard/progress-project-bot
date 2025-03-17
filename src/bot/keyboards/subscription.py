from src.bot.keyboards.utils import create_inline_keyboard

subscription_selection_btn = create_inline_keyboard([("📋 Выбрать подписку", "new_subscription")])
renew_or_change_subscription_kb = create_inline_keyboard(
    [
        ("🔄 Обновить подписку", "renew_subscription"),
        ("📋 Изменить подписку", "change_subscription"),
    ]
)
unfreeze_subscription_kb = create_inline_keyboard(
    [("🔥 Разморозить подписку", "unfreeze_subscription")]
)
to_registration_btn = create_inline_keyboard([("🚀 Зарегистрироваться", "to_registration")])
