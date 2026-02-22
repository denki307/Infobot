import os
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

app = Client("ReferralBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def add_referral(referrer_id):
    cursor.execute(
        "UPDATE users SET referrals = referrals + 1, balance = balance + 10 WHERE user_id = ?",
        (referrer_id,)
    )
    conn.commit()

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    add_user(user_id)

    args = message.text.split()
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id:
                add_referral(referrer_id)
        except:
            pass

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral Link", callback_data="ref")]
    ])

    await message.reply_text(
        "🔥 Welcome macha!\nUse buttons below:",
        reply_markup=buttons
    )

@app.on_message(filters.command("admin"))
async def admin_panel(client, message):
    if message.from_user.id != ADMIN_ID:
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Total Users", callback_data="total_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("💰 Add Balance", callback_data="add_balance")]
    ])

    await message.reply_text("🧾 Admin Panel", reply_markup=buttons)

@app.on_callback_query()
async def callbacks(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "balance":
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        await callback_query.message.reply_text(f"💰 Your Balance: {balance} Coins")

    elif data == "ref":
        bot_username = (await app.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        await callback_query.message.reply_text(
            f"👥 Your Referral Link:\n{referral_link}\n\nEarn 10 coins per referral 🔥"
        )

    elif user_id == ADMIN_ID:

        if data == "total_users":
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            await callback_query.message.reply_text(f"📊 Total Users: {total}")

        elif data == "broadcast":
            await callback_query.message.reply_text(
                "📢 Send the message you want to broadcast."
            )
            app.broadcast_mode = True

        elif data == "add_balance":
            await callback_query.message.reply_text(
                "💰 Send in format:\n123456789 50"
            )
            app.balance_mode = True

@app.on_message(filters.text & filters.user(ADMIN_ID))
async def admin_text_handler(client, message):

    if hasattr(app, "broadcast_mode") and app.broadcast_mode:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        for user in users:
            try:
                await client.send_message(user[0], message.text)
            except:
                pass

        await message.reply_text("✅ Broadcast Sent.")
        app.broadcast_mode = False

    elif hasattr(app, "balance_mode") and app.balance_mode:
        try:
            uid, amount = message.text.split()
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (int(amount), int(uid))
            )
            conn.commit()
            await message.reply_text("✅ Balance Added.")
        except:
            await message.reply_text("❌ Wrong Format.")
        app.balance_mode = False

app.run()
