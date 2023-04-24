import db
import logging

from api import telegram_api, flightradar24_api, planepictures_api

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def track(update, context):
    user_id = update.message.from_user.id

    # check args
    if len(update.message.text.split(" ")) != 2:
        update.message.reply_text("Invalid arguments. Command must be in the format /track <aircraft_registration>.")
        return

    aircraft_registration = update.message.text.split(" ")[1]

    # check if aircraft_registration is alphanumeric with "-" and > 10 chars
    if not aircraft_registration.replace("-", "").isalnum() or len(aircraft_registration) > 10:
        update.message.reply_text("Invalid aircraft registration. Please try again.")
        return

    tracking = db.is_user_tracking(user_id, aircraft_registration)

    if tracking:
        telegram_api.send_message_to_user(
            user_id,
            f"You are already tracking {aircraft_registration}.",
            None,
            aircraft_registration,
            tracking
        )
        return
    else:
        db.track_aircraft(user_id, aircraft_registration)
        image_urls = [flightradar24_api.get_image_by_registration_number(aircraft_registration)]

        if image_urls[0] is None:
            image_urls = planepictures_api.get_image_by_registration_number(aircraft_registration)

        if len(image_urls) > 0:

            for image_url in image_urls:
                try:
                    telegram_api.send_message_to_user(
                        user_id,
                        f"Tracking of {aircraft_registration} started.",
                        image_url,
                        aircraft_registration,
                        not tracking
                    )
                    return
                except Exception as e:
                    logger.error("Error while sending message to user: " + str(e))

        else:
            telegram_api.send_message_to_user(
                user_id,
                f"Tracking of {aircraft_registration} started.",
                None,
                aircraft_registration,
                not tracking
            )
