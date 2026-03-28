import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import asyncpg

from database import get_pool
from keyboards import morning_kb, evening_result_kb

logger = logging.getLogger(__name__)


async def send_morning_messages(bot: Bot):
    """Send morning focus message to all users"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id, main_goal, morning_time FROM users")

    for user in users:
        try:
            goal = user["main_goal"] or "не задана"
            await bot.send_message(
                user["user_id"],
                f"☀️ <b>Доброе утро!</b>\n\n"
                f"🎯 Твоя цель: <i>{goal}</i>\n\n"
                f"Что сделаем сегодня?\n"
                f"Введи главную задачу дня 👇",
                reply_markup=morning_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Morning message failed for {user['user_id']}: {e}")


async def send_evening_messages(bot: Bot):
    """Send evening audit to all users"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.user_id, t.main_task
            FROM users u
            LEFT JOIN tasks t ON t.user_id = u.user_id AND t.date = CURRENT_DATE
        """)

    for row in rows:
        try:
            task_text = row["main_task"] or "задача не была введена"
            await bot.send_message(
                row["user_id"],
                f"🌙 <b>Вечерний аудит</b>\n\n"
                f"Сегодняшняя задача:\n"
                f"📌 <i>{task_text}</i>\n\n"
                f"Удалось выполнить?",
                reply_markup=evening_result_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Evening message failed for {row['user_id']}: {e}")


async def send_weekly_review(bot: Bot):
    """Send weekly review on Sunday"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT user_id FROM users")

    for user in users:
        try:
            from database import get_week_stats, get_current_weekly_goal
            stats = await get_week_stats(user["user_id"])
            weekly = await get_current_weekly_goal(user["user_id"])

            goal_text = weekly["goal"] if weekly else "не задана"
            prog = weekly["progress_percent"] if weekly else 0

            await bot.send_message(
                user["user_id"],
                f"📅 <b>Еженедельный обзор</b>\n\n"
                f"За прошедшую неделю:\n"
                f"✅ Выполнено задач: {stats['completed']} из {stats['total']}\n"
                f"⏱ В фокусе: {stats['focus_minutes'] // 60}ч {stats['focus_minutes'] % 60}мин\n\n"
                f"🎯 Цель недели: <i>{goal_text}</i>\n"
                f"📈 Прогресс: {prog}%\n\n"
                f"Какая цель на следующую неделю? Напиши её:",
                parse_mode="HTML"
            )
            # Set state for weekly goal input
            from states import FocusStates
        except Exception as e:
            logger.warning(f"Weekly review failed for {user['user_id']}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

    # Morning messages at 08:00
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=8, minute=0, timezone="Asia/Almaty"),
        args=[bot],
        id="morning_messages",
        replace_existing=True,
        misfire_grace_time=300
    )

    # Evening audit at 21:00
    scheduler.add_job(
        send_evening_messages,
        CronTrigger(hour=21, minute=0, timezone="Asia/Almaty"),
        args=[bot],
        id="evening_messages",
        replace_existing=True,
        misfire_grace_time=300
    )

    # Weekly review on Sunday at 20:00
    scheduler.add_job(
        send_weekly_review,
        CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Asia/Almaty"),
        args=[bot],
        id="weekly_review",
        replace_existing=True,
        misfire_grace_time=600
    )

    logger.info("Scheduler configured")
    return scheduler
