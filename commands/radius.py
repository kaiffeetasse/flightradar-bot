import db
from utils import map
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


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
        map.create_map(user.latitude, user.longitude, user_radius)

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

        map.create_map(user.latitude, user.longitude, new_radius)

        db.set_user_radius(user_id, new_radius)
        update.message.reply_photo(open("map.png", "rb"), caption=f"Detection radius set to {new_radius}km.")

    except ValueError:
        update.message.reply_text("Invalid radius. Please send a number.")
    except Exception as e:
        update.message.reply_text(f"Sorry, something went wrong. Please try again.")
        logger.error("Error setting radius: ")
        logger.exception(e)