import os
import time
import mysql.connector
import logging
from dotenv import load_dotenv
from user import User

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

DB_URL = os.environ.get("DB_URL")
DB_DATABASE = os.environ.get("DB_DATABASE")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT")


def get_db():
    max_retry_count = 10
    retry_counter = 0
    retry_seconds = 30

    while retry_counter <= max_retry_count:
        try:
            logger.debug("trying connect to db...")

            mydb = mysql.connector.connect(
                host=DB_URL,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE
            )

            logger.debug("connection successfull!")
            return mydb
        except Exception as e:
            logger.exception(e)
            logger.error("could not connect to db! trying again in " + str(retry_seconds) + " seconds")
            retry_counter = retry_counter + 1
            time.sleep(retry_seconds)

    logger.error("could not establish a connection after " + str(max_retry_count) + " attempts. aborting!")

    return None


def remove_user(telegram_id):
    logger.info("removing user " + str(telegram_id))
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "DELETE FROM user WHERE telegram_id = %s"
    val = (telegram_id,)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def set_user_location(telegram_id, latitude, longitude) -> User:
    logger.info("setting user location for " + str(telegram_id) + " to " + str(latitude) + ", " + str(longitude))

    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    # insert or update
    sql = "INSERT INTO user (telegram_id, latitude, longitude) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE latitude = %s, longitude = %s"
    val = (telegram_id, latitude, longitude, latitude, longitude)
    mycursor.execute(sql, val)

    mydb.commit()

    return get_user(telegram_id)


def set_user_radius(telegram_id, radius_km):
    logger.info("setting user radius for " + str(telegram_id) + " to " + str(radius_km))
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "UPDATE user SET radius_km = %s WHERE telegram_id = %s"
    val = (radius_km, telegram_id)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def set_user_altitude_min_m(telegram_id, altitude_min_m):
    logger.info("setting user altitude min for " + str(telegram_id) + " to " + str(altitude_min_m))
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "UPDATE user SET altitude_min_m = %s WHERE telegram_id = %s"
    val = (altitude_min_m, telegram_id)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def set_user_altitude_max_m(telegram_id, altitude_max_m):
    logger.info("setting user altitude max for " + str(telegram_id) + " to " + str(altitude_max_m))
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "UPDATE user SET altitude_max_m = %s WHERE telegram_id = %s"
    val = (altitude_max_m, telegram_id)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def get_users():
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "SELECT * FROM user"
    mycursor.execute(sql)

    result = mycursor.fetchall()

    # convert to User objects
    users = []
    for user_result in result:
        users.append(map_user_entity(user_result))

    return users


def get_user(telegram_id):
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "SELECT * FROM user WHERE telegram_id = %s"
    val = (telegram_id,)
    mycursor.execute(sql, val)

    result = mycursor.fetchone()

    if result is None:
        return None

    return map_user_entity(result)


def map_user_entity(db_result):
    return User(
        db_result.get("telegram_id"),
        db_result.get("latitude"),
        db_result.get("longitude"),
        db_result.get("radius_km"),
        db_result.get("altitude_min_m"),
        db_result.get("altitude_max_m")
    )


def get_tracked_aircraft_registrations_by_telegram_id(telegram_id):
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "SELECT aircraft_registration FROM tracking WHERE user_telegram_id = %s"
    val = (telegram_id,)
    mycursor.execute(sql, val)

    result = mycursor.fetchall()

    return result


def track_aircraft(telegram_id, registration):
    logger.info("tracking aircraft for " + str(telegram_id) + " with registration " + str(registration))

    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    tracked_aircrafts = get_tracked_aircraft_registrations_by_telegram_id(telegram_id)

    if registration not in tracked_aircrafts:
        # add tracking
        sql = "INSERT INTO tracking (user_telegram_id, aircraft_registration) VALUES (%s, %s)"
        logger.info("tracking aircraft with registration " + str(registration) + " for user " + str(telegram_id))
    else:
        logger.warning("aircraft with registration " + str(registration)
                       + " is already tracked for user " + str(telegram_id))
        return

    val = (telegram_id, registration)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def untrack_aircraft(telegram_id, registration):
    logger.info("untracking aircraft for " + str(telegram_id) + " with registration " + str(registration))

    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "DELETE FROM tracking WHERE user_telegram_id = %s AND aircraft_registration = %s"
    val = (telegram_id, registration)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def is_aircraft_tracked(user_id, registration):
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "SELECT * FROM tracking WHERE user_telegram_id = %s AND aircraft_registration = %s"
    val = (user_id, registration)
    mycursor.execute(sql, val)

    result = mycursor.fetchone()

    if result is None:
        return False

    return True


if __name__ == '__main__':
    # set_user_location(123, 1.23456789, 9.87654321)

    user = get_users()[0]
    print(user)
