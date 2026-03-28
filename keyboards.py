from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать фокус"), KeyboardButton(text="📊 Прогресс")],
            [KeyboardButton(text="🎯 Моя цель"), KeyboardButton(text="📝 Итог дня")],
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
            InlineKeyboardButton(text="✅ Завершил раньше", callback_data="focus_done"),
            InlineKeyboardButton(text="❌ Сдался", callback_data="focus_quit"),
        ]
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


def evening_result_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, выполнил 😎", callback_data="evening_yes"),
            InlineKeyboardButton(text="❌ Нет, провалил 😔", callback_data="evening_no"),
        ]
    ])


def goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить цель", callback_data="goal_edit")],
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


def skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")]
    ])


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌅 Изменить утреннее время", callback_data="admin_morning")],
        [InlineKeyboardButton(text="🌙 Изменить вечернее время", callback_data="admin_evening")],
    ])
