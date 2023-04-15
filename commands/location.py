import db
from utils import map


def set_location(update, context):
    user_id = update.message.from_user.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude

    user = db.set_user_location(user_id, latitude, longitude)
    user_radius_km = user.radius_km

    map.create_map(latitude, longitude, user_radius_km)

    update.message.reply_photo(open('map.png', 'rb'), caption="Location set! Radius: " + str(user_radius_km) + "km")
