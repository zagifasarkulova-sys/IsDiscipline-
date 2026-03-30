import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from handlers import router
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com
WEBHOOK_PATH = f"/webhook/{TOKEN}"
PORT = int(os.getenv("PORT", 10000))


async def on_startup(app):
    bot: Bot = app["bot"]
    pool = app["pool"]
    await db.init_db(pool)
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    logger.info("Bot started, webhook set.")


async def on_shutdown(app):
    bot: Bot = app["bot"]
    await bot.delete_webhook()
    await app["pool"].close()
    logger.info("Bot stopped.")


async def health(request):
    return web.Response(text="OK")


async def main():
    bot = Bot(token=TOKEN)
    pool = await db.create_pool()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Передаём pool в хендлеры через middleware
    dp.update.middleware.register(PoolMiddleware(pool))
    dp.include_router(router)

    app = web.Application()
    app["bot"] = bot
    app["pool"] = pool

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    app.router.add_get("/health", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Server started on port {PORT}")
    await asyncio.Event().wait()


# ─── Pool Middleware ──────────────────────────────────────

from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject


class PoolMiddleware(BaseMiddleware):
    def __init__(self, pool):
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["pool"] = self.pool
        return await handler(event, data)


if __name__ == "__main__":
    asyncio.run(main())
