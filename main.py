import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

API_TOKEN = "7324156410:AAEx7O4Y1NUnQOKAr1tOrZg-9jm1orlLb94"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://your-domain.com{WEBHOOK_PATH}"  # адрес, куда Телеграм будет отправлять обновления
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8080

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("🧹 Webhook удалён")


async def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    asyncio.run(main())
