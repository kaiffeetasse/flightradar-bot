import threading
from dotenv import load_dotenv
import os
import logging
from telegram.ext import (
    Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler,
)
from api import telegram_api
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

    dispatcher.add_handler(CallbackQueryHandler(telegram_api.track_callback))

    updater.start_polling()

    updater.idle()
