import os
import asyncio
from flask import Flask, request
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URL = os.environ.get("MONGO_URL")
RENDER_URL = os.environ.get("RENDER_URL")

app = Client("AutoDeleteBot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

flask_app = Flask(__name__)

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo.autodelete
settings = db.settings

# --- Control Panel ---
@app.on_message(filters.command("panel") & filters.group)
async def panel(client, message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if not member.privileges:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("30 Sec", callback_data="30"),
         InlineKeyboardButton("60 Sec", callback_data="60")],
        [InlineKeyboardButton("5 Min", callback_data="300")],
        [InlineKeyboardButton("🟢 Start", callback_data="start"),
         InlineKeyboardButton("🔴 Stop", callback_data="stop")]
    ])

    await message.reply("⚙ Advanced Auto Delete Panel", reply_markup=keyboard)

# --- Button Handler ---
@app.on_callback_query()
async def callback_query(client, query):
    chat_id = query.message.chat.id
    data = query.data

    if data.isdigit():
        await settings.update_one({"chat_id": chat_id},
                                  {"$set": {"timer": int(data)}},
                                  upsert=True)
        await query.message.edit_text(f"✅ Timer set to {data} seconds")

    elif data == "start":
        await settings.update_one({"chat_id": chat_id},
                                  {"$set": {"status": True}},
                                  upsert=True)
        await query.message.edit_text("🟢 Auto Delete Enabled")

    elif data == "stop":
        await settings.update_one({"chat_id": chat_id},
                                  {"$set": {"status": False}},
                                  upsert=True)
        await query.message.edit_text("🔴 Auto Delete Disabled")

# --- Auto Delete ---
@app.on_message(filters.group & ~filters.service)
async def auto_delete(client, message):
    data = await settings.find_one({"chat_id": message.chat.id})
    if data and data.get("status"):

        timer = data.get("timer", 60)
        await asyncio.sleep(timer)

        try:
            await message.delete()
        except:
            pass

# --- Webhook Route ---
@flask_app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    await app.process_update(
        await request.get_json()
    )
    return "ok"

# --- Start ---
async def main():
    await app.start()
    await app.set_webhook(f"{RENDER_URL}/{BOT_TOKEN}")
    print("Bot Running With Webhook...")

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
    flask_app.run(host="0.0.0.0", port=10000)
