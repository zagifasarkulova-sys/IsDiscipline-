from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать фокус"), KeyboardButton(text="📋 Задачи")]
        ],
        resize_keyboard=True
    )


def tasks_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить задачу")],
            [KeyboardButton(text="📝 Мои задачи")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )


def remind_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Установить напоминание", callback_data="remind_yes")],
        [InlineKeyboardButton(text="⏭ Без напоминания", callback_data="remind_no")]
    ])


def remind_day_kb():
    """Выбор дня + пропустить"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="day:0"),
            InlineKeyboardButton(text="📅 Завтра", callback_data="day:1"),
        ],
        [
            InlineKeyboardButton(text="📅 Через 2 дня", callback_data="day:2"),
            InlineKeyboardButton(text="📅 Через 3 дня", callback_data="day:3"),
        ],
        [
            InlineKeyboardButton(text="📅 Через неделю", callback_data="day:7"),
        ],
        [
            InlineKeyboardButton(text="⏭ Без даты (только время)", callback_data="day:skip"),
        ],
    ])


def remind_time_kb():
    """Кнопки времени 05:00–23:00 + своё время"""
    rows = []
    hours = list(range(5, 24))
    for i in range(0, len(hours), 3):
        row = []
        for h in hours[i:i+3]:
            label = f"{h:02d}:00"
            row.append(InlineKeyboardButton(text=label, callback_data=f"time:{label}"))
        rows.append(row)
    # Кнопка своего времени
    rows.append([InlineKeyboardButton(text="⌨️ Своё время (ЧЧ:ММ)", callback_data="custom_time")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_list_kb(tasks):
    buttons = []
    for task in tasks:
        status = "✅" if task["is_done"] else "⬜️"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {task['title']}",
                callback_data=f"task_view:{task['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="tasks_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_actions_kb(task_id: int, is_done: bool):
    done_text = "↩️ Снять выполнение" if is_done else "✅ Отметить выполненной"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data=f"task_edit_title:{task_id}")],
        [InlineKeyboardButton(text="⏰ Изменить напоминание", callback_data=f"task_edit_remind:{task_id}")],
        [InlineKeyboardButton(text=done_text, callback_data=f"task_toggle_done:{task_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"task_delete:{task_id}")],
        [InlineKeyboardButton(text="◀️ К списку", callback_data="tasks_back_list")]
    ])


def confirm_delete_kb(task_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"task_confirm_delete:{task_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"task_view:{task_id}")]
    ])


def focus_task_list_kb(tasks):
    buttons = []
    for task in tasks:
        buttons.append([
            InlineKeyboardButton(text=task["title"], callback_data=f"focus_start:{task['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="▶️ Без задачи", callback_data="focus_start:0")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="focus_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def focus_running_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏸ Пауза", callback_data="focus_pause")],
        [InlineKeyboardButton(text="🏁 Завершить", callback_data="focus_finish")]
    ])


def focus_paused_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить", callback_data="focus_resume")],
        [InlineKeyboardButton(text="🏁 Завершить", callback_data="focus_finish")]
    ])


def focus_finish_kb(task_id: int):
    if task_id and task_id != 0:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Задача выполнена", callback_data=f"focus_done_task:{task_id}")],
            [InlineKeyboardButton(text="⬜️ Не выполнена", callback_data="focus_not_done")]
        ])
    return None
