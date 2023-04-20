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

    if flight_infos is None:
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

    res_json = response.json()

    cdn_full_url = "https://cdn.jetphotos.com/full/" + res_json[0]["filename"]

    return cdn_full_url


if __name__ == '__main__':
    get_image_by_registration_number("HB-ZRQ")
