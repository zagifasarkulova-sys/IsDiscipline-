from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать фокус"), KeyboardButton(text="📊 Прогресс")],
            [KeyboardButton(text="🎯 Моя цель"), KeyboardButton(text="📝 Итог дня")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
        persistent=True
    )


def timer_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ 25 мин", callback_data="timer_25"),
            InlineKeyboardButton(text="🔥 50 мин", callback_data="timer_50"),
        ],
        [
            InlineKeyboardButton(text="💪 90 мин", callback_data="timer_90"),
            InlineKeyboardButton(text="✏️ Своё время", callback_data="timer_custom"),
        ],
    ])


def focus_active_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏸ Пауза", callback_data="focus_pause"),
            InlineKeyboardButton(text="✅ Завершил", callback_data="focus_done"),
            InlineKeyboardButton(text="❌ Сдался", callback_data="focus_quit"),
        ]
    ])


def focus_paused_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="▶️ Продолжить", callback_data="focus_resume"),
            InlineKeyboardButton(text="❌ Завершить", callback_data="focus_quit"),
        ]
    ])


def after_session_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕ Сделать перерыв", callback_data="break_start")],
        [
            InlineKeyboardButton(text="🔄 Ещё сессию", callback_data="after_another"),
            InlineKeyboardButton(text="📝 Итог дня", callback_data="after_review"),
        ]
    ])


def break_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5 мин", callback_data="break_5"),
            InlineKeyboardButton(text="10 мин", callback_data="break_10"),
            InlineKeyboardButton(text="15 мин", callback_data="break_15"),
            InlineKeyboardButton(text="20 мин", callback_data="break_20"),
        ],
        [InlineKeyboardButton(text="✏️ Своё время", callback_data="break_custom")],
    ])


def energy_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔋 Низкий", callback_data="energy_low"),
            InlineKeyboardButton(text="⚡ Средний", callback_data="energy_medium"),
            InlineKeyboardButton(text="🔥 Высокий", callback_data="energy_high"),
        ]
    ])


def morning_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✍️ Ввести задачу", callback_data="morning_enter"),
            InlineKeyboardButton(text="⏭ Пропустить", callback_data="morning_skip"),
        ]
    ])


def morning_has_task_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="morning_change_task")],
        [InlineKeyboardButton(text="✅ Всё верно, начинаю", callback_data="morning_skip")],
    ])


def evening_result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, выполнил 😎", callback_data="evening_yes"),
            InlineKeyboardButton(text="❌ Нет, провалил 😔", callback_data="evening_no"),
        ]
    ])


def goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить главную цель", callback_data="goal_edit")],
        [InlineKeyboardButton(text="🗓 Поставить цель недели", callback_data="goal_week_set")],
        [InlineKeyboardButton(text="📈 Обновить прогресс недели", callback_data="goal_progress")],
    ])


def progress_percent_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0%", callback_data="prog_0"),
            InlineKeyboardButton(text="25%", callback_data="prog_25"),
            InlineKeyboardButton(text="50%", callback_data="prog_50"),
        ],
        [
            InlineKeyboardButton(text="75%", callback_data="prog_75"),
            InlineKeyboardButton(text="100% 🎉", callback_data="prog_100"),
        ]
    ])


def day_review_kb(completed: bool) -> InlineKeyboardMarkup:
    buttons = []
    if not completed:
        buttons.append([
            InlineKeyboardButton(text="✅ Да, выполнил 😎", callback_data="evening_yes"),
            InlineKeyboardButton(text="❌ Нет, провалил 😔", callback_data="evening_no"),
        ])
    buttons.append([
        InlineKeyboardButton(text="✏️ Изменить задачу", callback_data="task_edit"),
        InlineKeyboardButton(text="➕ Новая задача", callback_data="task_new"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🚀 Начать сессию", callback_data="quick_focus"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Изменить моё имя", callback_data="settings_user_name")],
        [InlineKeyboardButton(text="🤖 Переименовать наставника", callback_data="settings_mentor_name")],
        [InlineKeyboardButton(text="🌅 Время утреннего уведомления", callback_data="settings_morning")],
        [InlineKeyboardButton(text="🌙 Время вечернего уведомления", callback_data="settings_evening")],
    ])
