import os
import asyncpg
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

_pool = None


async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                user_name TEXT DEFAULT '',
                mentor_name TEXT DEFAULT 'Наставник',
                main_goal TEXT,
                morning_time TEXT DEFAULT '08:00',
                evening_time TEXT DEFAULT '21:00',
                timezone TEXT DEFAULT 'Asia/Almaty',
                xp INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                last_complete_date DATE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        for col, definition in [
            ("user_name", "TEXT DEFAULT ''"),
            ("mentor_name", "TEXT DEFAULT 'Наставник'"),
        ]:
            await conn.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {definition}")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                date DATE DEFAULT CURRENT_DATE,
                main_task TEXT,
                completed BOOLEAN DEFAULT FALSE,
                energy_level TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                duration_minutes INTEGER,
                completed BOOLEAN DEFAULT FALSE,
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                date DATE DEFAULT CURRENT_DATE,
                what_prevented TEXT,
                what_change TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS weekly_goals (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                week_start DATE,
                goal TEXT,
                progress_percent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

    logger.info("Database initialized")


async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def create_user(user_id: int, username: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, username)


async def update_user(user_id: int, **kwargs):
    pool = await get_pool()
    fields = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(kwargs))
    values = list(kwargs.values())
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {fields} WHERE user_id = $1",
            user_id, *values
        )


async def get_today_task(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM tasks
            WHERE user_id = $1 AND date = CURRENT_DATE
            ORDER BY created_at DESC LIMIT 1
        """, user_id)


async def create_task(user_id: int, main_task: str, energy_level: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO tasks (user_id, main_task, energy_level)
            VALUES ($1, $2, $3)
            RETURNING id
        """, user_id, main_task, energy_level)


async def update_today_task(user_id: int, main_task: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tasks SET main_task = $2
            WHERE user_id = $1 AND date = CURRENT_DATE
        """, user_id, main_task)


async def complete_task(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tasks SET completed = TRUE
            WHERE user_id = $1 AND date = CURRENT_DATE
        """, user_id)


async def get_week_stats(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM tasks
            WHERE user_id = $1 AND date >= CURRENT_DATE - INTERVAL '7 days'
        """, user_id)
        completed = await conn.fetchval("""
            SELECT COUNT(*) FROM tasks
            WHERE user_id = $1 AND date >= CURRENT_DATE - INTERVAL '7 days'
            AND completed = TRUE
        """, user_id)
        focus_mins = await conn.fetchval("""
            SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions
            WHERE user_id = $1
            AND started_at >= NOW() - INTERVAL '7 days'
            AND completed = TRUE
        """, user_id)
        today_sessions = await conn.fetchval("""
            SELECT COUNT(*) FROM focus_sessions
            WHERE user_id = $1 AND DATE(started_at) = CURRENT_DATE AND completed = TRUE
        """, user_id)
        today_minutes = await conn.fetchval("""
            SELECT COALESCE(SUM(duration_minutes), 0) FROM focus_sessions
            WHERE user_id = $1 AND DATE(started_at) = CURRENT_DATE AND completed = TRUE
        """, user_id)
        return {
            "total": total or 0,
            "completed": completed or 0,
            "focus_minutes": int(focus_mins or 0),
            "today_sessions": int(today_sessions or 0),
            "today_minutes": int(today_minutes or 0),
        }


async def has_session_today(user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM focus_sessions
            WHERE user_id = $1 AND DATE(started_at) = CURRENT_DATE
        """, user_id)
        return (count or 0) > 0


async def start_focus_session(user_id: int, duration: int) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO focus_sessions (user_id, duration_minutes)
            VALUES ($1, $2) RETURNING id
        """, user_id, duration)


async def end_focus_session(session_id: int, completed: bool):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE focus_sessions SET completed = $2, ended_at = NOW() WHERE id = $1
        """, session_id, completed)


async def add_xp_and_streak(user_id: int):
    pool = await get_pool()
    from datetime import date, timedelta
    today = date.today()
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        last = user["last_complete_date"]
        streak = user["streak"] or 0
        if last == today - timedelta(days=1):
            streak += 1
        elif last != today:
            streak = 1
        xp_gain = 10 + (streak * 2)
        await conn.execute("""
            UPDATE users SET xp = xp + $2, streak = $3, last_complete_date = $4
            WHERE user_id = $1
        """, user_id, xp_gain, streak, today)
        return streak, xp_gain


async def save_reflection(user_id: int, what_prevented: str, what_change: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO reflections (user_id, what_prevented, what_change)
            VALUES ($1, $2, $3)
        """, user_id, what_prevented, what_change)


async def get_current_weekly_goal(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM weekly_goals WHERE user_id = $1
            ORDER BY created_at DESC LIMIT 1
        """, user_id)


async def save_weekly_goal(user_id: int, goal: str):
    pool = await get_pool()
    from datetime import date
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO weekly_goals (user_id, week_start, goal) VALUES ($1, $2, $3)
        """, user_id, date.today(), goal)


async def update_weekly_progress(user_id: int, percent: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE weekly_goals SET progress_percent = $2
            WHERE user_id = $1
            AND id = (SELECT id FROM weekly_goals WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1)
        """, user_id, percent)


async def is_evening_done(user_id: int) -> bool:
    """Проверяет завершён ли вечерний аудит сегодня"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT completed FROM tasks
            WHERE user_id = $1 AND date = CURRENT_DATE
            ORDER BY created_at DESC LIMIT 1
        """, user_id)
        # Аудит считается пройденным если задача отмечена выполненной
        # или если есть запись в reflections за сегодня
        if row and row["completed"]:
            return True
        reflection = await conn.fetchrow("""
            SELECT id FROM reflections
            WHERE user_id = $1 AND date = CURRENT_DATE
        """, user_id)
        return reflection is not None
