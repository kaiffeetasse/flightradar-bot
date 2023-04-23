import threading
from FlightRadar24.api import FlightRadar24API
from dotenv import load_dotenv
import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import (
    Updater,
    MessageHandler, Filters, CommandHandler, CallbackQueryHandler,
)
import db
from commands import (
    altitude, altmax, altmin, location, radius, start, stop
)
from schedules import tracked_flights, location_flights

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
fr_api = FlightRadar24API()


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
    except Exception as e:
        logger.error("could not send message to user " + str(user_id))
        logger.exception(e)


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


def handle_message(update, context):
    print(update.message.text)
    update.message.reply_text("test")


if __name__ == '__main__':
    thread1 = threading.Thread(target=location_flights.check_flights_for_users_threaded)
    thread1.start()

    thread2 = threading.Thread(target=tracked_flights.check_tracked_flights_for_users_threaded)
    thread2.start()

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.location, location.set_location))

    dispatcher.add_handler(CommandHandler("start", start.start))
    dispatcher.add_handler(CommandHandler("stop", stop.stop))
    dispatcher.add_handler(CommandHandler("radius", radius.radius))
    dispatcher.add_handler(CommandHandler("altitude", altitude.altitude))
    dispatcher.add_handler(CommandHandler("altmin", altmin.altmin))
    dispatcher.add_handler(CommandHandler("altmax", altmax.altmax))

    dispatcher.add_handler(CallbackQueryHandler(track_callback))

    # dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()

    updater.idle()
