import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import exceptions, executor

# --- CONFIG ---
BOT_TOKEN = "8185897957:AAFzkFHf5qKPXkRtdOGXv6Oobhihz8OVEHo"  # 🔒 Replace with your new token
ADMIN_ID = 7513254429  # Replace with your Telegram user ID
CHANNEL_INVITE_LINK = "https://t.me/ErosComicShop"  # Replace with your channel link

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# --- DATABASE SETUP ---
conn = sqlite3.connect("referrals.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referred_by INTEGER
)
""")
conn.commit()

# --- COMMANDS ---

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    args = message.get_args()
    referrer = None

    if args.startswith("ref_"):
        referrer = int(args.replace("ref_", ""))

    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
                  (user_id, username, referrer))
        conn.commit()

    welcome_text = "Welcome to the Comic Channel Bot! 🎉\n"
    if referrer:
        welcome_text += f"You were invited by user ID {referrer}.\n"
    welcome_text += f"Click here to join the channel: {CHANNEL_INVITE_LINK}"
    await message.answer(welcome_text)

@dp.message_handler(commands=["mylink"])
async def mylink(message: types.Message):
    link = f"https://t.me/{(await bot.get_me()).username}?start=ref_{message.from_user.id}"
    await message.answer(f"Your referral link:\n{link}")

# --- Admin command to see who invited whom ---
@dp.message_handler(commands=["allrefs"])
async def allrefs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("You’re not authorized 😎")

    c.execute("SELECT user_id, username, referred_by FROM users")
    rows = c.fetchall()
    if not rows:
        await message.answer("No referrals yet.")
        return

    msg = "User ID | Username | Referred By\n"
    msg += "\n".join([f"{r[0]} | {r[1]} | {r[2]}" for r in rows])
    await message.answer(f"<pre>{msg}</pre>", parse_mode="HTML")
    
@dp.message_handler(commands=["find"])
async def find_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("You’re not authorized 😎")

    try:
        _, query = message.text.split(maxsplit=1)
    except ValueError:
        return await message.answer("Usage: /find <username or user_id>")

    # Check if query is a number (user_id)
    if query.isdigit():
        c.execute("SELECT user_id, username, referred_by FROM users WHERE user_id=?", (int(query),))
    else:
        # Make sure the username starts with @ (optional)
        if query.startswith("@"):
            query = query[1:]
        c.execute("SELECT user_id, username, referred_by FROM users WHERE username=?", (query,))
    
    user = c.fetchone()
    if not user:
        return await message.answer(f"No user found with: {query}")

    # Get referrer's username if possible
    ref_id = user[2]
    ref_username = "Unknown"
    if ref_id:
        c.execute("SELECT username FROM users WHERE user_id=?", (ref_id,))
        ref = c.fetchone()
        if ref:
            ref_username = ref[0]

    await message.answer(
        f"👤 User: @{user[1] or 'NoUsername'}\n"
        f"🆔 ID: {user[0]}\n"
        f"🔗 Invited by: @{ref_username or 'Unknown'} (ID: {ref_id or 'N/A'})"
    )



if __name__ == "__main__":

    executor.start_polling(dp, skip_updates=True)
