import asyncio
import sys

from loguru import logger

from app.config import settings

# Configure loguru
logger.remove()
logger.add(sys.stderr, level=settings.log_level, format=(
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
))


async def main() -> None:
    from aiogram import Bot, Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage

    from app.db.engine import async_session, engine
    from app.db.models import Base
    from app.db.seed import seed_avatars
    from app.handlers import chat, commands, start
    from app.middlewares.db_session import DbSessionMiddleware

    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        await seed_avatars(session)

    logger.info("Database initialized and seeded")

    # Create bot and dispatcher
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Register middleware
    dp.update.outer_middleware(DbSessionMiddleware())

    # Register routers (order matters: commands before catch-all chat)
    dp.include_router(start.router)
    dp.include_router(commands.router)
    dp.include_router(chat.router)

    logger.info("Bot starting in polling mode")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
