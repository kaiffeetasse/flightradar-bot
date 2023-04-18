import requests


def get_flight_infos(flight_id):
    url = "https://data-live.flightradar24.com/clickhandler/?version=1.5&flight=" + flight_id

    response = requests.request("GET", url)

    return response.json()


def get_image_by_flight_id(flight_id):
    flight_infos = get_flight_infos(flight_id)

    if "images" in flight_infos["aircraft"] and flight_infos["aircraft"]["images"] is not None:
        images = flight_infos["aircraft"]["images"]

        if "large" in images:
            image_src = images["large"][0]["src"]
            return image_src

    return None


if __name__ == '__main__':
    flight_infos = get_flight_infos("2ff0fd74")

    if "images" in flight_infos["aircraft"] and flight_infos["aircraft"]["images"] is not None:
        images = flight_infos["aircraft"]["images"]

        if "large" in images:
            image_src = images["large"][0]["src"]
            print(image_src)
