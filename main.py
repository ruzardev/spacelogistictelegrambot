import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# === Конфигурация ===
API_TOKEN = os.getenv("API_TOKEN", "7324156410:AAEx7O4Y1NUnQOKAr1tOrZg-9jm1orlLb94")

WEBHOOK_PATH = "/webhook"
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://spacelogistictelegrambot.onrender.com")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://space-logistic-webapp.vercel.app")

WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# === /start ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚛 Открыть форму", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    await message.answer("Нажмите кнопку, чтобы открыть форму WebApp:", reply_markup=keyboard)


# === Обработка данных из WebApp (sendData)
@dp.message()
async def handle_webapp(message: types.Message):
    if message.web_app_data:
        data = message.web_app_data.data
        logging.info(f"📦 Получены данные из WebApp: {data}")
        await message.answer(f"✅ Форма получена!\n<code>{data}</code>", parse_mode="HTML")
    else:
        logging.info(f"💬 Сообщение без web_app_data: {message.text}")
        await message.answer("Сообщение получено (без WebApp данных).")


# === Webhook lifecycle ===
async def on_startup(app: web.Application):
    await bot.set_webhook(
        WEBHOOK_URL,
        allowed_updates=["message", "web_app_data"]
    )
    logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logging.info("🧹 Webhook удалён")


# === Запуск aiohttp ===
def main():
    app = web.Application()

    # Регистрируем webhook-обработчик
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Регистрируем lifecycle-хуки
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
