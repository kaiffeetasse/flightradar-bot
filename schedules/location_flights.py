import time
from FlightRadar24.api import FlightRadar24API
from dotenv import load_dotenv
import logging
import db
from api import flightradar24_api
from api import telegram_api
from utils import map

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

fr_api = FlightRadar24API()


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

                        telegram_api.send_message_to_user(user_id, msg, image_src, registration, tracking)
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
