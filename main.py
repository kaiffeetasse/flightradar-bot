import math
import threading
import time
from FlightRadar24.api import FlightRadar24API
from dotenv import load_dotenv
import os
import logging
from telegram.ext import (
    Updater,
    MessageHandler, Filters, CommandHandler,
)
import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
fr_api = FlightRadar24API()

default_radius_km = 5


def set_location(update, context):
    user_id = update.message.from_user.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude

    db.set_user_location(user_id, latitude, longitude)

    update.message.reply_text("Location set!")


def get_y1_y2_x1_x2(latitude, longitude, radius_km):
    # https://stackoverflow.com/a/27943/1034395
    # 1 deg = 111.32 km
    y1 = latitude + radius_km / 111.32
    y2 = latitude - radius_km / 111.32
    x1 = longitude - radius_km / (111.32 * math.cos(latitude * math.pi / 180))
    x2 = longitude + radius_km / (111.32 * math.cos(latitude * math.pi / 180))

    return y1, y2, x1, x2


def send_message_to_user(user_id, message):
    updater.bot.send_message(user_id, message)


def check_flights_for_users_threaded():
    user_flights = {}
    user_flight_ids = {}

    while True:

        try:

            for user in db.get_users():

                user_id = user.telegram_id
                latitude = user.latitude
                longitude = user.longitude
                user_radius = user.radius_km

                if user_flights.get(user_id) is None:
                    user_flights[user_id] = []
                    user_flight_ids[user_id] = []

                logger.debug(f"Checking for user {user_id} at {latitude}, {longitude}")

                y1, y2, x1, x2 = get_y1_y2_x1_x2(latitude, longitude, user_radius)

                new_user_flights = fr_api.get_flights(bounds=f"{y1},{y2},{x1},{x2}")
                new_user_flight_ids = [flight.id for flight in new_user_flights]

                for flight in new_user_flights:

                    logger.debug(f"Checking flight {flight.id} for user {user_id}")

                    if flight.id not in user_flight_ids.get(user_id):
                        altitude_ft = flight.altitude
                        altitude_m = int(altitude_ft * 0.3048)

                        speed_kt = flight.ground_speed
                        speed_kmh = int(speed_kt * 1.852)

                        msg = "✈ New flight over your location ✈\n\n"
                        msg = msg + f"Aircraft: {flight.callsign} ({flight.aircraft_code})\n"
                        msg = msg + f"Altitude: {altitude_m}m\n"
                        msg = msg + f"Speed: {speed_kmh}km/h\n"
                        msg = msg + f"From: {flight.origin_airport_iata}\n"
                        msg = msg + f"To: {flight.destination_airport_iata}\n"
                        msg = msg + f"Link: https://www.flightradar24.com/{flight.callsign}/{flight.id}"

                        send_message_to_user(user_id, msg)

                        if user_flight_ids.get(user_id) is None:
                            user_flight_ids[user_id] = []

                        user_flight_ids[user_id].append(flight.id)

                for flight_id in user_flight_ids.get(user_id):
                    if flight_id not in new_user_flight_ids:
                        user_flight_ids[user_id].remove(flight_id)

        except Exception as e:
            print(e)

        time.sleep(5)


def handle_message(update, context):
    print(update.message.text)
    update.message.reply_text("test")


def start(update, context):
    update.message.reply_text("Send your location to start receiving notifications about flights over your location.")


def stop(update, context):
    try:
        db.remove_user(update.message.from_user.id)
        update.message \
            .reply_text("Notifications stopped. Send your location again to start receiving notifications again.")
    except KeyError:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")


def radius(update, context):
    user_id = update.message.from_user.id

    # check if user is registered
    user = db.get_user(user_id)
    if user is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
        return

    # when no args are passed, return current radius
    if len(update.message.text.split(" ")) == 1:
        user_radius = user.radius_km
        update.message \
            .reply_text(f"Current detection radius: {user_radius}km. You can change it with /radius <radius>.")
        return

    # try to set radius
    try:
        new_radius = int(update.message.text.split(" ")[1])

        if new_radius < 1:
            update.message.reply_text("Radius must be at least 1km.")
            return

        if new_radius > 25:
            update.message.reply_text("Radius must be less than 25km.")
            return

        db.set_user_radius(user_id, new_radius)
        update.message.reply_text(f"Detection radius set to {new_radius}km.")

    except ValueError:
        update.message.reply_text("Invalid radius. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting radius: ")
        logger.exception(e)


if __name__ == '__main__':
    thread = threading.Thread(target=check_flights_for_users_threaded)
    thread.start()

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.location, set_location))

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("radius", radius))

    # dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()

    updater.idle()
