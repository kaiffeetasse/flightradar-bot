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
from staticmap import StaticMap, CircleMarker

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_API_TOKEN = os.environ.get("TELEGRAM_API_TOKEN")
updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
fr_api = FlightRadar24API()


def create_map(latitude, longitude, radius_km):
    y1, y2, x1, x2 = get_y1_y2_x1_x2(latitude, longitude, radius_km)

    width = 300

    m = StaticMap(width, width)
    m.add_marker(CircleMarker((x1, y1), None, 1))
    m.add_marker(CircleMarker((x2, y2), None, 1))

    image = m.render()
    image.save('map.png')


def set_location(update, context):
    user_id = update.message.from_user.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude

    user = db.set_user_location(user_id, latitude, longitude)
    user_radius_km = user.radius_km

    create_map(latitude, longitude, user_radius_km)

    update.message.reply_photo(open('map.png', 'rb'), caption="Location set! Radius: " + str(user_radius_km) + "km")


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
    if db.get_user(update.message.from_user.id) is None:
        update.message \
            .reply_text("Send your location to start receiving notifications about flights over your location.")
    else:
        update.message \
            .reply_text("You are already receiving notifications. Send /stop to stop receiving notifications.")


def stop(update, context):
    if db.get_user(update.message.from_user.id) is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
    else:
        db.remove_user(update.message.from_user.id)
        update.message \
            .reply_text("Notifications stopped. Send your location again to start receiving notifications again.")


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
        create_map(user.latitude, user.longitude, user_radius)

        update.message.reply_photo(
            open('map.png', 'rb'),
            caption=f"Current detection radius: {user_radius}km.\nYou can change it with /radius <radius>."
        )
        return

    # try to set radius
    try:
        new_radius = int(update.message.text.split(" ")[1].replace("km", ""))

        if new_radius < 1:
            update.message.reply_text("Radius must be at least 1km.")
            return

        if new_radius > 25:
            update.message.reply_text("Radius must be less than 25km.")
            return

        create_map(user.latitude, user.longitude, new_radius)

        db.set_user_radius(user_id, new_radius)
        update.message.reply_photo(open("map.png", "rb"), caption=f"Detection radius set to {new_radius}km.")

    except ValueError:
        update.message.reply_text("Invalid radius. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting radius: ")
        logger.exception(e)


def altitude(update, context):
    user_id = update.message.from_user.id

    # check if user is registered
    user = db.get_user(user_id)
    if user is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
        return

    # when no args are passed, return current radius
    if len(update.message.text.split(" ")) == 1:
        user_altitude_min_m = user.altitude_min_m
        user_altitude_max_m = user.altitude_max_m
        update.message.reply_text(f"Current altitude bounds:\n\n"
                                  f"🛬 Min: {user_altitude_min_m}m\n"
                                  f"🛫 Max: {user_altitude_max_m}m\n\n"
                                  f"You can change it with /altitude <min> <max> or /altmin <min> or /altmax <max>.")
        return

    # when more than 2 args are passed, return error
    if len(update.message.text.split(" ")) > 3:
        update.message.reply_text("Invalid altitude boundaries. Command must be in the format /altitude <min> <max>.")
        return

    # try to set altitude
    try:
        new_altitude_min_m = int(update.message.text.split(" ")[1].replace("m", ""))
        new_altitude_max_m = int(update.message.text.split(" ")[2].replace("m", ""))

        if new_altitude_min_m < 1:
            update.message.reply_text("Altitude must be at least 1m.")
            return

        if new_altitude_max_m > 100_000:
            update.message.reply_text("Altitude must be less than 100000m.")
            return

        db.set_user_altitude_min_m(user_id, new_altitude_min_m)
        db.set_user_altitude_max_m(user_id, new_altitude_max_m)

        update.message.reply_text(f"Altitude bounds set to:\n\n"
                                  f"🛬 Min: {new_altitude_min_m}m\n"
                                  f"🛫 Max: {new_altitude_max_m}m"
                                  )

    except ValueError:
        update.message.reply_text("Invalid altitude. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting altitude: ")
        logger.exception(e)


def altmin(update, context):
    user_id = update.message.from_user.id

    # check if user is registered
    user = db.get_user(user_id)
    if user is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
        return

    # when no args are passed, return current min altitude
    if len(update.message.text.split(" ")) == 1:
        user_altitude_min_m = user.altitude_min_m
        update.message.reply_text(f"Current min altitude: {user_altitude_min_m}m.\n"
                                  f"You can change it with /altmin <min>.")
        return

    # when more than 1 args is passed, return an error
    if len(update.message.text.split(" ")) > 2:
        update.message.reply_text("Invalid min altitude. Command must be in the format /altmin <min>.")
        return

    # try to set altitude
    try:
        new_altitude_min_m = int(update.message.text.split(" ")[1].replace("m", ""))

        if new_altitude_min_m < 1:
            update.message.reply_text("Min altitude must be at least 1m.")
            return

        db.set_user_altitude_min_m(user_id, new_altitude_min_m)

        update.message.reply_text(f"Min altitude set to {new_altitude_min_m}m.")

    except ValueError:
        update.message.reply_text("Invalid altitude. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting altitude: ")
        logger.exception(e)


def altmax(update, context):
    user_id = update.message.from_user.id

    # check if user is registered
    user = db.get_user(user_id)
    if user is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
        return

    # when no args are passed, return current max altitude
    if len(update.message.text.split(" ")) == 1:
        user_altitude_max_m = user.altitude_max_m
        update.message.reply_text(f"Current max altitude: {user_altitude_max_m}m.\n"
                                  f"You can change it with /altmax <max>.")
        return

    # when more than 1 args is passed, return an error
    if len(update.message.text.split(" ")) > 2:
        update.message.reply_text("Invalid max altitude. Command must be in the format /altmax <max>.")
        return

    # try to set altitude
    try:
        new_altitude_max_m = int(update.message.text.split(" ")[1].replace("m", ""))

        if new_altitude_max_m > 100_000:
            update.message.reply_text("Max altitude must be less than 100000m.")
            return

        db.set_user_altitude_max_m(user_id, new_altitude_max_m)

        update.message.reply_text(f"Max altitude set to {new_altitude_max_m}m.")

    except ValueError:
        update.message.reply_text("Invalid altitude. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting altitude: ")
        logger.exception(e)


if __name__ == '__main__':
    thread = threading.Thread(target=check_flights_for_users_threaded)
    thread.start()

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.location, set_location))

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("radius", radius))
    dispatcher.add_handler(CommandHandler("altitude", altitude))
    dispatcher.add_handler(CommandHandler("altmin", altmin))
    dispatcher.add_handler(CommandHandler("altmax", altmax))

    # dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    updater.start_polling()

    updater.idle()
