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
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "DELETE FROM user WHERE telegram_id = %s"
    val = (telegram_id,)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def set_user_location(telegram_id, latitude, longitude):
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    # insert or update
    sql = "INSERT INTO user (telegram_id, latitude, longitude) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE latitude = %s, longitude = %s"
    val = (telegram_id, latitude, longitude, latitude, longitude)
    mycursor.execute(sql, val)

    mydb.commit()

    return mycursor.rowcount


def set_user_radius(telegram_id, radius_km):
    mydb = get_db()
    mycursor = mydb.cursor(dictionary=True, buffered=True)

    sql = "UPDATE user SET radius_km = %s WHERE telegram_id = %s"
    val = (radius_km, telegram_id)
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
    for user in result:
        users.append(User(user.get("telegram_id"), user.get("latitude"), user.get("longitude"), user.get("radius_km")))

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

    # convert to User object
    user = User(result.get("telegram_id"), result.get("latitude"), result.get("longitude"), result.get("radius_km"))

    return user


if __name__ == '__main__':
    # set_user_location(123, 1.23456789, 9.87654321)

    user = get_users()[0]
    print(user)
