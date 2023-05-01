import sys
import requests
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_flight_infos(flight_id):
    url = "https://data-live.flightradar24.com/clickhandler/?version=1.5&flight=" + flight_id

    response = requests.request("GET", url)

    try:
        return response.json()
    except Exception as e:
        logger.exception(e)
        return None


def get_image_by_flight_id(flight_id):
    flight_infos = get_flight_infos(flight_id)

    if flight_infos is None or "aircraft" not in flight_infos:
        return None

    if "images" in flight_infos["aircraft"] and flight_infos["aircraft"]["images"] is not None:
        images = flight_infos["aircraft"]["images"]

        if "large" in images:
            image_src = images["large"][0]["src"]
            return image_src

    return None


def get_image_by_registration_number(registration_number):
    url = "https://www.jetphotos.com/api/json/quicksearch.php?term=" + registration_number

    response = requests.request("GET", url)

    try:
        res_json = response.json()
        cdn_full_url = "https://cdn.jetphotos.com/full/" + res_json[0]["filename"]
        return cdn_full_url
    except IndexError:
        logger.info("No image found for registration number: " + registration_number)
    except Exception as e:
        logger.error("Error while getting image by registration number: " + str(e))
        logger.exception(e)

    return None


def __get_distance(lat1, lon1, lat2, lon2):
    from math import sin, cos, sqrt, atan2, radians
    # Approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def get_airport_by_lat_long(latitude, longitude):
    from FlightRadar24.api import FlightRadar24API
    fr_api = FlightRadar24API()
    airports = fr_api.get_airports()

    most_nearby_airport = None
    most_nearby_airport_distance_km = sys.maxsize

    for airport in airports:
        airport_latitude = airport["lat"]
        airport_longitude = airport["lon"]

        airport_distance = __get_distance(latitude, longitude, airport_latitude, airport_longitude)

        if airport_distance < most_nearby_airport_distance_km:
            most_nearby_airport = airport
            most_nearby_airport_distance_km = airport_distance

    return most_nearby_airport, most_nearby_airport_distance_km


def search_by_query(query):
    logger.info("Searching for query: " + query)

    url = "https://www.flightradar24.com/v1/search/web/find?query=" + query + "&limit=100&type=aircraft"

    response = requests.request("GET", url)

    res_json = response.json()

    aircrafts = []
    for result in res_json['results']:
        aircrafts.append(result)

    logger.info("Found " + str(len(aircrafts)) + " aircrafts")

    return aircrafts


if __name__ == '__main__':
    # get_image_by_registration_number("HB-ZRQ")
    # airport, distance = get_airport_by_lat_long(48.406355, 7.949271)
    # print("nearby: " + str(airport))
    # print("distance: " + str(distance) + "km")

    aircrafts = search_by_query("HB-ZRQ")
    print(aircrafts)
