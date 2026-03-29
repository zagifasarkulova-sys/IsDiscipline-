import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from database import get_pool, has_session_today, is_evening_done, get_today_task
from keyboards import morning_kb, morning_has_task_kb, evening_result_kb

logger = logging.getLogger(__name__)


def _name(user) -> str:
    return user["user_name"] or user["username"] or "друг"


def _mentor(user) -> str:
    return user["mentor_name"] or "Наставник"


async def send_morning_messages(bot: Bot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")

    for user in users:
        try:
            name = _name(user)
            goal = user["main_goal"] or "не задана"

            from database import get_today_task
            task = await get_today_task(user["user_id"])

            if task:
                await bot.send_message(
                    user["user_id"],
                    f"☀️ <b>Доброе утро, {name}!</b>\n\n"
                    f"🎯 Цель: <i>{goal}</i>\n\n"
                    f"Твоя задача на сегодня:\n"
                    f"📌 <i>{task['main_task']}</i>\n\n"
                    f"Всё верно или хочешь изменить?",
                    reply_markup=morning_has_task_kb(),
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    user["user_id"],
                    f"☀️ <b>Доброе утро, {name}!</b>\n\n"
                    f"🎯 Цель: <i>{goal}</i>\n\n"
                    f"Новый день. Чистый лист.\n"
                    f"Что будет на нём к вечеру?",
                    reply_markup=morning_kb(),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.warning(f"Morning message failed for {user['user_id']}: {e}")


async def send_midday_reminder(bot: Bot):
    """13:00 — если не было ни одной сессии"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")

    for user in users:
        try:
            had_session = await has_session_today(user["user_id"])
            if not had_session:
                name = _name(user)
                mentor = _mentor(user)
                await bot.send_message(
                    user["user_id"],
                    f"👀 <b>{name}</b>, половина дня прошла.\n\n"
                    f"Ты ещё не начинал работу сегодня.\n"
                    f"Это нормально — но только если начнёшь <b>сейчас</b>.\n\n"
                    f"— {mentor}",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.warning(f"Midday reminder failed for {user['user_id']}: {e}")


async def send_evening_messages(bot: Bot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.*, t.main_task, t.completed as task_completed
            FROM users u
            LEFT JOIN tasks t ON t.user_id = u.user_id AND t.date = CURRENT_DATE
        """)

    for row in rows:
        try:
            name = _name(row)
            task_text = row["main_task"] or "задача не была введена"
            if row["task_completed"]:
                continue  # уже отмечена выполненной — не спрашиваем
            await bot.send_message(
                row["user_id"],
                f"🌙 <b>Вечерний аудит, {name}</b>\n\n"
                f"Сегодняшняя задача:\n"
                f"📌 <i>{task_text}</i>\n\n"
                f"Слово сдержал?",
                reply_markup=evening_result_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Evening message failed for {row['user_id']}: {e}")


async def send_weekly_review(bot: Bot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")

    for user in users:
        try:
            from database import get_week_stats, get_current_weekly_goal
            stats = await get_week_stats(user["user_id"])
            weekly = await get_current_weekly_goal(user["user_id"])
            name = _name(user)

            goal_text = weekly["goal"] if weekly else "не задана"
            prog = weekly["progress_percent"] if weekly else 0
            bar = "█" * (prog // 10) + "░" * (10 - prog // 10)

            await bot.send_message(
                user["user_id"],
                f"📅 <b>Неделя закрыта, {name}. Давай посмотрим честно.</b>\n\n"
                f"✅ Выполнено задач: {stats['completed']} из {stats['total']}\n"
                f"⏱ В фокусе: {stats['focus_minutes'] // 60}ч {stats['focus_minutes'] % 60}мин\n\n"
                f"🎯 Цель недели: <i>{goal_text}</i>\n"
                f"[{bar}] {prog}%\n\n"
                f"Какая цель на следующую неделю?\nНапиши её:",
                parse_mode="HTML"
            )
            from states import FocusStates
        except Exception as e:
            logger.warning(f"Weekly review failed for {user['user_id']}: {e}")



async def send_evening_spam(bot: Bot):
    """Каждые 10 минут с 21:00 до 00:00 пока не сделан итог дня"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")

    for user in users:
        try:
            done = await is_evening_done(user["user_id"])
            if done:
                continue  # уже ответил — не беспокоим

            task = await get_today_task(user["user_id"])
            task_text = task["main_task"] if task else "задача не введена"
            name = _name(user)

            from keyboards import evening_audit_kb
            await bot.send_message(
                user["user_id"],
                f"🔔 <b>{name}, не забудь сделать итог дня!</b>\n\n"
                f"📌 <i>{task_text}</i>\n\n"
                f"Выполнил задачу?",
                reply_markup=evening_audit_kb(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Evening spam failed for {user['user_id']}: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")

    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=8, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="morning", replace_existing=True, misfire_grace_time=300
    )

    scheduler.add_job(
        send_task_reminder,
        CronTrigger(hour=10, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="task_reminder", replace_existing=True, misfire_grace_time=300
    )

    scheduler.add_job(
        send_midday_reminder,
        CronTrigger(hour=13, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="midday", replace_existing=True, misfire_grace_time=300
    )

    scheduler.add_job(
        send_evening_messages,
        CronTrigger(hour=21, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="evening", replace_existing=True, misfire_grace_time=300
    )

    scheduler.add_job(
        send_weekly_review,
        CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="weekly", replace_existing=True, misfire_grace_time=600
    )


    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=21, minute=10, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_21_10", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=21, minute=20, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_21_20", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=21, minute=30, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_21_30", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=21, minute=40, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_21_40", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=21, minute=50, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_21_50", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_0", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=10, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_10", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=20, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_20", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=30, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_30", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=40, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_40", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=22, minute=50, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_22_50", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=0, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_0", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=10, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_10", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=20, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_20", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=30, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_30", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=40, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_40", replace_existing=True, misfire_grace_time=120
    )

    scheduler.add_job(
        send_evening_spam,
        CronTrigger(hour=23, minute=50, timezone="Asia/Almaty"),
        args=[bot], id="evening_spam_23_50", replace_existing=True, misfire_grace_time=120
    )

    logger.info("Scheduler configured")
    return scheduler


async def send_task_reminder(bot: Bot):
    """10:00 — напоминание ввести задачу если ещё не ввёл"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        users = await conn.fetch("SELECT * FROM users")

    for user in users:
        try:
            from database import get_today_task
            task = await get_today_task(user["user_id"])
            if task:
                continue  # задача уже есть — не беспокоим

            name = _name(user)
            await bot.send_message(
                user["user_id"],
                f"⏰ <b>{name}, задача дня ещё не поставлена.</b>\n\n"
                f"До 11:00 ещё есть время — напиши что сделаешь сегодня.\n\n"
                f"Нажми 📝 Итог дня в меню.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Task reminder failed for {user['user_id']}: {e}")
