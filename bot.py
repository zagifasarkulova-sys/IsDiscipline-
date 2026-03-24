import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import (
    init_db, add_habit, get_habits, get_habit,
    delete_habit, mark_done, is_done_today,
    get_streak, get_total_completions, maybe_increase_goal
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")

# Состояния ConversationHandler
WAITING_HABIT_NAME, WAITING_HABIT_GOAL, WAITING_HABIT_INCREMENT, WAITING_HABIT_DAYS = range(4)

# Временное хранилище данных при создании привычки
user_data_temp = {}

# ───────────────────────── ГЛАВНОЕ МЕНЮ ─────────────────────────

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить привычку", callback_data="add_habit")],
        [InlineKeyboardButton("📋 Мои привычки", callback_data="list_habits")],
        [InlineKeyboardButton("✅ Отметить выполнение", callback_data="check_habits")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я твой *Трекер привычек*.\n\n"
        "Ставь цели, выполняй их каждый день и наблюдай как они растут 💪",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "📌 *Главное меню*",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# ───────────────────────── ДОБАВЛЕНИЕ ПРИВЫЧКИ ─────────────────────────

async def add_habit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_temp[query.from_user.id] = {}
    await query.message.edit_text(
        "✏️ *Новая привычка*\n\nНапиши название привычки:\n_(например: Отжимания, Бег, Чтение)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="menu")]])
    )
    return WAITING_HABIT_NAME

async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    name = update.message.text.strip()
    user_data_temp[uid]["name"] = name
    await update.message.reply_text(
        f"💪 Привычка: *{name}*\n\nНапиши начальную цель — сколько раз/минут в день?\n_(например: 10)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="menu")]])
    )
    return WAITING_HABIT_GOAL

async def received_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    try:
        goal = int(update.message.text.strip())
        if goal <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❗ Введи целое положительное число, например: *10*", parse_mode="Markdown")
        return WAITING_HABIT_GOAL
    user_data_temp[uid]["goal"] = goal
    await update.message.reply_text(
        f"📈 Цель: *{goal}*\n\nНа сколько увеличивать цель каждый раз?\n_(например: 2 — значит +2 каждые N дней)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="menu")]])
    )
    return WAITING_HABIT_INCREMENT

async def received_increment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    try:
        inc = int(update.message.text.strip())
        if inc <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❗ Введи целое положительное число, например: *2*", parse_mode="Markdown")
        return WAITING_HABIT_INCREMENT
    user_data_temp[uid]["increment"] = inc
    await update.message.reply_text(
        f"📅 Прирост: *+{inc}*\n\nКаждые сколько дней увеличивать цель?\n_(например: 10)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="menu")]])
    )
    return WAITING_HABIT_DAYS

async def received_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    try:
        days = int(update.message.text.strip())
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❗ Введи целое положительное число, например: *10*", parse_mode="Markdown")
        return WAITING_HABIT_DAYS

    d = user_data_temp.get(uid, {})
    name = d.get("name", "Привычка")
    goal = d.get("goal", 10)
    inc = d.get("increment", 2)

    add_habit(uid, name, goal, inc, days)
    user_data_temp.pop(uid, None)

    await update.message.reply_text(
        f"✅ Привычка *«{name}»* создана!\n\n"
        f"🎯 Начальная цель: *{goal}*\n"
        f"📈 Прирост: *+{inc}* каждые *{days}* дней",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    user_data_temp.pop(uid, None)
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text("❌ Отменено.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Отменено.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# ───────────────────────── СПИСОК ПРИВЫЧЕК ─────────────────────────

async def list_habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    habits = get_habits(uid)

    if not habits:
        await query.message.edit_text(
            "📋 У тебя пока нет привычек.\n\nДобавь первую!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить", callback_data="add_habit")],
                [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
            ])
        )
        return

    buttons = []
    for h in habits:
        done = "✅" if is_done_today(h["id"]) else "⬜"
        buttons.append([InlineKeyboardButton(
            f"{done} {h['name']} — цель: {h['current_goal']}",
            callback_data=f"habit_detail_{h['id']}"
        )])
    buttons.append([InlineKeyboardButton("🏠 Меню", callback_data="menu")])

    await query.message.edit_text(
        "📋 *Твои привычки:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ───────────────────────── ДЕТАЛИ ПРИВЫЧКИ ─────────────────────────

async def habit_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    habit_id = int(query.data.split("_")[-1])
    h = get_habit(habit_id)
    if not h:
        await query.message.edit_text("❗ Привычка не найдена.", reply_markup=main_menu_keyboard())
        return

    streak = get_streak(habit_id)
    total = get_total_completions(habit_id)
    done_today = is_done_today(habit_id)
    done_emoji = "✅ Выполнено сегодня" if done_today else "⬜ Не выполнено сегодня"

    next_increase = h["increment_every_days"] - (total % h["increment_every_days"])
    if total % h["increment_every_days"] == 0 and total > 0:
        next_increase = h["increment_every_days"]

    text = (
        f"📌 *{h['name']}*\n\n"
        f"🎯 Текущая цель: *{h['current_goal']}*\n"
        f"📈 Прирост: *+{h['increment']}* каждые *{h['increment_every_days']}* дней\n"
        f"🔥 Серия: *{streak} дней*\n"
        f"📊 Всего выполнений: *{total}*\n"
        f"⏳ До следующего прироста: *{next_increase} выполнений*\n\n"
        f"{done_emoji}"
    )

    buttons = []
    if not done_today:
        buttons.append([InlineKeyboardButton("✅ Отметить выполнение", callback_data=f"done_{habit_id}")])
    buttons.append([InlineKeyboardButton("🗑️ Удалить привычку", callback_data=f"confirm_delete_{habit_id}")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="list_habits")])

    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

# ───────────────────────── ОТМЕТИТЬ ВЫПОЛНЕНИЕ ─────────────────────────

async def check_habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    habits = get_habits(uid)

    if not habits:
        await query.message.edit_text(
            "📋 У тебя пока нет привычек.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить", callback_data="add_habit")],
                [InlineKeyboardButton("🏠 Меню", callback_data="menu")]
            ])
        )
        return

    buttons = []
    for h in habits:
        done = is_done_today(h["id"])
        emoji = "✅" if done else "⬜"
        label = f"{emoji} {h['name']} ({h['current_goal']})"
        cb = f"noop_{h['id']}" if done else f"done_{h['id']}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb)])
    buttons.append([InlineKeyboardButton("🏠 Меню", callback_data="menu")])

    await query.message.edit_text(
        "✅ *Отметь выполненные привычки:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    habit_id = int(query.data.split("_")[-1])
    success = mark_done(habit_id)
    h = get_habit(habit_id)

    if not success:
        await query.answer("Уже отмечено сегодня!", show_alert=True)
        return

    new_goal = maybe_increase_goal(habit_id)
    h = get_habit(habit_id)  # перечитываем после возможного обновления
    streak = get_streak(habit_id)

    msg = f"🔥 *{h['name']}* выполнено!\nСерия: *{streak} дней* подряд"
    if new_goal:
        msg += f"\n\n🎉 Цель выросла до *{new_goal}*! Ты становишься сильнее!"

    await query.answer(msg[:200], show_alert=True)

    # Обновляем список
    uid = query.from_user.id
    habits = get_habits(uid)
    buttons = []
    for hab in habits:
        done = is_done_today(hab["id"])
        emoji = "✅" if done else "⬜"
        label = f"{emoji} {hab['name']} ({hab['current_goal']})"
        cb = f"noop_{hab['id']}" if done else f"done_{hab['id']}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb)])
    buttons.append([InlineKeyboardButton("🏠 Меню", callback_data="menu")])

    await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Уже отмечено сегодня ✅", show_alert=False)

# ───────────────────────── СТАТИСТИКА ─────────────────────────

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    habits = get_habits(uid)

    if not habits:
        await query.message.edit_text(
            "📊 Нет привычек для статистики.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu")]])
        )
        return

    text = "📊 *Твоя статистика:*\n\n"
    for h in habits:
        streak = get_streak(h["id"])
        total = get_total_completions(h["id"])
        done = "✅" if is_done_today(h["id"]) else "⬜"
        text += (
            f"{done} *{h['name']}*\n"
            f"   🎯 Цель: {h['current_goal']} | 🔥 Серия: {streak} дн | 📊 Всего: {total}\n\n"
        )

    await query.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="menu")]])
    )

