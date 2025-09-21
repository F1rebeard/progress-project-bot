import logging
from typing import Any

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Column, NextPage, PrevPage, Row, Select
from aiogram_dialog.widgets.text import Const, Format, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handlers.workout_calendar import go_to_main_menu
from src.constants.sinkler_coefficients import MAX_REPS, MIN_REPS
from src.dao import (
    BiometricDAO,
    ExerciseStandardDAO,
    LeaderboardDAO,
    ProfileCategoryDAO,
    ProfileExerciseDAO,
    UserDAO,
    UserProfileResultDAO,
)
from src.database.config import connection
from src.database.models import ProfileCategory, ProfileExercise, User, UserProfileResult
from src.database.models.profile import ResultType
from src.schemas import BiometricUpdateSchema
from src.schemas.profile import ProfileResultSubmitSchema
from src.utils.coefficient import calculate_coefficient_value, get_coefficient_data
from src.utils.profile import (
    calculate_total_completion,
    format_result_value,
    time_format_for_time_based_exercise,
)

logger = logging.getLogger(__name__)

profile_router = Router()

HISTORY_RECORD_PER_PAGE: int = 20

MAX_WEIGHT = 1
MIN_WEIGHT = 1

class ProfileSG(StatesGroup):
    profile = State()
    category = State()
    exercise = State()
    add_result = State()
    add_weight = State()
    biometrics = State()
    leaderboard = State()
    add_coefficient_result = State()
    # TODO delete and edit for ADMIN


@profile_router.callback_query(F.data == "profile")
async def open_profile_menu(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
):
    """
    Open profile menu on clicking profile button in main menu.
    """
    await dialog_manager.start(state=ProfileSG.profile)


async def get_category_completion_for_user(
    session: AsyncSession,
    user_id: int,
    category: ProfileCategory,
) -> dict[str, Any] | None:
    """
    Calculate completion percentage for a single category for current user.

    Args:
        session: Database session
        user_id: User's telegram ID
        category: Category object from database

    Returns:
        Tuple of (completion_data, filled_count, exercises_count)
    """
    total_exercises_in_cat = await ProfileExerciseDAO.count_exercises_in_category(
        session=session,
        category_name=category.name,
    )
    if total_exercises_in_cat == 0:
        logger.debug(f"Category {category.name} has no exercises")
        return None

    count_filled_exercises = await UserProfileResultDAO.count_unique_exercises_with_results(
        session=session,
        user_id=user_id,
        category_name=category.name,
    )
    completion_percentage = (
        int((count_filled_exercises / total_exercises_in_cat) * 100)
        if count_filled_exercises > 0 and total_exercises_in_cat > 0
        else 0
    )
    category_completion_data = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "exercises_count": total_exercises_in_cat,
        "filled_count": count_filled_exercises,
        "percentage": completion_percentage,
    }
    logger.debug(f"Category {category.name} completion data: {category_completion_data}")
    return category_completion_data


@connection(commit=False)
async def get_profile_categories(
    dialog_manager: DialogManager, session: AsyncSession, **kwargs
) -> dict[str, Any]:
    """
    Get all profile categories and calculate completion percentages.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of category completion data.
    """
    user_id = dialog_manager.event.from_user.id
    categories = await ProfileCategoryDAO.find_all(session=session, filters=None)
    total_filled = 0
    total_exercises = 0
    total_data = []
    for category in categories:
        category_completion_data = await get_category_completion_for_user(
            session=session,
            user_id=user_id,
            category=category,
        )
        if category_completion_data:
            total_data.append(category_completion_data)
            total_filled += category_completion_data.get("filled_count", 0)
            total_exercises += category_completion_data.get("exercises_count", 0)

    biometrics_data = await UserDAO.get_user_biometrics(session=session, user_id=user_id)
    dialog_manager.dialog_data["biometrics"] = biometrics_data

    total_complete_percentage = await calculate_total_completion(
        total_filled=total_filled,
        total_exercises=total_exercises,
    )
    profile_data: dict = {
        "categories": total_data,
        "biometrics": biometrics_data,
        "total_complete_percentage": total_complete_percentage,
        "total_exercises": total_exercises,
        "total_filled": total_filled,
    }
    logger.debug(f"Profile data: {profile_data} for user {user_id}")
    return profile_data


