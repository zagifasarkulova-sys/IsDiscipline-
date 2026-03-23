import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from keep_alive import keep_alive
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📋 Мои задачи", callback_data="tasks"),
            InlineKeyboardButton("✅ Отметить выполнено", callback_data="done"),
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("❓ Помощь", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот для дисциплины и самоорганизации.\n"
        "Помогу тебе держать задачи под контролем!\n\n"
        "Выбери действие:",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "📖 *Команды бота:*\n\n"
        "/start — главное меню\n"
        "/add <задача> — добавить задачу\n"
        "/list — список задач\n"
        "/done <номер> — отметить задачу выполненной\n"
        "/clear — очистить все задачи\n"
        "/stats — статистика\n"
        "/help — эта справка\n\n"
        "💡 Просто напиши задачу, и я её запомню!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Укажи задачу: /add <текст задачи>\n\nНапример: /add Прочитать книгу"
        )
        return

    task_text = " ".join(context.args)
    if "tasks" not in context.user_data:
        context.user_data["tasks"] = []

    context.user_data["tasks"].append({"text": task_text, "done": False})
    task_num = len(context.user_data["tasks"])
    await update.message.reply_text(
        f"✅ Задача #{task_num} добавлена:\n*{task_text}*", parse_mode="Markdown"
    )


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = context.user_data.get("tasks", [])
    if not tasks:
        await update.message.reply_text(
            "📋 Задач нет. Добавь первую: /add <задача>"
        )
        return

    text = "📋 *Твои задачи:*\n\n"
    for i, task in enumerate(tasks, 1):
        status = "✅" if task["done"] else "⬜"
        text += f"{status} {i}. {task['text']}\n"

    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    text += f"\n📊 Выполнено: {done}/{total}"

    await update.message.reply_text(text, parse_mode="Markdown")


async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажи номер задачи: /done <номер>")
        return

    try:
        task_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Номер должен быть числом.")
        return

    tasks = context.user_data.get("tasks", [])
    if not tasks or task_num < 1 or task_num > len(tasks):
        await update.message.reply_text(
            f"Задачи #{task_num} не существует. Проверь список: /list"
        )
        return

    task = tasks[task_num - 1]
    if task["done"]:
        await update.message.reply_text(f"Задача #{task_num} уже выполнена! 🎉")
        return

    task["done"] = True
    await update.message.reply_text(
        f"🎉 Задача #{task_num} выполнена!\n*{task['text']}*", parse_mode="Markdown"
    )


async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["tasks"] = []
    await update.message.reply_text("🗑 Все задачи очищены.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = context.user_data.get("tasks", [])
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    pending = total - done

    if total == 0:
        await update.message.reply_text(
            "📊 Статистика пуста. Добавь задачи: /add <задача>"
        )
        return

    percent = int((done / total) * 100) if total > 0 else 0
    bar_filled = percent // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    text = (
        f"📊 *Статистика:*\n\n"
        f"Всего задач: {total}\n"
        f"✅ Выполнено: {done}\n"
        f"⬜ Осталось: {pending}\n\n"
        f"Прогресс: [{bar}] {percent}%"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "tasks":
        tasks = context.user_data.get("tasks", [])
        if not tasks:
            await query.edit_message_text("📋 Задач нет. Добавь: /add <задача>")
        else:
            text = "📋 *Твои задачи:*\n\n"
            for i, task in enumerate(tasks, 1):
                status = "✅" if task["done"] else "⬜"
                text += f"{status} {i}. {task['text']}\n"
            await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "done":
        await query.edit_message_text(
            "Отметь выполненную задачу командой:\n/done <номер>\n\nСписок задач: /list"
        )

    elif query.data == "stats":
        tasks = context.user_data.get("tasks", [])
        total = len(tasks)
        done = sum(1 for t in tasks if t["done"])
        pending = total - done
        percent = int((done / total) * 100) if total > 0 else 0
        bar_filled = percent // 10
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        text = (
            f"📊 *Статистика:*\n\n"
            f"Всего: {total} | ✅ {done} | ⬜ {pending}\n"
            f"[{bar}] {percent}%"
        )
        await query.edit_message_text(text, parse_mode="Markdown")

    elif query.data == "help":
        await query.edit_message_text(
            "📖 Команды:\n/add <задача> — добавить\n/list — список\n/done <номер> — выполнено\n/stats — статистика"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if not context.user_data.get("tasks"):
        context.user_data["tasks"] = []

    context.user_data["tasks"].append({"text": text, "done": False})
    task_num = len(context.user_data["tasks"])
    await update.message.reply_text(
        f"📝 Задача #{task_num} сохранена!\n*{text}*\n\n/list — посмотреть все",
        parse_mode="Markdown",
    )


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("Укажи BOT_TOKEN в переменных окружения!")

    # Start keep-alive server for Railway health checks
    keep_alive()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("clear", clear_tasks))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
