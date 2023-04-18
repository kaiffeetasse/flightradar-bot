import requests
from FlightRadar24.api import FlightRadar24API
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


if __name__ == '__main__':
    # flight_infos = get_flight_infos("2ff0fd74")
    #
    # if "images" in flight_infos["aircraft"] and flight_infos["aircraft"]["images"] is not None:
    #     images = flight_infos["aircraft"]["images"]
    #
    #     if "large" in images:
    #         image_src = images["large"][0]["src"]
    #         print(image_src)

    fr_api = FlightRadar24API()
    info = fr_api.get_flights(registration="N363UP")
    print(info)