@connection(commit=False)
async def get_exercises_for_category(
    dialog_manager: DialogManager, session: AsyncSession, **kwargs
):
    """
    Get all exercises for the selected category with current user results.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of exercises data for the selected category.
    """

    user_id = dialog_manager.event.from_user.id
    category_id = dialog_manager.dialog_data.get("selected_category_id")

    if not category_id:
        return {"exercises": [], "category_name": "Нету id категории"}

    category: ProfileCategory = await ProfileCategoryDAO.find_one_or_none_by_id(
        data_id=category_id, session=session
    )
    if not category:
        return {"exercises": [], "category_name": f"Категория c id {category_id} не найдена!"}

    category_data = await get_category_completion_for_user(
        session=session,
        user_id=user_id,
        category=category,
    )

    filled_count = category_data.get("filled_count", 0)
    exercises_count = category_data.get("exercises_count", 0)
    percentage = category_data.get("percentage", 0)

    exercises_in_category = await ProfileExerciseDAO.get_exercises_by_category(
        session=session, category_name=category.name
    )
    exercises_data = []

    for exercise in exercises_in_category:
        latest_result = await UserProfileResultDAO.get_latest_result(
            session=session,
            user_id=user_id,
            exercise_id=exercise.id,
        )

        exercises_data.append(
            {
                "id": exercise.id,
                "name": exercise.name,
                "has_result": latest_result is not None,
                "result_value": await format_result_value(latest_result)
                if latest_result
                else "(Ноу инфоу)",
                "unit": exercise.unit.value if latest_result else "",
            }
        )
    category_data = {
        "exercises": exercises_data,
        "category_name": category.name,
        "description": category.description,
        "filled_count": filled_count,
        "exercises_count": exercises_count,
        "percentage": percentage,
    }
    logger.debug(f"Category {category.name} data: {category_data}")
    return category_data


@connection(commit=True)
async def result_input_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
    session: AsyncSession,
):
    """
    Handle user input for result submit.

    If the exercise is time-based, parse MM:SS or seconds format.
    Otherwise, parse a float value.
    Add a new result with validation against exercise standards.
    If the result is valid, switch back to exercise selection.
    Otherwise, show an error message.
    """
    user_id = message.from_user.id
    exercise_id = manager.dialog_data.get("selected_exercise_id")
    try:
        exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
            data_id=exercise_id, session=session
        )
        try:
            if exercise.is_time_based:
                # Parse time format (MM:SS or seconds)
                if ":" in message.text:
                    minutes, seconds = message.text.split(":")
                    result_value = float(minutes) * 60 + float(seconds)
                else:
                    result_value = float(message.text)
            else:
                result_value = float(message.text.replace(",", "."))
        except ValueError:
            await message.answer(
                "❌ Некорректный формат. "
                + (
                    "Введите время в формате ММ:СС или в секундах."
                    if exercise.is_time_based
                    else "Введите числовое значение."
                )
            )
            return

        result_data = ProfileResultSubmitSchema(
            exercise_id=exercise_id,
            result_value=result_value,
        )
        new_result, validation_message = await UserProfileResultDAO.add_result_with_validation(
            session=session,
            user_id=user_id,
            data=result_data,
        )
        if new_result:
            # Success - show a nice confirmation and return to exercise view
            formatted_value = result_value
            if exercise.is_time_based:
                minutes = int(result_value) // 60
                seconds = int(result_value) % 60
                formatted_value = f"{minutes}:{seconds:02d}"

            await message.answer(
                f"✅ Результат <b>{formatted_value} {exercise.unit.value}</b> "
                f"для упражнения <b>{exercise.name}</b> успешно добавлен!"
            )
            await manager.switch_to(ProfileSG.exercise)
        elif float(message.from_user.text) < 0:
            await message.answer(
                "❌ Введенное значение не может быть отрицательным.\n\n"
                "Пожалуйста, введите результат в пределах допустимых значений"
            )
        # Error - show a friendly error message with guidance
        elif "unrealistically high" in validation_message or "too high" in validation_message:
            await message.answer(
                "❌ Введенное значение слишком большое.\n\n"
                "Пожалуйста, введите результат в пределах допустимых значений"
            )
        elif "unrealistically fast" in validation_message or "too low" in validation_message:
            await message.answer(
                "❌ Введенное значение слишком маленькое.\n\n"
                "Пожалуйста, введите результат в пределах допустимых значений"
            )
        else:
            await message.answer(
                f"❌ {validation_message}\n\n"
                f"Пожалуйста, проверьте введенное значение и попробуйте снова."
            )

    except Exception as e:
        logger.error(f"Error adding result: {e}")
        await message.answer(
            "❌ Произошла ошибка при добавлении результата.\n\n"
            "Пожалуйста, попробуйте снова или обратитесь к администратору."
        )


