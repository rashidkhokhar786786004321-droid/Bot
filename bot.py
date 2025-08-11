import json
import requests
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# === CONFIG ===
BOT_TOKEN = "7531864759:AAF-SfvbWcjHPxFXGHpYTCk8svh4aXOBim4"
API_URL = "http://musa699.serv00.net/public%20api.php?number="
USERS_FILE = "users.json"

# Emoji mapping same as PHP code
EMOJI_MAP = {
    'Name': '👤 Name',
    'CNIC': '🆔 CNIC',
    'Address': '🗺️ Address',
    'Associated Numbers': '🔢 Associated Numbers'
}

# Load or create user list
try:
    with open(USERS_FILE, "r") as f:
        users = set(json.load(f))
except FileNotFoundError:
    users = set()

# === START COMMAND ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    users.add(user_id)
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

    keyboard = [
        [InlineKeyboardButton("📢 Support Channel", url="https://t.me/Musa_x2")],
        [InlineKeyboardButton("👥 Join Group", url="https://t.me/Discuss_group33")],
        [InlineKeyboardButton("🔍 Find Data", callback_data="find_data")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"Welcome to Musa SIM Database Bot, @{username}!"
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# === BUTTON HANDLER ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "find_data":
        context.user_data["awaiting_number"] = True
        await query.message.reply_text("📥 Enter Number/CNIC:")

    elif query.data == "stats":
        count = len(users)
        await query.message.reply_text(f"📊 Total unique users: {count}")

# === MESSAGE HANDLER FOR NUMBER ===
async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_number"):
        number = update.message.text.strip()
        context.user_data["awaiting_number"] = False

        # Send loading emoji
        loading_msg = await update.message.reply_text("💬")

        # Fetch data from PHP API
        try:
            response = requests.get(API_URL + number, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Parse the HTML like PHP
            result_div = soup.find("div", class_="result-box")
            if result_div:
                rows = result_div.find_all("tr")
                data = {}

                for row in rows:
                    th = row.find("th")
                    td = row.find("td")
                    if th and td:
                        key = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        data[key] = value

                numbers_list = []
                li_items = result_div.find_all("li")
                for li in li_items:
                    numbers_list.append(li.get_text(strip=True))

                if numbers_list:
                    data["Associated Numbers"] = numbers_list

                # Format output like PHP
                content = "📞 SIM Information Result\n\n"
                for key, value in data.items():
                    label = EMOJI_MAP.get(key, key)
                    if isinstance(value, list):
                        content += f"{label}:\n"
                        for v in value:
                            content += f"   ➤ {v}\n"
                    else:
                        content += f"{label}: {value}\n"

            else:
                content = "❌ No data found for this number."

        except Exception as e:
            content = f"⚠️ Error fetching data: {e}"

        # Delete loading emoji
        await loading_msg.delete()

        # Send result
        await update.message.reply_text(content)

# === MAIN ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
