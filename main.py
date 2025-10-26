import hmac, hashlib, json, asyncio
from urllib.parse import parse_qsl
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, F, types
from starlette.middleware.cors import CORSMiddleware

BOT_TOKEN = "7324156410:AAEx7O4Y1NUnQOKAr1tOrZg-9jm1orlLb94"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_init_data(init_data: str):
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    if "hash" not in data:
        raise ValueError("No hash")
    their_hash = data.pop("hash")

    pairs = [f"{k}={data[k]}" for k in sorted(data.keys())]
    dcs = "\n".join(pairs)
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    my_hash = hmac.new(secret_key, dcs.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(my_hash, their_hash):
        raise ValueError("Bad hash")

    user_json = data.get("user")
    if not user_json:
        raise ValueError("No user")
    return json.loads(user_json)

@app.post("/api/form")
async def handle_form(request: Request):
    body = await request.json()
    init_data = body.get("initData")
    form = body.get("form", {})
    if not init_data:
        raise HTTPException(400, "initData required")
    user = verify_init_data(init_data)
    user_id = user["id"]
    text = f"✅ Новая форма от {user_id}:\n{json.dumps(form, ensure_ascii=False, indent=2)}"
    await bot.send_message(chat_id=user_id, text=text)
    return {"ok": True, "message": "Форма успешно обработана"}

@dp.message(F.text == "/start")
async def start_command(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(
                text="Открыть форму",
                web_app=types.WebAppInfo(url="https://web-app-telegram-six.vercel.app/")
            )
        ]]
    )
    await message.answer("👋 Привет! Открой форму ниже:", reply_markup=keyboard)

async def main():
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8080)
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
