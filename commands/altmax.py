import db
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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
