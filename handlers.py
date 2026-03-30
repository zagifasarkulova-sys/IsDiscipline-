from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from datetime import datetime, timedelta

from states import AddTask, EditTask, FocusSession
from keyboards import (
    main_menu, tasks_menu, remind_choice_kb,
    remind_day_kb, remind_time_kb,
    task_list_kb, task_actions_kb, confirm_delete_kb,
    focus_task_list_kb, focus_running_kb, focus_paused_kb, focus_finish_kb
)
import database as db

router = Router()


# ─── /start ──────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, pool, state: FSMContext):
    await state.clear()
    await db.ensure_user(pool, message.from_user.id, message.from_user.username or "")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\nВыбери действие:",
        reply_markup=main_menu()
    )


# ─── Главное меню ─────────────────────────────────────────

@router.message(F.text == "◀️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu())


# ════════════════════════════════════════════════════════
#  ЗАДАЧИ
# ════════════════════════════════════════════════════════

@router.message(F.text == "📋 Задачи")
async def tasks_section(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📋 Задачи:", reply_markup=tasks_menu())


# ─── Добавить задачу ─────────────────────────────────────

@router.message(F.text == "➕ Добавить задачу")
async def add_task_start(message: Message, state: FSMContext):
    await state.set_state(AddTask.waiting_title)
    await message.answer("✏️ Введи название задачи:")


@router.message(AddTask.waiting_title)
async def add_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTask.waiting_remind_choice)
    await message.answer(
        f"Задача: <b>{message.text.strip()}</b>\n\nУстановить напоминание?",
        reply_markup=remind_choice_kb(),
        parse_mode="HTML"
    )


# ─── Без напоминания (AddTask) ───────────────────────────

@router.callback_query(AddTask.waiting_remind_choice, F.data == "remind_no")
async def add_task_no_remind(callback: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    await db.add_task(pool, callback.from_user.id, data["title"])
    await state.clear()
    await callback.message.edit_text(
        f"✅ Задача добавлена: <b>{data['title']}</b>",
        parse_mode="HTML"
    )
    await callback.message.answer("📋 Задачи:", reply_markup=tasks_menu())
    await callback.answer()


# ─── Установить напоминание (AddTask) ────────────────────

@router.callback_query(AddTask.waiting_remind_choice, F.data == "remind_yes")
async def add_task_remind_yes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddTask.waiting_remind_date)
    await callback.message.edit_text(
        "📅 Выбери день напоминания:",
        reply_markup=remind_day_kb()
    )
    await callback.answer()


@router.callback_query(AddTask.waiting_remind_date, F.data.startswith("day:"))
async def add_task_remind_day(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split(":")[1])
    remind_date = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
    await state.update_data(remind_date=remind_date)
    await state.set_state(AddTask.waiting_remind_time)
    await callback.message.edit_text(
        f"📅 Дата: <b>{remind_date}</b>\n\n⏰ Выбери время:",
        parse_mode="HTML",
        reply_markup=remind_time_kb()
    )
    await callback.answer()


@router.callback_query(AddTask.waiting_remind_time, F.data.startswith("time:"))
async def add_task_remind_time(callback: CallbackQuery, state: FSMContext, pool):
    time_str = callback.data[5:]  # убираем "time:"
    data = await state.get_data()
    remind_at = datetime.strptime(f"{data['remind_date']} {time_str}", "%d.%m.%Y %H:%M")
    await db.add_task(pool, callback.from_user.id, data["title"], remind_at)
    await state.clear()
    await callback.message.edit_text(
        f"✅ Задача добавлена: <b>{data['title']}</b>\n"
        f"⏰ Напоминание: {remind_at.strftime('%d.%m.%Y %H:%M')}",
        parse_mode="HTML"
    )
    await callback.message.answer("📋 Задачи:", reply_markup=tasks_menu())
    await callback.answer()


# ─── Мои задачи ──────────────────────────────────────────

@router.message(F.text == "📝 Мои задачи")
async def my_tasks(message: Message, pool):
    tasks = await db.get_tasks(pool, message.from_user.id)
    if not tasks:
        await message.answer("У тебя пока нет задач. Добавь первую!")
        return
    await message.answer("📝 Твои задачи:", reply_markup=task_list_kb(tasks))


@router.callback_query(F.data == "tasks_back_list")
async def tasks_back_list(callback: CallbackQuery, pool):
    tasks = await db.get_tasks(pool, callback.from_user.id)
    if not tasks:
        await callback.message.edit_text("У тебя пока нет задач.")
        return
    await callback.message.edit_text("📝 Твои задачи:", reply_markup=task_list_kb(tasks))


@router.callback_query(F.data == "tasks_back")
async def tasks_back(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(F.data.startswith("task_view:"))
async def task_view(callback: CallbackQuery, pool):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(pool, task_id)
    if not task:
        await callback.answer("Задача не найдена")
        return
    status = "✅ Выполнена" if task["is_done"] else "⬜️ Не выполнена"
    remind = task["remind_at"].strftime("%d.%m.%Y %H:%M") if task["remind_at"] else "нет"
    text = (
        f"<b>{task['title']}</b>\n\n"
        f"Статус: {status}\n"
        f"Напоминание: {remind}"
    )
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=task_actions_kb(task_id, task["is_done"])
    )


# ─── Изменить название ────────────────────────────────────

@router.callback_query(F.data.startswith("task_edit_title:"))
async def task_edit_title_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.set_state(EditTask.waiting_new_title)
    await state.update_data(task_id=task_id)
    await callback.message.edit_text("✏️ Введи новое название задачи:")


@router.message(EditTask.waiting_new_title)
async def task_edit_title_done(message: Message, state: FSMContext, pool):
    data = await state.get_data()
    await db.update_task_title(pool, data["task_id"], message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ Название изменено: <b>{message.text.strip()}</b>",
        parse_mode="HTML",
        reply_markup=tasks_menu()
    )


# ─── Изменить напоминание (EditTask) ─────────────────────

@router.callback_query(F.data.startswith("task_edit_remind:"))
async def task_edit_remind_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.set_state(EditTask.waiting_remind_choice)
    await state.update_data(task_id=task_id)
    await callback.message.edit_text(
        "Изменить напоминание:",
        reply_markup=remind_choice_kb()
    )


@router.callback_query(EditTask.waiting_remind_choice, F.data == "remind_no")
async def edit_remind_remove(callback: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    await db.update_task_remind(pool, data["task_id"], None)
    await state.clear()
    await callback.message.edit_text("✅ Напоминание убрано.")
    await callback.message.answer("📋 Задачи:", reply_markup=tasks_menu())
    await callback.answer()


@router.callback_query(EditTask.waiting_remind_choice, F.data == "remind_yes")
async def edit_remind_yes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditTask.waiting_remind_date)
    await callback.message.edit_text(
        "📅 Выбери день напоминания:",
        reply_markup=remind_day_kb()
    )
    await callback.answer()


@router.callback_query(EditTask.waiting_remind_date, F.data.startswith("day:"))
async def edit_remind_day(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split(":")[1])
    remind_date = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
    await state.update_data(remind_date=remind_date)
    await state.set_state(EditTask.waiting_remind_time)
    await callback.message.edit_text(
        f"📅 Дата: <b>{remind_date}</b>\n\n⏰ Выбери время:",
        parse_mode="HTML",
        reply_markup=remind_time_kb()
    )
    await callback.answer()


@router.callback_query(EditTask.waiting_remind_time, F.data.startswith("time:"))
async def edit_remind_time(callback: CallbackQuery, state: FSMContext, pool):
    time_str = callback.data[5:]
    data = await state.get_data()
    remind_at = datetime.strptime(f"{data['remind_date']} {time_str}", "%d.%m.%Y %H:%M")
    await db.update_task_remind(pool, data["task_id"], remind_at)
    await state.clear()
    await callback.message.edit_text(
        f"✅ Напоминание установлено: <b>{remind_at.strftime('%d.%m.%Y %H:%M')}</b>",
        parse_mode="HTML"
    )
    await callback.message.answer("📋 Задачи:", reply_markup=tasks_menu())
    await callback.answer()


# ─── Отметить выполнено ───────────────────────────────────

@router.callback_query(F.data.startswith("task_toggle_done:"))
async def task_toggle_done(callback: CallbackQuery, pool):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(pool, task_id)
    await db.mark_task_done(pool, task_id, not task["is_done"])
    task = await db.get_task(pool, task_id)
    status = "✅ Выполнена" if task["is_done"] else "⬜️ Не выполнена"
    remind = task["remind_at"].strftime("%d.%m.%Y %H:%M") if task["remind_at"] else "нет"
    text = f"<b>{task['title']}</b>\n\nСтатус: {status}\nНапоминание: {remind}"
    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=task_actions_kb(task_id, task["is_done"])
    )


