import time
from FlightRadar24.api import FlightRadar24API
from dotenv import load_dotenv
import logging
import db
from api import flightradar24_api, planepictures_api
from api import telegram_api

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

fr_api = FlightRadar24API()

# set log level to DEBUG
logger.setLevel(logging.DEBUG)


def get_aircraft_states_for_all_users():
    logger.debug("Checking tracked flights for users...")
    aircraft_states = {}

    tracked_aircrafts = db.get_all_tracked_aircrafts()

    for aircraft in tracked_aircrafts:

        flights = fr_api.get_flights(registration=aircraft["aircraft_registration"])

        if flights is None or len(flights) == 0:
            aircraft_states[aircraft["aircraft_registration"]] = None
        else:
            aircraft_states[aircraft["aircraft_registration"]] = flights[0]
            break

    logger.debug("Aircraft states loaded")

    return aircraft_states


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

                    flight_status = aircraft_states.get(aircraft_registration) is None
                    new_flight_status = new_aircraft_states.get(aircraft_registration) is None

                    if new_flight_status == flight_status:
                        continue

                    logger.debug("Flight status of " + aircraft_registration + " changed")

                    aircraft = new_aircraft_states.get(aircraft_registration)

                    if aircraft is None:
                        status_msg = "Landed"

                        latitude = aircraft_states.get(aircraft_registration).latitude
                        longitude = aircraft_states.get(aircraft_registration).longitude
                    else:
                        status_msg = "Started"

                        latitude = aircraft.latitude
                        longitude = aircraft.longitude

                    logger.debug("new status_msg: " + status_msg)

                    most_nearby_airport, most_nearby_airport_distance_km = flightradar24_api \
                        .get_airport_by_lat_long(latitude, longitude)

                    # probably a faulty status update
                    if most_nearby_airport_distance_km > 3:
                        logger.debug("Most nearby airport is too far away, skipping")
                        logger.debug("most_nearby_airport: " + str(most_nearby_airport))
                        logger.debug("most_nearby_airport_distance_km: " + str(most_nearby_airport_distance_km))
                        continue

                    # skip aircrafts on ground
                    if aircraft is not None and aircraft.ground_speed < 30:
                        logger.debug("Aircraft is on ground, skipping")
                        continue

                    # build message
                    status_msg = status_msg + " (" + most_nearby_airport['name'] + ")"

                    msg = "✈ Tracked flight Update ✈\n\n"
                    msg = msg + f"Aircraft: {aircraft_registration}\n"
                    msg = msg + f"Status: {status_msg}"

                    # add url if available
                    if aircraft is not None:
                        if aircraft.callsign is not None and aircraft.id is not None:
                            msg = msg + f"\nLink: https://www.flightradar24.com/{aircraft.callsign}/{aircraft.id}"

                    # search for image
                    image_urls = [flightradar24_api.get_image_by_registration_number(aircraft_registration)]

                    if image_urls[0] is None:
                        image_urls = planepictures_api.get_image_by_registration_number(aircraft_registration)

                    image_urls.append(None)  # ensure that the loop will be executed at least once (msg without image)

                    for image_url in image_urls:
                        try:
                            telegram_api.send_message_to_user(user_id, msg, image_url, aircraft_registration, True)
                            logger.debug("Tracking message sent to user: " + str(user_id))
                            break
                        except Exception as e:
                            logger.error("Error while sending message to user: " + str(e))

                    # update aircraft state only if message was sent
                    aircraft_states[aircraft_registration] = aircraft

                    time.sleep(1)

            aircraft_states = new_aircraft_states  # TODO remove?

        except Exception as e:
            logger.error("Error while checking for tracked flights: " + str(e))
            logger.exception(e)

        time.sleep(30)