@connection(commit=False)
async def get_exercise_history(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    """
    Get details and history for a specific exercise.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of exercise details and history.
    """
    user_id = dialog_manager.event.from_user.id
    exercise_id = dialog_manager.dialog_data.get("selected_exercise_id")
    if not exercise_id:
        return {"exercise": None, "results": []}

    user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if user and user.level and user.gender:
        gender_standards = await ExerciseStandardDAO.get_gender_standards(
            session=session, exercise_id=exercise_id, user_level=user.level, gender=user.gender
        )

    exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id, session=session
    )
    if not exercise:
        logger.warning(f"Exercise with id {exercise_id} not found")
        return {"exercise": None, "results": []}

    history: list[UserProfileResult] = await UserProfileResultDAO.get_history_for_exercise(
        session=session,
        user_id=user_id,
        exercise_id=exercise_id,
    )
    logger.debug(f"Raw history results count: {len(history)}")
    for i, result in enumerate(history):
        logger.debug(f"Result {i}: id={result.id}, value={result.result_value}, date={result.date}")

    # Create history data with proper error handling
    history_data = []
    for result in history:
        try:
            formatted_date = result.date.strftime("%d.%m.%Y")
            result_value = result.result_value
            unit_value = exercise.unit.value

            history_data.append(
                {
                    "date": formatted_date,
                    "value": result_value,
                    "unit": unit_value,
                }
            )
        except Exception as e:
            logger.error(f"Error creating history data: {e}")

    try:
        await time_format_for_time_based_exercise(
            history_data=history_data,
            exercise=exercise,
        )
    except Exception as e:
        logger.error(f"Error formatting values: {e}")
        for item in history_data:
            if "formatted_value" not in item:
                item["formatted_value"] = str(item.get("value", ""))

    # Log the history data count
    logger.debug(f"Processed history data count: {len(history_data)}")
    await time_format_for_time_based_exercise(
        history_data=history_data,
        exercise=exercise,
    )
    exercise_data = {
        "exercise": {
            "id": exercise.id,
            "name": exercise.name,
            "description": exercise.description,
            "unit": exercise.unit.value,
            "result_type": exercise.result_type,
            "is_time_based": exercise.is_time_based,
            "category": exercise.category_name,
        },
        "results": history_data,
        "standards": gender_standards,
    }
    logger.debug(f"Exercise {exercise.name} for user {user_id} with history: {history_data}")
    return exercise_data


@connection(commit=False)
async def get_exercise_leaderboard(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    """
    Get leaderboard data for a specific exercise.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of leaderboard data.
    """
    exercise_id = dialog_manager.dialog_data.get("selected_exercise_id")
    user_id = dialog_manager.event.from_user.id

    exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id, session=session
    )
    if not exercise:
        return {"exercise": None, "leaderboard": []}
    user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    leaderboard_data = await LeaderboardDAO.get_exercise_leaderboard(
        session=session, exercise_id=exercise_id, gender=user.gender
    )
    user_ranking_data = await LeaderboardDAO.get_user_ranking(
        session=session, user_id=user_id, exercise_id=exercise_id
    )
    data = {
        "exercise_name": exercise.name,
        "unit": exercise.unit.value,
        "is_time_based": exercise.is_time_based,
        "result_type": exercise.result_type.value,
        "leaderboard": leaderboard_data,
        "user_ranking": user_ranking_data,
    }
    return data


