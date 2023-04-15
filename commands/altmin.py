import db
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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
