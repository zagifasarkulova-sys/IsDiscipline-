import asyncio
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_user, create_user, update_user,
    get_today_task, create_task, complete_task,
    get_week_stats, start_focus_session, end_focus_session,
    add_xp_and_streak, save_reflection,
    get_current_weekly_goal, save_weekly_goal, update_weekly_progress
)
from keyboards import (
    main_menu_kb, timer_choice_kb, focus_active_kb,
    energy_kb, morning_kb, evening_result_kb,
    goal_kb, progress_percent_kb, skip_kb, admin_kb
)
from states import FocusStates

router = Router()
logger = logging.getLogger(__name__)

# Active focus sessions: {user_id: {"message_id": int, "session_id": int, "end_time": datetime, "task": asyncio.Task}}
active_sessions = {}


# ─── START / ONBOARDING ────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await create_user(message.from_user.id, message.from_user.username or "")
        await message.answer(
            "👋 <b>Привет! Я Focus Mentor</b>\n\n"
            "Помогу тебе работать глубоко, не отвлекаться и двигаться к своим целям.\n\n"
            "Для начала — <b>напиши свою главную цель</b>.\n"
            "Это то, к чему ты стремишься в этот период жизни.\n\n"
            "Например: <i>«Запустить свой продукт», «Выучить английский до B2»</i>",
            parse_mode="HTML"
        )
        await state.set_state(FocusStates.setting_goal)
    else:
        await message.answer(
            "👋 Рад видеть тебя снова!\nВыбери действие:",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )


@router.message(FocusStates.setting_goal)
async def handle_goal_input(message: Message, state: FSMContext):
    goal = message.text.strip()
    await update_user(message.from_user.id, main_goal=goal)
    await state.clear()
    await message.answer(
        f"🎯 <b>Цель сохранена!</b>\n\n<i>{goal}</i>\n\n"
        "Теперь каждое утро я буду напоминать тебе о ней и помогать двигаться вперёд.\n\n"
        "Используй меню ниже 👇",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


# ─── MAIN MENU ─────────────────────────────────────────────────────────────────

@router.message(F.text == "🚀 Начать фокус")
async def handle_start_focus(message: Message, state: FSMContext):
    if message.from_user.id in active_sessions:
        await message.answer("⏳ У тебя уже идёт сессия фокуса!")
        return
    await message.answer(
        "⚡ <b>Deep Work</b>\n\nВыбери длительность сессии:",
        reply_markup=timer_choice_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Прогресс")
async def handle_progress(message: Message):
    stats = await get_week_stats(message.from_user.id)
    user = await get_user(message.from_user.id)
    xp = user["xp"] if user else 0
    streak = user["streak"] if user else 0

    hours = stats["focus_minutes"] // 60
    mins = stats["focus_minutes"] % 60

    await message.answer(
        f"📊 <b>Твой прогресс за 7 дней</b>\n\n"
        f"✅ Задач выполнено: {stats['completed']} из {stats['total']}\n"
        f"⏱ В фокусе: {hours}ч {mins}мин\n"
        f"🔥 Серия дней: {streak} дней подряд\n"
        f"⭐ Всего XP: {xp}\n\n"
        f"{'🏆 Отличный результат!' if stats['completed'] >= stats['total'] * 0.8 else '💪 Продолжай работать!'}",
        parse_mode="HTML"
    )


@router.message(F.text == "🎯 Моя цель")
async def handle_my_goal(message: Message):
    user = await get_user(message.from_user.id)
    weekly = await get_current_weekly_goal(message.from_user.id)

    goal = user["main_goal"] if user else "не задана"
    week_goal = weekly["goal"] if weekly else "не задана"
    prog = weekly["progress_percent"] if weekly else 0

    await message.answer(
        f"🎯 <b>Твои цели</b>\n\n"
        f"🏔 Главная цель:\n<i>{goal}</i>\n\n"
        f"📅 Цель недели:\n<i>{week_goal}</i>\n"
        f"📈 Прогресс: {prog}%\n\n"
        f"{'█' * (prog // 10)}{'░' * (10 - prog // 10)} {prog}%",
        reply_markup=goal_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📝 Итог дня")
async def handle_day_review(message: Message, state: FSMContext):
    task = await get_today_task(message.from_user.id)
    if not task:
        await message.answer(
            "📝 <b>Задача на сегодня не поставлена</b>\n\n"
            "Напиши главную задачу дня — что хочешь сделать сегодня?",
            parse_mode="HTML"
        )
        await state.set_state(FocusStates.entering_task)
        return

    task_text = task["main_task"] or "не указана"
    completed = task["completed"]

    status = "✅ Выполнена" if completed else "⏳ Ещё не завершена"
    await message.answer(
        f"📝 <b>Итог дня</b>\n\n"
        f"Задача: <i>{task_text}</i>\n"
        f"Статус: {status}",
        reply_markup=evening_result_kb() if not completed else None,
        parse_mode="HTML"
    )


# ─── MORNING MODULE ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "morning_enter")
async def cb_morning_enter(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "🔋 <b>Как твой энергетический уровень сегодня?</b>",
        reply_markup=energy_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("energy_"))
async def cb_energy(callback: CallbackQuery, state: FSMContext):
    level_map = {"energy_low": "🔋 Низкий", "energy_medium": "⚡ Средний", "energy_high": "🔥 Высокий"}
    level = level_map.get(callback.data, "⚡ Средний")
    await state.update_data(energy_level=callback.data.replace("energy_", ""))
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        f"Энергия: {level}\n\n"
        "✍️ <b>Напиши главную задачу дня</b>\n"
        "<i>Одна задача, которую выполнив, ты будешь доволен этим днём</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.entering_task)


@router.callback_query(F.data == "morning_skip")
async def cb_morning_skip(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "⏭ Пропустил утренний фокус.\n"
        "Помни: без чёткой задачи день уходит в никуда 💨"
    )


@router.message(FocusStates.entering_task)
async def handle_task_input(message: Message, state: FSMContext):
    data = await state.get_data()
    energy = data.get("energy_level", "medium")
    task_id = await create_task(message.from_user.id, message.text.strip(), energy)
    await state.update_data(current_task_id=task_id)
    await state.clear()
    await message.answer(
        f"✅ <b>Задача дня поставлена!</b>\n\n"
        f"📌 <i>{message.text.strip()}</i>\n\n"
        "Теперь иди делать это. Удачи! 💪",
        parse_mode="HTML"
    )


# ─── FOCUS TIMER ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("timer_"))
async def cb_timer_select(callback: CallbackQuery, state: FSMContext):
    if callback.data == "timer_custom":
        await callback.message.edit_reply_markup()
        await callback.message.answer("✏️ Введи время в минутах (от 5 до 180):")
        await state.set_state(FocusStates.custom_timer)
        return

    durations = {"timer_25": 25, "timer_50": 50, "timer_90": 90}
    duration = durations[callback.data]
    await callback.message.edit_reply_markup()
    await start_focus(callback.message, callback.from_user.id, duration, state)


@router.message(FocusStates.custom_timer)
async def handle_custom_timer(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if not (5 <= duration <= 180):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введи число от 5 до 180")
        return
    await state.clear()
    await start_focus(message, message.from_user.id, duration, state)


async def start_focus(message: Message, user_id: int, duration: int, state: FSMContext):
    session_id = await start_focus_session(user_id, duration)
    end_time = datetime.now().timestamp() + duration * 60

    task = await get_today_task(user_id)
    task_text = task["main_task"] if task else "не указана"

    msg = await message.answer(
        _format_timer(duration, duration, task_text),
        reply_markup=focus_active_kb(),
        parse_mode="HTML"
    )

    active_sessions[user_id] = {
        "message_id": msg.message_id,
        "chat_id": message.chat.id,
        "session_id": session_id,
        "end_time": end_time,
        "duration": duration,
        "task_text": task_text,
    }

    # Start background timer
    bot = message.bot
    asyncio.create_task(_run_timer(bot, user_id))


def _format_timer(remaining_min: int, total_min: int, task_text: str) -> str:
    filled = int((1 - remaining_min / total_min) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    h = remaining_min // 60
    m = remaining_min % 60
    time_str = f"{h}ч {m}мин" if h > 0 else f"{m} мин"
    return (
        f"🎯 <b>Режим глубокой работы</b>\n\n"
        f"📌 {task_text}\n\n"
        f"⏳ Осталось: <b>{time_str}</b>\n"
        f"[{bar}]\n\n"
        f"<i>Убери телефон. Работай.</i>"
    )


async def _run_timer(bot: Bot, user_id: int):
    import time
    session = active_sessions.get(user_id)
    if not session:
        return

    duration = session["duration"]
    remaining = duration

    while remaining > 0:
        await asyncio.sleep(60)
        session = active_sessions.get(user_id)
        if not session:
            return  # Session was cancelled

        remaining -= 1

        try:
            await bot.edit_message_text(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                text=_format_timer(remaining, duration, session["task_text"]),
                reply_markup=focus_active_kb(),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Timer finished
    session = active_sessions.pop(user_id, None)
    if session:
        await end_focus_session(session["session_id"], completed=True)
        # Убираем кнопки со старого сообщения
        try:
            await bot.edit_message_reply_markup(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                reply_markup=None
            )
        except Exception:
            pass
        # Новое сообщение = пуш-уведомление на телефоне
        try:
            await bot.send_message(
                chat_id=session["chat_id"],
                text=f"🔔 <b>Сессия завершена!</b>\n\n"
                     f"⏱ {duration} минут глубокой работы — отличный результат!\n\n"
                     f"Сделай перерыв 5-10 минут. Ты заслужил 💪",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data == "focus_done")
async def cb_focus_done(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.pop(user_id, None)
    if session:
        elapsed = session["duration"] - int((session["end_time"] - datetime.now().timestamp()) / 60)
        elapsed = max(elapsed, 1)
        await end_focus_session(session["session_id"], completed=True)
        await callback.message.edit_text(
            f"✅ <b>Молодец!</b>\n\n"
            f"Завершил сессию раньше времени.\n"
            f"Проведено в фокусе: ~{elapsed} мин 💪",
            parse_mode="HTML"
        )
    else:
        await callback.answer("Сессия не найдена")


@router.callback_query(F.data == "focus_quit")
async def cb_focus_quit(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.pop(user_id, None)
    if session:
        await end_focus_session(session["session_id"], completed=False)
        await callback.message.edit_text(
            "😔 <b>Сессия прервана</b>\n\n"
            "Отвлечься — это нормально. Но помни: каждый раз когда сдаёшься, "
            "ты тренируешь привычку сдаваться.\n\n"
            "Попробуй снова. Даже 10 минут лучше нуля.",
            parse_mode="HTML"
        )
    else:
        await callback.answer("Сессия не найдена")


# ─── EVENING AUDIT ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "evening_yes")
async def cb_evening_yes(callback: CallbackQuery):
    await complete_task(callback.from_user.id)
    streak, xp_gain = await add_xp_and_streak(callback.from_user.id)
    user = await get_user(callback.from_user.id)

    streak_msg = f"🔥 Серия: {streak} дней подряд!" if streak > 1 else "🔥 Начало серии!"

    await callback.message.edit_text(
        f"🎉 <b>Отлично! Задача выполнена!</b>\n\n"
        f"⭐ +{xp_gain} XP\n"
        f"{streak_msg}\n"
        f"💫 Всего XP: {user['xp']}\n\n"
        f"{'🏆 Легенда! 10+ дней подряд!' if streak >= 10 else ''}",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "evening_no")
async def cb_evening_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💭 <b>Что помешало выполнить задачу?</b>\n\n"
        "<i>Это не наказание — это рефлексия. Понять причину = не повторить завтра.</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.reflection_prevented)


@router.message(FocusStates.reflection_prevented)
async def handle_reflection_prevented(message: Message, state: FSMContext):
    await state.update_data(what_prevented=message.text.strip())
    await message.answer(
        "💡 <b>Что сделаешь иначе завтра?</b>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.reflection_change)


@router.message(FocusStates.reflection_change)
async def handle_reflection_change(message: Message, state: FSMContext):
    data = await state.get_data()
    await save_reflection(
        message.from_user.id,
        data.get("what_prevented", ""),
        message.text.strip()
    )
    # Reset streak
    await update_user(message.from_user.id, streak=0)
    await state.clear()
    await message.answer(
        "📝 <b>Рефлексия сохранена</b>\n\n"
        "Завтра новый день. Новая задача. Новый шанс.\n\n"
        "Streak сбросился до 0, но это не конец — это начало 💪",
        parse_mode="HTML"
    )


# ─── GOAL MANAGEMENT ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "goal_edit")
async def cb_goal_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("✏️ Напиши новую главную цель:")
    await state.set_state(FocusStates.editing_goal)


@router.message(FocusStates.editing_goal)
async def handle_goal_edit(message: Message, state: FSMContext):
    await update_user(message.from_user.id, main_goal=message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ <b>Цель обновлена!</b>\n\n<i>{message.text.strip()}</i>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "goal_progress")
async def cb_goal_progress(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "📈 На сколько процентов ты продвинулся к цели недели?",
        reply_markup=progress_percent_kb()
    )


@router.callback_query(F.data.startswith("prog_"))
async def cb_progress_update(callback: CallbackQuery):
    percent = int(callback.data.replace("prog_", ""))
    await update_weekly_progress(callback.from_user.id, percent)
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    await callback.message.edit_text(
        f"📈 <b>Прогресс обновлён: {percent}%</b>\n\n[{bar}]",
        parse_mode="HTML"
    )


# ─── WEEKLY GOAL ───────────────────────────────────────────────────────────────

@router.message(FocusStates.entering_weekly_goal)
async def handle_weekly_goal(message: Message, state: FSMContext):
    await save_weekly_goal(message.from_user.id, message.text.strip())
    await state.clear()
    await message.answer(
        f"🎯 <b>Цель на неделю:</b>\n<i>{message.text.strip()}</i>\n\n"
        "Удачи! Каждый день маленький шаг вперёд 🚀",
        parse_mode="HTML"
    )


# ─── ADMIN ─────────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(
        "⚙️ <b>Настройки</b>",
        reply_markup=admin_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_morning")
async def cb_admin_morning(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("🌅 Введи время утреннего уведомления в формате HH:MM\nНапример: 07:30")
    await state.set_state(FocusStates.admin_set_morning)


@router.callback_query(F.data == "admin_evening")
async def cb_admin_evening(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("🌙 Введи время вечернего уведомления в формате HH:MM\nНапример: 21:00")
    await state.set_state(FocusStates.admin_set_evening)


@router.message(FocusStates.admin_set_morning)
async def handle_admin_morning(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer("⚠️ Неверный формат. Используй HH:MM, например 08:00")
        return
    await update_user(message.from_user.id, morning_time=time_str)
    await state.clear()
    await message.answer(f"✅ Утреннее уведомление: {time_str}")


@router.message(FocusStates.admin_set_evening)
async def handle_admin_evening(message: Message, state: FSMContext):
    time_str = message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer("⚠️ Неверный формат. Используй HH:MM, например 21:00")
        return
    await update_user(message.from_user.id, evening_time=time_str)
    await state.clear()
    await message.answer(f"✅ Вечернее уведомление: {time_str}")


# ─── SKIP ──────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "skip")
async def cb_skip(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup()
    await callback.answer("Пропущено")