@connection(commit=True)
async def coefficient_input_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
    session: AsyncSession,
):
    """
    Handler input for coefficient exercise.

    Args:
        message: message text from user
        message_input: type of message from user
        manager: dialog manager to handle
        session: database session
    """
    user_id = message.from_user.id
    exercise_id = manager.dialog_data.get("selected_exercise_id")

    coefficient_data, ready, error_message = await get_coefficient_data(
        session=session,
        exercise_id=exercise_id,
        user_id=user_id,
    )
    if not ready:
        await message.answer(error_message)
        return
    logger.info(f"{coefficient_data} for user {user_id}, {ready}, {exercise_id}")

    reps = int(message.text)
    if reps < MIN_REPS:
        await message.answer(f"Пошутили и хватит, 😬 количество повторений больше {MIN_REPS}")
        return
    elif reps > MAX_REPS:
        await message.answer(f"Тут без видео никак 🤥, максимум 100 повторений {MAX_REPS}")
        return

    coefficient = calculate_coefficient_value(
        data=coefficient_data,
        reps=reps,
    )
    logger.debug(f"Calculated coefficient value: {coefficient}")

    workout_weight = coefficient_data.workout_weight
    result_data = ProfileResultSubmitSchema(
        exercise_id=exercise_id,
        result_value=coefficient,
    )
    logger.debug(f"Result data: {result_data}")
    new_result, validation_message = await UserProfileResultDAO.add_result_with_validation(
        session=session,
        user_id=user_id,
        data=result_data,
    )
    logger.debug(f"New result: {new_result}, {validation_message}")
    if new_result:
        exercise = coefficient_data.coefficient_exercise
        await message.answer(
            f"✅ Результат сохранен\n\n"
            f"Упражнение: <b>{exercise.name}</b>\n"
            f"Повторения: <b>{reps}</b>\n"
            f"Рабочий вес: <b>{workout_weight:.1f} кг</b>\n"
            f"Коэффициент Синклера: <b>{coefficient}</b>"
        )
        await manager.switch_to(ProfileSG.exercise)
    else:
        await message.answer(f"{validation_message} fsfsddsfsdf")


@connection(commit=True)
async def edit_weight_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
    session: AsyncSession,
):
    """
    Handles weight editing for a user during the registration process in the application. It parses the
    weight from the user's input, validates it against minimum and maximum constraints, updates the
    weight in the database if valid, and provides feedback throughout the process. This handler also
    manages transitions in the dialog's state upon successful completion.

    Args:
        message (Message): Incoming message object containing details about the user's input.
        message_input (MessageInput): Input configuration for dialogs.
        manager (DialogManager): Facilitates management of dialog states and transitions.
        session (AsyncSession): Asynchronous database session for executing operations.

    Raises:
        ValueError: If the input value cannot be converted to a float.
        Exception: For unexpected errors during the weight update process.
    """
    user_id = message.from_user.id

    try:
        weight = float(message.text.replace(",", "."))
        if MIN_WEIGHT <= weight <= MAX_WEIGHT:
            data_to_add = BiometricUpdateSchema(weight=weight)
            await BiometricDAO.update_one_by_id(
                session=session,
                data_id=user_id,
                data=data_to_add,
            )
            await message.answer(f"✅ Вес обновлен {weight} кг")
            await manager.switch_to(ProfileSG.biometrics)
        else:
            await message.answer(
                f"Вес должен быть от {MAX_WEIGHT} до {MAX_WEIGHT} кг. Пожалуйста, введи корректное "
                f"значение."
            )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное числовое значение для веса в килограммах."
        )
    except Exception as e:
        logger.error(f"Error in weight handler during registration: {e}")


