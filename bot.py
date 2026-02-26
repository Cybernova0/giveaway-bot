import asyncio
import logging
import sqlite3
import time
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart

# ================= CONFIG =================

TOKEN = os.getenv("7959398770:AAGjABI294aOpeSB9_MjNOeu6BUTQNNLaPs")
ADMIN_ID = 7334992081

CHANNEL_1 = "@HackingToolshere"
CHANNEL_2 = "@CYBERNOVA0"

# ================= SETUP =================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    referred_by INTEGER
)
""")

conn.commit()

# ================= MENU =================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Balance"), KeyboardButton(text="🎁 Giveaway")],
        [KeyboardButton(text="👥 Referral"), KeyboardButton(text="🏆 Leaderboard")],
        [KeyboardButton(text="📞 Contact Developer")]
    ],
    resize_keyboard=True
)

# ================= ANTI SPAM =================

user_cooldown = {}

def anti_spam(user_id):
    now = time.time()
    if user_id in user_cooldown and now - user_cooldown[user_id] < 3:
        return False
    user_cooldown[user_id] = now
    return True

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    await message.answer("😎 Welcome to Final Boss Giveaway Bot", reply_markup=menu)

# ================= BALANCE =================

@dp.message(F.text == "💰 Balance")
async def balance(message: Message):
    if not anti_spam(message.from_user.id):
        return

    cursor.execute("SELECT points FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    points = data[0] if data else 0

    await message.answer(f"💰 Balance: {points} points")

# ================= REFERRAL =================

@dp.message(F.text == "👥 Referral")
async def referral(message: Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"🔗 Referral Link:\n{link}")

# ================= LEADERBOARD =================

@dp.message(F.text == "🏆 Leaderboard")
async def leaderboard(message: Message):
    cursor.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    rows = cursor.fetchall()

    text = "🏆 Top Players\n\n"
    for i, (uid, pts) in enumerate(rows, 1):
        text += f"{i}. {uid} — {pts} pts\n"

    await message.answer(text)

# ================= CONTACT =================

@dp.message(F.text == "📞 Contact Developer")
async def contact(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📲 Contact", url="https://t.me/Cybernova_io")]
        ]
    )
    await message.answer("Contact developer 👇", reply_markup=kb)

# ================= RUN =================

async def main():
    print("Bot started successfully 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
