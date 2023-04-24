from dotenv import load_dotenv
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import Updater
import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)


def send_message_to_user(user_id, message, image_src, registration, tracking):
    track_button = get_track_button(registration, tracking)

    try:

        if image_src is None:
            updater.bot.send_message(user_id, message, reply_markup=track_button)
        else:
            updater.bot.send_photo(user_id, image_src, caption=message, reply_markup=track_button)
    except Unauthorized:
        # user has blocked the bot
        logger.error("could not send message to user " + str(user_id) + " (user has blocked the bot)")
        db.remove_user(user_id)
        db.remove_all_tracked_aiplanes(user_id)


def get_track_button(aircraft_registration, untrack=False):
    button_text = "📌 Track" if not untrack else "📌 Untrack"

    callback_text = ("track" if not untrack else "untrack") + "_" + aircraft_registration

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=callback_text)]
    ])

    return buttons


def track_callback(update, context):
    query = update.callback_query
    query.answer()

    if query.data.startswith("untrack"):
        db.untrack_aircraft(query.from_user.id, query.data.split("_")[1])
        tracking = False
    else:
        db.track_aircraft(query.from_user.id, query.data.split("_")[1])
        tracking = True

    # set button to (un)track
    message = query.message
    message.edit_reply_markup(get_track_button(query.data.split("_")[1], tracking))

    updater.bot.send_message(
        query.from_user.id,
        "Tracking of " + query.data.split("_")[1] + " " + ("started" if tracking else "stopped")
    )