# ───────────────────────── УДАЛЕНИЕ ─────────────────────────

async def confirm_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    habit_id = int(query.data.split("_")[-1])
    h = get_habit(habit_id)
    if not h:
        await query.message.edit_text("❗ Привычка не найдена.", reply_markup=main_menu_keyboard())
        return

    await query.message.edit_text(
        f"🗑️ Удалить привычку *«{h['name']}»*?\n\nВсе данные будут потеряны.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"delete_{habit_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"habit_detail_{habit_id}")]
        ])
    )

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    habit_id = int(query.data.split("_")[-1])
    h = get_habit(habit_id)
    name = h["name"] if h else "Привычка"
    delete_habit(habit_id)

    await query.message.edit_text(
        f"🗑️ Привычка *«{name}»* удалена.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

# ───────────────────────── ЗАПУСК ─────────────────────────

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_habit_start, pattern="^add_habit$")],
        states={
            WAITING_HABIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)],
            WAITING_HABIT_GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_goal)],
            WAITING_HABIT_INCREMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_increment)],
            WAITING_HABIT_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_days)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_conv, pattern="^menu$"),
            CommandHandler("cancel", cancel_conv),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(list_habits_callback, pattern="^list_habits$"))
    app.add_handler(CallbackQueryHandler(habit_detail_callback, pattern="^habit_detail_\\d+$"))
    app.add_handler(CallbackQueryHandler(check_habits_callback, pattern="^check_habits$"))
    app.add_handler(CallbackQueryHandler(done_callback, pattern="^done_\\d+$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop_\\d+$"))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_callback, pattern="^confirm_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete_\\d+$"))

    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
