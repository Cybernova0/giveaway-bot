import logging
import sqlite3
import datetime
import time

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# ================= CONFIG =================

API_TOKEN = "7959398770:AAGjABI294aOpeSB9_MjNOeu6BUTQNNLaPs"
ADMIN_ID = 7334992081

CHANNEL_1 = "@HackingToolshere"
CHANNEL_2 = "@CYBERNOVA0"

# ================= SETUP =================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats(
    user_id INTEGER PRIMARY KEY,
    level INTEGER DEFAULT 1,
    daily_claim TEXT
)
""")

conn.commit()

# ================= MENU =================

menu = ReplyKeyboardMarkup(resize_keyboard=True)

menu.add(
    KeyboardButton("💰 Balance"),
    KeyboardButton("🎁 Giveaway")
)

menu.add(
    KeyboardButton("👑 Level"),
    KeyboardButton("🏆 Leaderboard")
)

menu.add(
    KeyboardButton("👥 Referral"),
    KeyboardButton("📞 Contact Developer")
)

# ================= ANTI SPAM =================

user_cooldown = {}

def anti_spam(user_id):
    now = time.time()

    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 3:
            return False

    user_cooldown[user_id] = now
    return True

# ================= FORCE JOIN =================

async def check_subscription(user_id):
    try:
        m1 = await bot.get_chat_member(CHANNEL_1, user_id)
        m2 = await bot.get_chat_member(CHANNEL_2, user_id)

        return m1.status != "left" and m2.status != "left"

    except:
        return False


def join_keyboard():
    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/HackingToolshere")
    )

    kb.add(
        InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/CYBERNOVA0")
    )

    kb.add(
        InlineKeyboardButton("✅ Check Again", callback_data="check_sub")
    )

    return kb

# ================= START =================

@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    user_id = message.from_user.id
    args = message.get_args()

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:

        referred_by = int(args) if args.isdigit() else None

        if referred_by == user_id:
            referred_by = None

        cursor.execute(
            "INSERT INTO users (user_id, referred_by) VALUES (?,?)",
            (user_id, referred_by)
        )

        conn.commit()

        if referred_by:
            cursor.execute(
                "UPDATE users SET points = points + 10 WHERE user_id=?",
                (referred_by,)
            )
            conn.commit()

    if not await check_subscription(user_id):

        await message.answer(
            "❌ Join channels first",
            reply_markup=join_keyboard()
        )
        return

    await message.answer("😎 Welcome to Final Boss Giveaway Bot", reply_markup=menu)

# ================= CHECK SUB =================

@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_sub(call: types.CallbackQuery):

    user_id = call.from_user.id

    if await check_subscription(user_id):
        await bot.send_message(user_id, "✅ Verified!", reply_markup=menu)
    else:
        await bot.answer_callback_query(call.id, "❌ Not yet joined", show_alert=True)

# ================= BALANCE =================

@dp.message_handler(lambda m: m.text == "💰 Balance")
async def balance(message: types.Message):

    if not anti_spam(message.from_user.id):
        return

    cursor.execute(
        "SELECT points FROM users WHERE user_id=?",
        (message.from_user.id,)
    )

    points = cursor.fetchone()[0]

    await message.answer(f"💰 Balance: {points} points")

# ================= REFERRAL =================

@dp.message_handler(lambda m: m.text == "👥 Referral")
async def referral(message: types.Message):

    link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"

    await message.answer(
        f"🔗 Referral Link:\n{link}\n\nEarn 10 points per invite!"
    )

# ================= GIVEAWAY =================

@dp.message_handler(lambda m: m.text == "🎁 Giveaway")
async def giveaway(message: types.Message):

    cursor.execute(
        "SELECT points FROM users WHERE user_id=?",
        (message.from_user.id,)
    )

    points = cursor.fetchone()[0]

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton("15 Points (7.5⭐)", callback_data="stars_15")
    )

    kb.add(
        InlineKeyboardButton("30 Points (15⭐)", callback_data="stars_30")
    )

    await message.answer(
        f"⭐ Stars Withdrawal\nRate: 0.5 ⭐ per point\nMinimum: 15 points\n\nYour Balance: {points}",
        reply_markup=kb
    )

# ================= STARS WITHDRAW =================

@dp.callback_query_handler(lambda c: c.data.startswith("stars_"))
async def process_stars(call: types.CallbackQuery):

    user_id = call.from_user.id
    amount = int(call.data.split("_")[1])

    cursor.execute(
        "SELECT points FROM users WHERE user_id=?",
        (user_id,)
    )

    points = cursor.fetchone()[0]

    if points < amount:
        await bot.answer_callback_query(call.id, "❌ Not enough points", show_alert=True)
        return

    if amount < 15:
        await bot.answer_callback_query(call.id, "❌ Minimum 15 points", show_alert=True)
        return

    stars = amount * 0.5

    cursor.execute(
        "UPDATE users SET points = points - ? WHERE user_id=?",
        (amount, user_id)
    )

    conn.commit()

    await bot.send_message(
        ADMIN_ID,
        f"""
⭐ Withdrawal Request

User: {user_id}
Points: {amount}
Stars: {stars}
"""
    )

    await bot.send_message(
        user_id,
        f"⏳ Request sent!\nYou will receive {stars} ⭐ after approval."
    )

# ================= LEVEL =================

@dp.message_handler(lambda m: m.text == "👑 Level")
async def level(message: types.Message):

    cursor.execute(
        "SELECT level FROM stats WHERE user_id=?",
        (message.from_user.id,)
    )

    data = cursor.fetchone()

    level = data[0] if data else 1

    await message.answer(f"👑 VIP Level: {level}")

# ================= LEADERBOARD =================

@dp.message_handler(lambda m: m.text == "🏆 Leaderboard")
async def leaderboard(message: types.Message):

    cursor.execute(
        "SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10"
    )

    rows = cursor.fetchall()

    text = "🏆 Top Players\n\n"

    rank = 1

    for user_id, points in rows:
        text += f"{rank}. {user_id} — {points} pts\n"
        rank += 1

    await message.answer(text)

# ================= CONTACT =================

@dp.message_handler(lambda m: m.text == "📞 Contact Developer")
async def contact(message: types.Message):

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "📲 WhatsApp",
            url="https://t.me/Cybernova_io"
        )
    )

    await message.answer("Contact developer 👇", reply_markup=kb)

# ================= RUN =================

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)