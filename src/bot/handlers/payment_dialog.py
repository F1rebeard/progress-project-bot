import datetime
import logging
from typing import Any

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import ChatEvent, Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Column
from aiogram_dialog.widgets.kbd.select import Select
from aiogram_dialog.widgets.text import Const, Format
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handlers.workouts_for_start_program import set_start_program_date_for_new_subscription
from src.bot.keyboards.subscription import to_registration_btn
from src.dao import PaymentDAO, SubscriptionDAO, UserDAO
from src.database.config import connection
from src.database.models import Payment, Subscription, User
from src.database.models.payment import PaymentStatus
from src.database.models.subscription import SubscriptionStatus, SubscriptionType
from src.database.models.user import UserLevel, UserRole
from src.schemas.payment import PaymentCreateSchema
from src.schemas.subscription import SubscriptionCreateSchema
from src.schemas.user import UserCreateSchema, UserUpdateSchema

logger = logging.getLogger(__name__)


class SubscriptionPlan(BaseModel):
    id: int
    name: str
    description: str
    price: int
    days: int


progress_standard = SubscriptionPlan(
    id=1,
    name=SubscriptionType.STANDARD.value,
    description="💪 Тренируйся самостоятельно вместе с нашим дружным комьюнити.",
    price=4500,
    days=30,
)

progress_with_curator = SubscriptionPlan(
    id=2,
    name=SubscriptionType.WITH_CURATOR.value,
    description="👨‍🏫 Персональное сопровождение куратора: индивидуальные рекомендации и поддержка.",
    price=7000,
    days=30,
)

full_start = SubscriptionPlan(
    id=3,
    name=SubscriptionType.START_PROGRAM.value,
    description='🚀 Полная программа тренировок "Cтарт" c персональным сопровождением куратора.\n\n'
    ' Подготовь себя к "Прогрессу"!',
    price=10000,
    days=90,
)

month_start = SubscriptionPlan(
    id=4,
    name=SubscriptionType.ONE_MONTH_START.value,
    description='Один месяц по программе "Старт" c персональным сопровождением куратора.',
    price=10000,
    days=30,
)

sub_plans = (
    progress_standard.model_dump(exclude_unset=True),
    progress_with_curator.model_dump(exclude_unset=True),
    full_start.model_dump(exclude_unset=True),
    month_start.model_dump(exclude_unset=True),
)
payment_router = Router()


class ChoosePlanSG(StatesGroup):
    sub_plan_selection = State()
    sub_plan_details = State()


@payment_router.callback_query(F.data == "new_subscription")
async def start_new_sub_dialog(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
):
    await dialog_manager.start(state=ChoosePlanSG.sub_plan_selection)


async def on_plan_chosen(
    callback: ChatEvent,
    select: Any,
    manager: DialogManager,
    item_id: str,
):
    chosen_plan = next(plan for plan in sub_plans if plan["id"] == int(item_id))
    manager.dialog_data["chosen_plan"] = chosen_plan
    await manager.next()


async def get_chosen_plan(dialog_manager: DialogManager, **kwargs):
    chosen_plan = dialog_manager.dialog_data.get("chosen_plan", None)
    return {
        "chosen_plan": chosen_plan,
    }


@connection(commit=True)
async def process_new_subscription(
    callback: CallbackQuery,
    button: Any,
    manager: DialogManager,
    session: AsyncSession,
):
    telegram_id = callback.from_user.id
    username = callback.from_user.username
    chosen_plan = manager.dialog_data["chosen_plan"]
    logger.info(
        f"Выбранный тип подписки: {chosen_plan} для пользователя с 🆔 {callback.from_user.id}"
    )

    # Create a new user
    new_user_data = UserCreateSchema(telegram_id=telegram_id, username=username, role=UserRole.USER)
    new_user: User = await UserDAO.add(session=session, data=new_user_data)

    is_start_program: bool = chosen_plan["name"] in (
        SubscriptionType.START_PROGRAM.value,
        SubscriptionType.ONE_MONTH_START.ONE_MONTH_START.value,
    )
    if is_start_program:
        user_update_data = UserUpdateSchema(level=UserLevel.START)
        await UserDAO.update_one_by_id(session=session, data=user_update_data, data_id=telegram_id)

    # Create new subscription
    end_date = (datetime.datetime.today() + datetime.timedelta(days=chosen_plan["days"])).date()
    new_sub_data = SubscriptionCreateSchema(
        user_id=new_user.telegram_id,
        subscription_type=chosen_plan["name"],
        status=SubscriptionStatus.UNREGISTERED,
        end_date=end_date,
    )
    new_sub: Subscription = await SubscriptionDAO.add(session=session, data=new_sub_data)

    start_date = None
    if is_start_program:
        start_date = await set_start_program_date_for_new_subscription(
            telegram_id=telegram_id, subscription_type=chosen_plan["name"], session=session
        )
        if start_date:
            start_date_message = (
                f"\n\n📆 Программа СТАРТ начнется в понедельник ({start_date.strftime('%d.%m.%Y')})"
            )

    # Create new payment info
    payment_data = PaymentCreateSchema(
        sub_id=new_sub.user_id,
        sub_type=chosen_plan["name"],
        amount=chosen_plan["price"],
        status=PaymentStatus.COMPLETED,
    )
    new_payment_data: Payment = await PaymentDAO.add(session=session, data=payment_data)
    logger.info(f"New payment: {new_payment_data}")

    await manager.done()
    await callback.message.edit_text(
        f"✅ Оплата успешно проведена!\n\n"
        f"Подписка <b>{chosen_plan['name']}</b> активирована.\n"
        f"📅 Действует до <b>{new_sub.end_date.strftime('%d %B %Y')}</b>."
        f"{start_date_message if start_date else ''}\n\n"
        f"⬇️ Осталось завершить регистрацию ",
        reply_markup=to_registration_btn,
    )


subscription_selection_dialog = Dialog(
    Window(
        Const("Выберите тип подписки:"),
        Column(
            Select(
                Format("{item[name]}"),
                items=sub_plans,
                item_id_getter=lambda x: x["id"],
                id="select_sub_plan",
                on_click=on_plan_chosen,
            ),
        ),
        state=ChoosePlanSG.sub_plan_selection,
        getter=get_chosen_plan,
    ),
    Window(
        Format(
            "📋 <b>{dialog_data[chosen_plan][name]}</b>\n\n"
            "📅 Длительность: {dialog_data[chosen_plan][days]} дней\n"
            "💰 Цена: {dialog_data[chosen_plan][price]} ₽\n\n"
            "{dialog_data[chosen_plan][description]}"
        ),
        Button(
            text=Const("Оплатить подписку"), on_click=process_new_subscription, id="process_payment"
        ),
        Back(Const("Назад, к выбору подписки")),
        state=ChoosePlanSG.sub_plan_details,
    ),
)