# ─── Удалить задачу ───────────────────────────────────────

@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_confirm(callback: CallbackQuery, pool):
    task_id = int(callback.data.split(":")[1])
    task = await db.get_task(pool, task_id)
    await callback.message.edit_text(
        f"🗑 Удалить задачу <b>{task['title']}</b>?",
        parse_mode="HTML",
        reply_markup=confirm_delete_kb(task_id)
    )


@router.callback_query(F.data.startswith("task_confirm_delete:"))
async def task_delete_done(callback: CallbackQuery, pool):
    task_id = int(callback.data.split(":")[1])
    await db.delete_task(pool, task_id)
    tasks = await db.get_tasks(pool, callback.from_user.id)
    if tasks:
        await callback.message.edit_text("✅ Задача удалена.\n\n📝 Твои задачи:", reply_markup=task_list_kb(tasks))
    else:
        await callback.message.edit_text("✅ Задача удалена. Задач больше нет.")


# ════════════════════════════════════════════════════════
#  ФОКУС
# ════════════════════════════════════════════════════════

@router.message(F.text == "🚀 Начать фокус")
async def focus_start_menu(message: Message, state: FSMContext, pool):
    session = await db.get_active_session(pool, message.from_user.id)
    if session:
        task = await db.get_task(pool, session["task_id"]) if session["task_id"] else None
        task_name = task["title"] if task else "без задачи"
        is_paused = session["paused_at"] is not None
        kb = focus_paused_kb() if is_paused else focus_running_kb()
        status = "⏸ На паузе" if is_paused else "▶️ Идёт"
        await message.answer(
            f"У тебя уже есть активная сессия!\n"
            f"Задача: <b>{task_name}</b>\n"
            f"Статус: {status}",
            parse_mode="HTML",
            reply_markup=kb
        )
        await state.update_data(session_id=session["id"], task_id=session["task_id"])
        await state.set_state(FocusSession.in_progress)
        return

    tasks = await db.get_tasks(pool, message.from_user.id)
    await state.set_state(FocusSession.choosing_task)
    await message.answer(
        "🎯 Выбери задачу для фокус-сессии:",
        reply_markup=focus_task_list_kb(tasks)
    )


