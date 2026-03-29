import asyncio
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_user, create_user, update_user,
    get_today_task, create_task, update_today_task, complete_task,
    get_week_stats, start_focus_session, end_focus_session,
    add_xp_and_streak, save_reflection,
    get_current_weekly_goal, save_weekly_goal, update_weekly_progress
)
from keyboards import (
    main_menu_kb, timer_choice_kb, focus_active_kb, focus_paused_kb,
    after_session_kb, break_choice_kb, energy_kb, morning_kb, morning_has_task_kb,
    evening_result_kb, goal_kb, progress_percent_kb,
    day_review_kb, settings_kb
)
from states import FocusStates

router = Router()
logger = logging.getLogger(__name__)

# {user_id: {message_id, chat_id, session_id, end_time, duration, task_text, paused, pause_remaining}}
active_sessions = {}
active_breaks = {}  # {user_id: asyncio.Task}


# ─── HELPERS ───────────────────────────────────────────────────────────────────

def _name(user) -> str:
    return user["user_name"] or user["username"] or "друг"

def _mentor(user) -> str:
    return user["mentor_name"] or "Наставник"


# ─── ONBOARDING ────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user:
        await create_user(message.from_user.id, message.from_user.username or "")
        await message.answer(
            "👋 <b>Привет! Я твой личный наставник по продуктивности.</b>\n\n"
            "Как мне тебя называть?",
            parse_mode="HTML"
        )
        await state.set_state(FocusStates.entering_user_name)
    else:
        name = _name(user)
        await message.answer(
            f"👋 Рад видеть тебя снова, <b>{name}</b>!",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )


