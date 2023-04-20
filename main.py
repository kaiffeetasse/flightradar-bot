import threading
import time
from FlightRadar24.api import FlightRadar24API
from dotenv import load_dotenv
import os
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    MessageHandler, Filters, CommandHandler, CallbackQueryHandler,
)
import db
import flightradar24_api
from commands import (
    altitude, altmax, altmin, location, radius, start, stop
)
from utils import map

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

    if image_src is None:
        updater.bot.send_message(user_id, message, reply_markup=track_button)
    else:
        updater.bot.send_photo(user_id, image_src, caption=message, reply_markup=track_button)


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
                altitude_min_m = user.altitude_min_m
                altitude_max_m = user.altitude_max_m

                if user_flights.get(user_id) is None:
                    user_flights[user_id] = []
                    user_flight_ids[user_id] = []

                logger.debug(f"Checking for user {user_id} at {latitude}, {longitude}")

                y1, y2, x1, x2 = map.get_y1_y2_x1_x2(latitude, longitude, user_radius)

                new_user_flights = fr_api.get_flights(bounds=f"{y1},{y2},{x1},{x2}")
                new_user_flight_ids = [flight.id for flight in new_user_flights]

                for flight in new_user_flights:

                    logger.debug(f"Checking flight {flight.id} for user {user_id}")

                    if flight.id not in user_flight_ids.get(user_id):

                        altitude_ft = flight.altitude
                        altitude_m = int(altitude_ft * 0.3048)

                        if altitude_m < altitude_min_m or altitude_m > altitude_max_m:
                            continue

                        speed_kt = flight.ground_speed
                        speed_kmh = int(speed_kt * 1.852)

                        msg = "✈ New flight over your location ✈\n\n"
                        msg = msg + f"Aircraft: {flight.callsign} ({flight.aircraft_code})\n"
                        msg = msg + f"Altitude: {altitude_m}m\n"
                        msg = msg + f"Speed: {speed_kmh}km/h\n"
                        msg = msg + f"From: {flight.origin_airport_iata}\n"
                        msg = msg + f"To: {flight.destination_airport_iata}\n"
                        msg = msg + f"Link: https://www.flightradar24.com/{flight.callsign}/{flight.id}"

                        image_src = flightradar24_api.get_image_by_flight_id(flight.id)
                        registration = flight.registration

                        tracking = db.is_aircraft_tracked(user_id, registration)

                        send_message_to_user(user_id, msg, image_src, registration, tracking)
                        time.sleep(1)

                        if user_flight_ids.get(user_id) is None:
                            user_flight_ids[user_id] = []

                        user_flight_ids[user_id].append(flight.id)

                for flight_id in user_flight_ids.get(user_id):
                    if flight_id not in new_user_flight_ids:
                        user_flight_ids[user_id].remove(flight_id)

        except Exception as e:
            logger.error("Error while checking for flights: " + str(e))
            logger.exception(e)

        time.sleep(5)


def get_aircraft_states_for_all_users():
    aircraft_status = {}

    for user in db.get_users():
        user_id = user.telegram_id
        tracked_aircrafts = db.get_tracked_aircraft_registrations_by_telegram_id(user_id)

        for aircraft in tracked_aircrafts:

            flights = fr_api.get_flights(registration=aircraft["aircraft_registration"])

            if flights is None or len(flights) == 0:
                aircraft_status[aircraft["aircraft_registration"]] = None
                continue
            else:
                aircraft_status[aircraft["aircraft_registration"]] = flights[0]

    return aircraft_status


def check_tracked_flights_for_users_threaded():
    aircraft_states = get_aircraft_states_for_all_users()

    while True:

        try:

            new_aircraft_states = get_aircraft_states_for_all_users()

            for user in db.get_users():

                user_id = user.telegram_id
                tracked_aircrafts = db.get_tracked_aircraft_registrations_by_telegram_id(user_id)

                for aircraft in tracked_aircrafts:

                    aircraft_registration = aircraft["aircraft_registration"]

                    new_flight_status = new_aircraft_states.get(aircraft_registration) is None
                    flight_status = aircraft_states.get(aircraft_registration) is None

                    if new_flight_status == flight_status:
                        continue

                    msg = "✈ Tracked flight Update ✈\n\n"
                    msg = msg + f"Aircraft: {aircraft_registration}\n"
                    msg = msg + f"Old status: {aircraft_states.get(aircraft_registration)}\n"
                    msg = msg + f"New status: {new_aircraft_states.get(aircraft_registration)}\n"

                    image_url = flightradar24_api.get_image_by_registration_number(aircraft_registration)

                    send_message_to_user(user_id, msg, image_url, aircraft_registration, True)
                    time.sleep(1)

            aircraft_states = new_aircraft_states

        except Exception as e:
            logger.error("Error while checking for tracked flights: " + str(e))
            logger.exception(e)

        time.sleep(30)


def handle_message(update, context):
    print(update.message.text)
    update.message.reply_text("test")


if __name__ == '__main__':
    thread1 = threading.Thread(target=check_flights_for_users_threaded)
    thread1.start()

    thread2 = threading.Thread(target=check_tracked_flights_for_users_threaded)
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