@router.callback_query(FocusSession.choosing_task, F.data.startswith("focus_start:"))
async def focus_begin(callback: CallbackQuery, state: FSMContext, pool):
    task_id_raw = callback.data.split(":")[1]
    task_id = int(task_id_raw) if task_id_raw != "0" else None

    session_id = await db.start_focus(pool, callback.from_user.id, task_id)
    await state.update_data(session_id=session_id, task_id=task_id, pause_started=None)
    await state.set_state(FocusSession.in_progress)

    task_name = "без задачи"
    if task_id:
        task = await db.get_task(pool, task_id)
        if task:
            task_name = task["title"]

    await callback.message.edit_text(
        f"🚀 Фокус-сессия запущена!\n\n"
        f"Задача: <b>{task_name}</b>\n\n"
        f"Концентрируйся. Удачи! 💪",
        parse_mode="HTML",
        reply_markup=focus_running_kb()
    )


@router.callback_query(FocusSession.choosing_task, F.data == "focus_cancel")
async def focus_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(FocusSession.in_progress, F.data == "focus_pause")
async def focus_pause(callback: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    await db.pause_focus(pool, data["session_id"])
    await state.update_data(pause_started=datetime.now().isoformat())
    await callback.message.edit_text(
        "⏸ Сессия на паузе.\n\nВернись когда будешь готов!",
        reply_markup=focus_paused_kb()
    )


@router.callback_query(FocusSession.in_progress, F.data == "focus_resume")
async def focus_resume(callback: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    pause_started = data.get("pause_started")
    extra = 0
    if pause_started:
        paused_dt = datetime.fromisoformat(pause_started)
        extra = int((datetime.now() - paused_dt).total_seconds())
    await db.resume_focus(pool, data["session_id"], extra)
    await state.update_data(pause_started=None)
    await callback.message.edit_text(
        "▶️ Сессия продолжается!\n\nФокусируйся 💪",
        reply_markup=focus_running_kb()
    )


@router.callback_query(FocusSession.in_progress, F.data == "focus_finish")
async def focus_finish(callback: CallbackQuery, state: FSMContext, pool):
    data = await state.get_data()
    session_id = data["session_id"]
    task_id = data.get("task_id")
    pause_started = data.get("pause_started")

    extra = 0
    if pause_started:
        paused_dt = datetime.fromisoformat(pause_started)
        extra = int((datetime.now() - paused_dt).total_seconds())

    await db.finish_focus(pool, session_id, extra)

    async with pool.acquire() as conn:
        session = await conn.fetchrow("SELECT total_seconds FROM focus_sessions WHERE id = $1", session_id)
    total = session["total_seconds"] if session else 0
    minutes = total // 60
    seconds = total % 60

    await state.clear()

    finish_kb = focus_finish_kb(task_id) if task_id else None
    text = f"🏁 Сессия завершена!\n\n⏱ Время: <b>{minutes} мин {seconds} сек</b>\n\n"
    if task_id:
        task = await db.get_task(pool, task_id)
        if task:
            text += f"Задача: <b>{task['title']}</b>\n\nОтметить задачу?"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=finish_kb)
    if not finish_kb:
        await callback.message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("focus_done_task:"))
async def focus_done_task(callback: CallbackQuery, pool):
    task_id = int(callback.data.split(":")[1])
    await db.mark_task_done(pool, task_id, True)
    await callback.message.edit_text("✅ Отлично! Задача отмечена выполненной.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data == "focus_not_done")
async def focus_not_done(callback: CallbackQuery):
    await callback.message.edit_text("Окей, задача осталась в списке.")
    await callback.message.answer("Главное меню:", reply_markup=main_menu())
