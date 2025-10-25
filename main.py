import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# === Конфигурация ===
API_TOKEN = os.getenv("API_TOKEN")  # токен берётся из переменных окружения Render
WEBHOOK_PATH = "/webhook"
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render автоматически создаёт URL, например https://your-app-name.onrender.com
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))  # Render задаёт PORT автоматически

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === Хендлер ===
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")

# === Хуки ===
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"✅ Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🧹 Webhook удалён")

# === Основная функция ===
async def main():
    app = web.Application()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    asyncio.run(main())