# Button clicks handlers
async def on_category_click(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """
    Handle category selection.
    """
    manager.dialog_data["selected_category_id"] = int(item_id)
    await manager.switch_to(ProfileSG.category)


async def on_exercise_click(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    """
    Handle exercise selection.
    """
    manager.dialog_data["selected_exercise_id"] = int(item_id)
    await manager.switch_to(ProfileSG.exercise)


async def on_leaderboard_click(callback: CallbackQuery, button, manager: DialogManager):
    """
    Show a leaderboard for the selected exercise.
    """
    await manager.switch_to(ProfileSG.leaderboard)


async def on_biometrics_click(callback: CallbackQuery, button, manager: DialogManager):
    """
    Handle biometrics button click.
    """
    await manager.switch_to(ProfileSG.biometrics)


async def on_add_result_click(callback: CallbackQuery, button, manager: DialogManager):
    """
    Handle add result button click.
    """
    exercise_id = manager.dialog_data.get("selected_exercise_id")
    session = manager.middleware_data.get("session_without_commit")
    exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id,
        session=session,
    )
    if exercise and exercise.result_type == ResultType.COEFFICIENT:
        user_id = callback.from_user.id
        coefficient_data, ready, message = await get_coefficient_data(
            session=session,
            exercise_id=exercise_id,
            user_id=user_id,
        )
        if not ready:
            await callback.answer(message, show_alert=True)
            return

        manager.dialog_data["workout_weight"] = round(coefficient_data.workout_weight, 1)
        manager.dialog_data["base_exercise_name"] = coefficient_data.base_exercise.name

        await manager.switch_to(ProfileSG.add_coefficient_result)
    else:
        await manager.switch_to(ProfileSG.add_result)


async def other_type_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Handle non-text input when adding exercise results.
    """
    await message.answer("❌ Пожалуйста, введите числовое значение в виде текста!")


profile_dialog = Dialog(
    Window(
        Const("👤 Профиль\n"),
        Format(
            "Профиль заполнен на <b>{total_complete_percentage}%</b>"
            " ({total_filled}/{total_exercises})\n\n"
        ),
        Column(
            Select(
                Format(
                    "{item[name]} - {item[filled_count]}/{item[exercises_count]}"
                    " ({item[percentage]}%)"
                ),
                id="category_select",
                item_id_getter=lambda x: x["id"],
                items="categories",
                on_click=on_category_click,
            ),
            Button(
                Const("📏 Биометрия"),
                id="biometrics_button",
                on_click=on_biometrics_click,
            ),
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=ProfileSG.profile,
        getter=get_profile_categories,
    ),
    Window(
        Format(
            " <b>{category_name}</b>\n\n{description}\n\n"
            "📊 Заполнено <b>{filled_count}/{exercises_count}</b> ({percentage}%)\n"
        ),
        Const("Выбери упражнение:"),
        Column(
            Select(
                Format(
                    "{item[name]} {item[result_value]} {item[unit]}",
                ),
                id="exercise_select",
                item_id_getter=lambda x: x["id"],
                items="exercises",
                on_click=on_exercise_click,
            ),
        ),
        Button(
            Const("Назад к категориям"),
            id="back_to_categories",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.profile),
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=ProfileSG.category,
        getter=get_exercises_for_category,
    ),
    Window(
        Format(
            "<b>Биометрия</b>\n\n"
            "⚖️ Вес: {biometrics[weight]:.1f} кг\n"
            "📏 Рост: {biometrics[height]:.0f} cм\n"
            "🎂 Дршечка: {biometrics[birthday]}"
        ),
        Button(
            Const("Изменить вес"),
            id="change_weight",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.add_weight),
        ),
        Button(
            Const("Назад к категориям"),
            id="back_to_categories",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.profile),
        ),
        state=ProfileSG.biometrics,
        getter=get_profile_categories,
    ),
    Window(
        Const("⚖️ Введите свой <b>вес</b> в килограммах (например, 70.2):"),
        MessageInput(edit_weight_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Button(
            Const("Назад"),
            id="back_to_biometrics",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.biometrics),
        ),
        state=ProfileSG.add_weight,
    ),
    Window(
        Format("<b>{exercise[name]}</b>\n"),
        Format("{exercise[description]}\n\n"),
        Format(
            "<b>История результатов:</b>\n",
            when=lambda data, *_: data.get("results") and len(data["results"]) > 0,
        ),
        Format(
            "Еще нет результатов для этого упражнения 🫠",
            when=lambda data, *_: not data.get("results") or len(data["results"]) == 0,
        ),
        List(
            Format("{item[date]}: {item[formatted_value]} {item[unit]}"),
            items="results",
            when=lambda data, *_: data.get("results") and len(data["results"]) > 0,
            id="history_list",
            page_size=HISTORY_RECORD_PER_PAGE,
        ),
        Row(
            PrevPage(
                scroll="history_list",
                text=Const("◀️ Назад"),
                id="history_prev",
            ),
            NextPage(
                scroll="history_list",
                text=Const("Вперед ▶️"),
                id="history_next",
            ),
            when=lambda data, *_: data.get("results")
            and len(data["results"]) > HISTORY_RECORD_PER_PAGE,
        ),
        Button(Const("✍️ Добавить результат"), id="add_result", on_click=on_add_result_click),
        Button(Const("📊 Лидерборд"), id="show_leaderboard", on_click=on_leaderboard_click),
        Button(
            Const("Назад к упражнениям"),
            id="back_to_exercises",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.category),
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=ProfileSG.exercise,
        getter=get_exercise_history,
    ),
    Window(
        Format("<b>✍️ Добавить результат</b>\n\n🏋️‍♂️Упражнение: <b>{exercise[name]}</b>"),
        Format(
            "😱Диапазон значений: "
            "от <b>{standards[min_value]}</b> до <b>{standards[max_value]} {exercise[unit]}</b>\n",
            when=lambda data, *_: data.get("standards")
            and data["standards"].get("min_value") is not None
            and data["standards"].get("max_value") is not None,
        ),
        Format(
            "Напиши результат в формате ММ:СС (например, 2:30) или в секундах (например, 150)",
            when=lambda data, *_: data.get("exercise") and data["exercise"].get("is_time_based"),
        ),
        Format(
            "Введи числовое значение (например, 75)",
            when=lambda data, *_: data.get("exercise")
            and not data["exercise"].get("is_time_based"),
        ),
        MessageInput(result_input_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Back(Const("Назад к упражнению")),
        state=ProfileSG.add_result,
        getter=get_exercise_history,
    ),
    Window(
        Format("<b>✍️ Добавить результат</b>\n\n🏋️‍Упражнение: <b>{exercise[name]}</b>"),
        Format("Рабочий вес: <b>{dialog_data[workout_weight]} кг</b>"),
        Format("Основан на результате в упражнении <b>{dialog_data[base_exercise_name]}</b>\n"),
        Const("Введи количество повторений с этим весом:"),
        MessageInput(coefficient_input_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Button(
            Const("Назад к упражнению"),
            id="back_to_exercise",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.exercise),
        ),
        state=ProfileSG.add_coefficient_result,
        getter=get_exercise_history,
    ),
    Window(
        Format("📊 <b>Лидерборд: {exercise_name}</b>\n"),
        Format(
            "🏆 Твое место: <b>{user_ranking[position]}</b> из {user_ranking[total_users]}\n"
            "Результат: <b>{user_ranking[formatted_value]} {unit}</b>\n",
            when=lambda data, *_: data.get("user_ranking") is not None,
        ),
        Format(
            "❗ Нет результатов в этом упражнении\n",
            when=lambda data, *_: data.get("user_ranking") is None,
        ),
        Const("<b>🥇 Топ участников:</b>\n"),
        List(
            Format(
                "{item[position]}. {item[user_name]} @{item[username]} <b>{item[formatted_value]} {item[unit]}</b>"
            ),
            items="leaderboard",
            id="leaderboard_list",
            page_size=20,
        ),
        Row(
            PrevPage(scroll="leaderboard_list", text=Const("◀️ Назад"), id="leaderboard_prev"),
            NextPage(scroll="leaderboard_list", text=Const("Вперед ▶️"), id="leaderboard_next"),
        ),
        Button(
            Const("Назад к упражнению"),
            id="back_to_exercise",
            on_click=lambda c, b, m: m.switch_to(ProfileSG.exercise),
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=ProfileSG.leaderboard,
        getter=get_exercise_leaderboard,
    ),
)
