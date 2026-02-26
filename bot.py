import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("autodeletebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

delete_status = {}
delete_timer = {}

# Control Panel
@app.on_message(filters.command("panel") & filters.group)
async def panel(client, message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("30 Sec", callback_data="30"),
            InlineKeyboardButton("60 Sec", callback_data="60")
        ],
        [
            InlineKeyboardButton("5 Min", callback_data="300"),
            InlineKeyboardButton("Custom Timer", callback_data="custom")
        ],
        [
            InlineKeyboardButton("🟢 Start", callback_data="start"),
            InlineKeyboardButton("🔴 Stop", callback_data="stop")
        ]
    ])
    await message.reply("⚙ Auto Delete Control Panel", reply_markup=keyboard)

# Button Handler
@app.on_callback_query()
async def callback_handler(client, query):
    chat_id = query.message.chat.id
    data = query.data

    if data.isdigit():
        delete_timer[chat_id] = int(data)
        await query.message.edit_text(f"✅ Timer set to {int(data)} seconds")

    elif data == "start":
        delete_status[chat_id] = True
        await query.message.edit_text("🟢 Auto Delete Enabled")

    elif data == "stop":
        delete_status[chat_id] = False
        await query.message.edit_text("🔴 Auto Delete Disabled")

    elif data == "custom":
        await query.message.reply("Send /settimer <seconds>\nExample: /settimer 120")

# Custom Timer Command
@app.on_message(filters.command("settimer") & filters.group)
async def set_custom_timer(client, message):
    try:
        seconds = int(message.command[1])
        delete_timer[message.chat.id] = seconds
        await message.reply(f"✅ Custom Timer Set To {seconds} Seconds")
    except:
        await message.reply("❌ Usage: /settimer 120")

# Auto Delete Handler
@app.on_message(filters.group & ~filters.service)
async def auto_delete(client, message):
    chat_id = message.chat.id

    if delete_status.get(chat_id, False):
        timer = delete_timer.get(chat_id, 60)

        await asyncio.sleep(timer)

        try:
            await message.delete()
        except:
            pass

print("Auto Delete Bot Running...")
app.run()
