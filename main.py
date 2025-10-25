import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# === Конфигурация ===
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_PATH = "/webhook"
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # https://your-bot-name.onrender.com
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

WEBAPP_URL = os.getenv("WEBAPP_URL")  # ваш Vue WebApp (например, https://space-logistic-webapp.vercel.app)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === /start ===
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚛 Открыть WebApp",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )
    await message.answer("Откройте WebApp, чтобы отправить данные:", reply_markup=keyboard)

# === Обработка данных из WebApp ===
@dp.message(lambda m: m.web_app_data is not None)
async def handle_webapp(message: types.Message):
    data = message.web_app_data.data
    logging.info(f"Получены данные из WebApp: {data}")
    await message.answer(f"✅ Получены данные:\n<code>{data}</code>", parse_mode="HTML")

# === Webhook lifecycle ===
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, allowed_updates=["message", "web_app_data"])
    logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🧹 Webhook удалён")

# === Запуск aiohttp ===
def main():
    app = web.Application()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()
