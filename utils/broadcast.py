import db
import os
from telegram.ext import Updater

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
TEST_MODE = True

# this


def escape_text(text):
    return text \
        .replace("-", "\-") \
        .replace("_", "\_") \
        .replace(".", "\.") \
        .replace("|", "\|") \
        .replace("`", "\`") \
        .replace("=", "\=") \
        .replace("!", "\!")


users = db.get_users()

for user in users:
    telegram_id = user.telegram_id

    if telegram_id != "23730491" and TEST_MODE:
        continue

    msg = "*Update 2023-04-18*\n\n"
    msg = msg + "🖼️ Aircraft images"
    msg = msg + "📌 Track aircrafts (Beta)"

    updater.bot.send_message(telegram_id, escape_text(msg), parse_mode="MarkdownV2")

    print("sent message to " + str(telegram_id))
