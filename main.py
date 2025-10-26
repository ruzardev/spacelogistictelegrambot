import hmac
import hashlib
import json
import asyncio
import logging
import os
from urllib.parse import parse_qsl
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F, types
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# -------------------------------
# 🔧 Настройки и инициализация
# -------------------------------
BOT_TOKEN = os.getenv("API_TOKEN")
FRONTEND_URL = os.getenv("WEBAPP_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# CORS — разрешаем запросы только с фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# -------------------------------
# 🧮 Проверка подписи initData
# -------------------------------
def verify_init_data(init_data: str):
    logger.info("🔹 Проверяем initData...")
    logger.debug(f"RAW initData: {init_data[:250]}...")

    data = dict(parse_qsl(init_data, keep_blank_values=True))
    if "hash" not in data:
        raise ValueError("Нет hash в initData")

    their_hash = data.pop("hash")
    pairs = [f"{k}={data[k]}" for k in sorted(data.keys())]
    data_check_string = "\n".join(pairs)

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    my_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(my_hash, their_hash):
        raise ValueError("❌ Подпись не совпадает (Bad hash)")

    user_json = data.get("user")
    if not user_json:
        raise ValueError("❌ Поле user отсутствует в initData")

    user = json.loads(user_json)
    logger.info(f"✅ Подпись прошла. Пользователь: {user}")
    return user

# -------------------------------
# 🧾 Обработка формы
# -------------------------------
@app.post("/api/form")
async def handle_form(request: Request):
    logger.info("📩 Получен запрос /api/form")

    try:
        body = await request.json()
        init_data = body.get("initData")
        form = body.get("form", {})
        logger.info(f"➡️ Полученные данные формы: {form}")

        if not init_data:
            raise HTTPException(400, "initData отсутствует")

        # Проверяем initData
        user = verify_init_data(init_data)
        user_id = user["id"]

        # Пример модификации данных
        processed = {k: str(v).upper() for k, v in form.items()}
        text = (
            f"✅ Ваша форма обработана!\n\n"
            f"Исходные данные:\n{json.dumps(form, ensure_ascii=False, indent=2)}\n\n"
            f"Модифицированные:\n{json.dumps(processed, ensure_ascii=False, indent=2)}"
        )

        # Отправляем пользователю сообщение
        logger.info(f"📤 Отправляем сообщение пользователю {user_id}")
        await bot.send_message(chat_id=user_id, text=text)

        logger.info("✅ Сообщение отправлено успешно")
        return {"ok": True, "message": "Форма успешно обработана"}

    except Exception as e:
        logger.exception("❌ Ошибка при обработке формы")
        raise HTTPException(500, f"Ошибка: {e}")

# -------------------------------
# 🤖 Обработка /start
# -------------------------------
@dp.message(F.text == "/start")
async def start_command(message: types.Message):
    logger.info(f"▶️ Пользователь {message.from_user.id} запустил /start")

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(
                text="🧾 Открыть форму",
                web_app=types.WebAppInfo(url=FRONTEND_URL)
            )
        ]]
    )
    await message.answer(
        "👋 Привет! Нажмите на кнопку ниже, чтобы открыть форму:",
        reply_markup=keyboard,
    )

# -------------------------------
# 🚀 Основной запуск
# -------------------------------
async def main():
    logger.info("🚀 Запуск сервера FastAPI и polling бота...")
    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())  # фоновый запуск FastAPI
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
