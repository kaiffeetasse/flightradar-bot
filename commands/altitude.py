import db
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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
                                  f"You can change it with:\n\n"
                                  f"/altitude <min> <max> or\n"
                                  f"/altmin <min> or\n"
                                  f"/altmax <max>")
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
