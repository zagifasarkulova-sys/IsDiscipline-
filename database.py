import asyncpg
import os
from datetime import datetime


async def create_pool():
    return await asyncpg.create_pool(os.getenv("DATABASE_URL"))


async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                remind_at TIMESTAMP,
                is_done BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_sessions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                started_at TIMESTAMP DEFAULT NOW(),
                paused_at TIMESTAMP,
                finished_at TIMESTAMP,
                total_seconds INTEGER DEFAULT 0
            )
        """)


# ─── Users ───────────────────────────────────────────────

async def ensure_user(pool, user_id: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET username = $2
        """, user_id, username)


# ─── Tasks ───────────────────────────────────────────────

async def add_task(pool, user_id: int, title: str, remind_at=None):
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO tasks (user_id, title, remind_at)
            VALUES ($1, $2, $3)
            RETURNING id
        """, user_id, title, remind_at)


async def get_tasks(pool, user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT id, title, remind_at, is_done
            FROM tasks
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user_id)


async def get_task(pool, task_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT id, title, remind_at, is_done
            FROM tasks WHERE id = $1
        """, task_id)


async def update_task_title(pool, task_id: int, new_title: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tasks SET title = $1 WHERE id = $2
        """, new_title, task_id)


async def update_task_remind(pool, task_id: int, remind_at):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tasks SET remind_at = $1 WHERE id = $2
        """, remind_at, task_id)


async def mark_task_done(pool, task_id: int, done: bool = True):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tasks SET is_done = $1 WHERE id = $2
        """, done, task_id)


async def delete_task(pool, task_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM tasks WHERE id = $1", task_id)


# ─── Focus sessions ──────────────────────────────────────

async def start_focus(pool, user_id: int, task_id: int) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO focus_sessions (user_id, task_id, started_at)
            VALUES ($1, $2, NOW())
            RETURNING id
        """, user_id, task_id)


async def pause_focus(pool, session_id: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE focus_sessions SET paused_at = NOW() WHERE id = $1
        """, session_id)


async def resume_focus(pool, session_id: int, extra_seconds: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE focus_sessions
            SET paused_at = NULL,
                total_seconds = total_seconds + $2
            WHERE id = $1
        """, session_id, extra_seconds)


async def finish_focus(pool, session_id: int, extra_seconds: int):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE focus_sessions
            SET finished_at = NOW(),
                total_seconds = total_seconds + $2
            WHERE id = $1
        """, session_id, extra_seconds)


async def get_active_session(pool, user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
            SELECT id, task_id, started_at, paused_at, total_seconds
            FROM focus_sessions
            WHERE user_id = $1 AND finished_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
        """, user_id)