@router.message(FocusStates.entering_user_name)
async def handle_user_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await update_user(message.from_user.id, user_name=name)
    await message.answer(
        f"Отлично, <b>{name}</b>! 💪\n\n"
        "Теперь напиши свою главную цель.\n"
        "Это то, к чему ты стремишься в этот период жизни.\n\n"
        "<i>Например: «Запустить свой продукт», «Выучить английский до B2»</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.setting_goal)


@router.message(FocusStates.setting_goal)
async def handle_goal_input(message: Message, state: FSMContext):
    goal = message.text.strip()
    await update_user(message.from_user.id, main_goal=goal)
    user = await get_user(message.from_user.id)
    name = _name(user)
    await state.clear()
    await message.answer(
        f"🎯 <b>Записал.</b>\n\n"
        f"<i>{goal}</i>\n\n"
        f"Каждое утро я буду напоминать тебе об этом, {name}.\n"
        f"Теперь иди и сделай это — остальное подождёт.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


# ─── MAIN MENU ─────────────────────────────────────────────────────────────────

@router.message(F.text == "🚀 Начать фокус")
async def handle_start_focus(message: Message, state: FSMContext):
    if message.from_user.id in active_sessions:
        await message.answer("⏳ Сейчас идёт сессия фокуса. Сначала заверши её.")
        return
    user = await get_user(message.from_user.id)
    name = _name(user)
    await message.answer(
        f"⚡ <b>Телефон в сторону, {name}.</b>\n\nМир подождёт. Выбери длительность:",
        reply_markup=timer_choice_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Прогресс")
async def handle_progress(message: Message):
    stats = await get_week_stats(message.from_user.id)
    user = await get_user(message.from_user.id)
    xp = user["xp"] if user else 0
    streak = user["streak"] if user else 0
    name = _name(user)

    hours = stats["focus_minutes"] // 60
    mins = stats["focus_minutes"] % 60

    if stats["total"] > 0 and stats["completed"] >= stats["total"] * 0.8:
        verdict = "🏆 Отличная неделя. Так держать."
    elif stats["completed"] > 0:
        verdict = "💪 Есть прогресс. Не останавливайся."
    else:
        verdict = "📌 Неделя только началась. Первый шаг самый важный."

    await message.answer(
        f"📊 <b>{name}, вот твои цифры за 7 дней:</b>\n\n"
        f"✅ Задач выполнено: <b>{stats['completed']}</b> из {stats['total']}\n"
        f"⏱ В фокусе: <b>{hours}ч {mins}мин</b>\n"
        f"🔥 Серия: <b>{streak} дней</b> подряд\n"
        f"⭐ XP: <b>{xp}</b>\n\n"
        f"{verdict}",
        parse_mode="HTML"
    )


@router.message(F.text == "🎯 Моя цель")
async def handle_my_goal(message: Message):
    user = await get_user(message.from_user.id)
    weekly = await get_current_weekly_goal(message.from_user.id)

    goal = user["main_goal"] if user else "не задана"
    week_goal = weekly["goal"] if weekly else "не задана"
    prog = weekly["progress_percent"] if weekly else 0
    bar = "█" * (prog // 10) + "░" * (10 - prog // 10)

    await message.answer(
        f"🎯 <b>Твои цели</b>\n\n"
        f"🏔 Главная:\n<i>{goal}</i>\n\n"
        f"📅 Цель недели:\n<i>{week_goal}</i>\n"
        f"[{bar}] {prog}%",
        reply_markup=goal_kb(),
        parse_mode="HTML"
    )


@router.message(F.text == "📝 Итог дня")
async def handle_day_review(message: Message, state: FSMContext):
    task = await get_today_task(message.from_user.id)
    user = await get_user(message.from_user.id)
    name = _name(user)

    if not task:
        await message.answer(
            f"📝 <b>{name}, задача на сегодня не поставлена.</b>\n\n"
            "Что хочешь сделать сегодня?",
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
        reply_markup=day_review_kb(completed),
        parse_mode="HTML"
    )


@router.message(F.text == "⚙️ Настройки")
async def handle_settings(message: Message):
    user = await get_user(message.from_user.id)
    name = _name(user)
    mentor = _mentor(user)
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"👤 Твоё имя: <b>{name}</b>\n"
        f"🤖 Имя наставника: <b>{mentor}</b>\n"
        f"🌅 Утро: <b>{user['morning_time']}</b>\n"
        f"🌙 Вечер: <b>{user['evening_time']}</b>",
        reply_markup=settings_kb(),
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


@router.callback_query(F.data == "morning_change_task")
async def cb_morning_change_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("✏️ Напиши новую задачу дня:")
    await state.set_state(FocusStates.editing_task)


@router.callback_query(F.data.startswith("energy_"))
async def cb_energy(callback: CallbackQuery, state: FSMContext):
    level_map = {"energy_low": "🔋 Низкий", "energy_medium": "⚡ Средний", "energy_high": "🔥 Высокий"}
    level = level_map.get(callback.data, "⚡ Средний")
    await state.update_data(energy_level=callback.data.replace("energy_", ""))
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        f"Энергия: {level}\n\n"
        "✍️ <b>Напиши главную задачу дня</b>\n"
        "<i>Одна задача, выполнив которую ты будешь доволен этим днём</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.entering_task)


@router.callback_query(F.data == "morning_skip")
async def cb_morning_skip(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "Хорошо. Без чёткой задачи день уходит в никуда — помни об этом 💨"
    )


@router.message(FocusStates.entering_task)
async def handle_task_input(message: Message, state: FSMContext):
    data = await state.get_data()
    energy = data.get("energy_level", "medium")
    await create_task(message.from_user.id, message.text.strip(), energy)
    await state.clear()
    await message.answer(
        f"📌 <b>Записал.</b>\n\n"
        f"<i>{message.text.strip()}</i>\n\n"
        "Теперь иди и сделай это — остальное подождёт.",
        parse_mode="HTML"
    )


@router.message(FocusStates.editing_task)
async def handle_task_edit(message: Message, state: FSMContext):
    await update_today_task(message.from_user.id, message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ <b>Задача обновлена:</b>\n\n<i>{message.text.strip()}</i>",
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
    await start_focus(callback.message, callback.from_user.id, duration)


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
    await start_focus(message, message.from_user.id, duration)


async def start_focus(message: Message, user_id: int, duration: int):
    session_id = await start_focus_session(user_id, duration)
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
        "duration": duration,
        "task_text": task_text,
        "paused": False,
        "pause_remaining": None,
    }

    asyncio.create_task(_run_timer(message.bot, user_id))


def _format_timer(remaining_min: int, total_min: int, task_text: str, paused: bool = False) -> str:
    filled = int((1 - remaining_min / total_min) * 10)
    bar = "█" * filled + "░" * (10 - filled)
    h = remaining_min // 60
    m = remaining_min % 60
    time_str = f"{h}ч {m}мин" if h > 0 else f"{m} мин"
    status = "⏸ <b>ПАУЗА</b>" if paused else "<i>Убери телефон. Работай.</i>"
    return (
        f"🎯 <b>Режим глубокой работы</b>\n\n"
        f"📌 {task_text}\n\n"
        f"⏳ Осталось: <b>{time_str}</b>\n"
        f"[{bar}]\n\n"
        f"{status}"
    )


async def _run_timer(bot: Bot, user_id: int):
    session = active_sessions.get(user_id)
    if not session:
        return

    duration = session["duration"]
    remaining = duration
    warned_5min = False

    while remaining > 0:
        await asyncio.sleep(60)
        session = active_sessions.get(user_id)
        if not session:
            return

        if session["paused"]:
            continue  # на паузе — ждём, не уменьшаем

        remaining -= 1

        # Предупреждение за 5 минут
        if remaining == 5 and not warned_5min:
            warned_5min = True
            try:
                await bot.send_message(
                    chat_id=session["chat_id"],
                    text="⚡ <b>Осталось 5 минут — финишная прямая!</b>\nНе останавливайся.",
                    parse_mode="HTML"
                )
            except Exception:
                pass

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

    # Таймер завершён
    session = active_sessions.pop(user_id, None)
    if session:
        await end_focus_session(session["session_id"], completed=True)
        stats = await get_week_stats(user_id)

        try:
            await bot.edit_message_reply_markup(
                chat_id=session["chat_id"],
                message_id=session["message_id"],
                reply_markup=None
            )
        except Exception:
            pass

        try:
            await bot.send_message(
                chat_id=session["chat_id"],
                text=f"🔔 <b>Сессия завершена!</b>\n\n"
                     f"Ты только что сделал то, что большинство откладывает на завтра.\n\n"
                     f"⏱ Сегодня: {stats['today_sessions']} сессий · {stats['today_minutes']} мин\n\n"
                     f"Сделай перерыв 5-10 минут.",
                reply_markup=after_session_kb(),
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data == "focus_pause")
async def cb_focus_pause(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.get(user_id)
    if not session:
        await callback.answer("Сессия не найдена")
        return
    session["paused"] = True
    try:
        await callback.message.edit_text(
            _format_timer(
                active_sessions[user_id].get("pause_remaining") or session["duration"],
                session["duration"],
                session["task_text"],
                paused=True
            ),
            reply_markup=focus_paused_kb(),
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer("Пауза")


@router.callback_query(F.data == "focus_resume")
async def cb_focus_resume(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.get(user_id)
    if not session:
        await callback.answer("Сессия не найдена")
        return
    session["paused"] = False
    try:
        await callback.message.edit_reply_markup(reply_markup=focus_active_kb())
    except Exception:
        pass
    await callback.answer("Продолжаем!")


@router.callback_query(F.data == "focus_done")
async def cb_focus_done(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.pop(user_id, None)
    if not session:
        await callback.answer("Сессия не найдена")
        return
    await end_focus_session(session["session_id"], completed=True)
    stats = await get_week_stats(user_id)
    await callback.message.edit_text(
        f"✅ <b>Готово.</b>\n\n"
        f"Сегодня: {stats['today_sessions']} сессий · {stats['today_minutes']} мин\n\n"
        f"Сделай перерыв.",
        reply_markup=after_session_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "focus_quit")
async def cb_focus_quit(callback: CallbackQuery):
    user_id = callback.from_user.id
    session = active_sessions.pop(user_id, None)
    if not session:
        await callback.answer("Сессия не найдена")
        return
    await end_focus_session(session["session_id"], completed=False)
    await callback.message.edit_text(
        "Окей. Но ты знаешь что мог дотерпеть.\n\n"
        "Попробуй снова. Даже 10 минут лучше нуля.",
        reply_markup=after_session_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "after_another")
async def cb_after_another(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "⚡ Выбери длительность следующей сессии:",
        reply_markup=timer_choice_kb()
    )


@router.callback_query(F.data == "after_review")
async def cb_after_review(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    task = await get_today_task(callback.from_user.id)
    if not task:
        await callback.message.answer("📝 Задача на сегодня не поставлена.")
        return
    task_text = task["main_task"] or "не указана"
    completed = task["completed"]
    status = "✅ Выполнена" if completed else "⏳ Ещё не завершена"
    await callback.message.answer(
        f"📝 <b>Итог дня</b>\n\nЗадача: <i>{task_text}</i>\nСтатус: {status}",
        reply_markup=day_review_kb(completed),
        parse_mode="HTML"
    )


# ─── QUICK FOCUS FROM REVIEW ───────────────────────────────────────────────────

@router.callback_query(F.data == "quick_focus")
async def cb_quick_focus(callback: CallbackQuery):
    if callback.from_user.id in active_sessions:
        await callback.answer("Сессия уже идёт!")
        return
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "⚡ Выбери длительность:",
        reply_markup=timer_choice_kb()
    )


@router.callback_query(F.data == "task_edit")
async def cb_task_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("✏️ Напиши новую задачу дня:")
    await state.set_state(FocusStates.editing_task)



@router.callback_query(F.data == "task_new")
async def cb_task_new(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "➕ <b>Добавь ещё одну задачу на сегодня:</b>\n\n"
        "<i>Напиши задачу и она появится в списке дня</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.entering_task)



# ─── BREAK TIMER ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "break_start")
async def cb_break_start(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "☕ <b>Перерыв — это часть работы.</b>\n\nСколько минут отдыхаем?",
        reply_markup=break_choice_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.in_({"break_5", "break_10", "break_15", "break_20", "break_custom"}))
async def cb_break_select(callback: CallbackQuery, state: FSMContext):
    if callback.data == "break_custom":
        await callback.message.edit_reply_markup()
        await callback.message.answer("✏️ Введи время перерыва в минутах (от 1 до 60):")
        await state.set_state(FocusStates.custom_break)
        return
    minutes = int(callback.data.replace("break_", ""))
    await callback.message.edit_reply_markup()
    await _start_break(callback.message, callback.from_user.id, minutes)


@router.message(FocusStates.custom_break)
async def handle_custom_break(message: Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        if not (1 <= minutes <= 60):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введи число от 1 до 60")
        return
    await state.clear()
    await _start_break(message, message.from_user.id, minutes)


async def _start_break(message: Message, user_id: int, minutes: int):
    msg = await message.answer(
        f"☕ <b>Перерыв: {minutes} мин</b>\n\n"
        f"[{'░' * 10}]\n\n"
        f"<i>Встань, подвигайся, выпей воды.</i>",
        parse_mode="HTML"
    )
    task = asyncio.create_task(_run_break(message.bot, user_id, msg.message_id, message.chat.id, minutes))
    active_breaks[user_id] = task


async def _run_break(bot: Bot, user_id: int, message_id: int, chat_id: int, total: int):
    for elapsed in range(1, total + 1):
        await asyncio.sleep(60)
        remaining = total - elapsed
        filled = int((elapsed / total) * 10)
        bar = "█" * filled + "░" * (10 - filled)

        if remaining == 0:
            break

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"☕ <b>Перерыв: осталось {remaining} мин</b>\n\n"
                     f"[{bar}]\n\n"
                     f"<i>Встань, подвигайся, выпей воды.</i>",
                parse_mode="HTML"
            )
        except Exception:
            pass

    active_breaks.pop(user_id, None)

    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=chat_id,
            text="🔔 <b>Перерыв закончен!</b>\n\nВремя снова в строй. Выбери следующую сессию:",
            reply_markup=timer_choice_kb(),
            parse_mode="HTML"
        )
    except Exception:
        pass

# ─── EVENING AUDIT ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "evening_yes")
async def cb_evening_yes(callback: CallbackQuery):
    await complete_task(callback.from_user.id)
    streak, xp_gain = await add_xp_and_streak(callback.from_user.id)
    user = await get_user(callback.from_user.id)
    name = _name(user)

    if streak >= 10:
        streak_msg = f"🏆 {streak} дней подряд. Легенда."
    elif streak > 1:
        streak_msg = f"🔥 Серия: {streak} дней подряд!"
    else:
        streak_msg = "🔥 Начало серии!"

    await callback.message.edit_text(
        f"<b>Слово сдержал, {name}.</b>\n\n"
        f"Так и строятся результаты.\n\n"
        f"⭐ +{xp_gain} XP · {streak_msg}\n"
        f"💫 Всего XP: {user['xp']}",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "evening_no")
async def cb_evening_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💭 <b>Что помешало выполнить задачу?</b>\n\n"
        "<i>Это не наказание — это рефлексия.\n"
        "Понять причину = не повторить завтра.</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.reflection_prevented)


@router.message(FocusStates.reflection_prevented)
async def handle_reflection_prevented(message: Message, state: FSMContext):
    await state.update_data(what_prevented=message.text.strip())
    await message.answer("💡 <b>Что сделаешь иначе завтра?</b>", parse_mode="HTML")
    await state.set_state(FocusStates.reflection_change)


@router.message(FocusStates.reflection_change)
async def handle_reflection_change(message: Message, state: FSMContext):
    data = await state.get_data()
    await save_reflection(message.from_user.id, data.get("what_prevented", ""), message.text.strip())
    await update_user(message.from_user.id, streak=0)
    await state.clear()
    await message.answer(
        "📝 <b>Записал.</b>\n\n"
        "Бывает. Важно не то что упал — важно что анализируешь почему.\n\n"
        "Завтра новый день. Новая задача. Новый шанс.",
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
        f"✅ <b>Цель обновлена.</b>\n\n<i>{message.text.strip()}</i>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "goal_week_set")
async def cb_goal_week_set(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("📅 Напиши цель на эту неделю:")
    await state.set_state(FocusStates.entering_weekly_goal)


@router.message(FocusStates.entering_weekly_goal)
async def handle_weekly_goal(message: Message, state: FSMContext):
    await save_weekly_goal(message.from_user.id, message.text.strip())
    await state.clear()
    await message.answer(
        f"🎯 <b>Цель недели:</b>\n<i>{message.text.strip()}</i>\n\n"
        "Каждый день маленький шаг вперёд.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "goal_progress")
async def cb_goal_progress(callback: CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "📈 На сколько % продвинулся к цели недели?",
        reply_markup=progress_percent_kb()
    )


@router.callback_query(F.data.startswith("prog_"))
async def cb_progress_update(callback: CallbackQuery):
    percent = int(callback.data.replace("prog_", ""))
    await update_weekly_progress(callback.from_user.id, percent)
    bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
    await callback.message.edit_text(
        f"📈 <b>Прогресс: {percent}%</b>\n\n[{bar}]",
        parse_mode="HTML"
    )


# ─── SETTINGS ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "settings_user_name")
async def cb_settings_user_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("👤 Как мне тебя называть? Введи новое имя:")
    await state.set_state(FocusStates.changing_user_name)


@router.message(FocusStates.changing_user_name)
async def handle_change_user_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await update_user(message.from_user.id, user_name=name)
    await state.clear()
    await message.answer(f"✅ Буду называть тебя <b>{name}</b>!", parse_mode="HTML")


@router.callback_query(F.data == "settings_mentor_name")
async def cb_settings_mentor_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer(
        "🤖 Как назовём наставника?\n\n"
        "<i>Например: Коуч, Ментор, Сенсей, Владимир Иванович...</i>",
        parse_mode="HTML"
    )
    await state.set_state(FocusStates.changing_mentor_name)


@router.message(FocusStates.changing_mentor_name)
async def handle_change_mentor_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await update_user(message.from_user.id, mentor_name=name)
    await state.clear()
    await message.answer(
        f"✅ Теперь твой наставник — <b>{name}</b>!",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "settings_morning")
async def cb_settings_morning(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("🌅 Введи время утреннего уведомления (HH:MM)\nНапример: 07:30")
    await state.set_state(FocusStates.admin_set_morning)


@router.callback_query(F.data == "settings_evening")
async def cb_settings_evening(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("🌙 Введи время вечернего уведомления (HH:MM)\nНапример: 21:00")
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
    await message.answer(f"✅ Утреннее уведомление: <b>{time_str}</b>", parse_mode="HTML")


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
    await message.answer(f"✅ Вечернее уведомление: <b>{time_str}</b>", parse_mode="HTML")
