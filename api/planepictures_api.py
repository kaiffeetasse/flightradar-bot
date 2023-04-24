import bs4
import requests
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def get_image_by_registration_number(aircraft_registration):
    url = "https://www.planepictures.net/v3/search.php?srch=" + aircraft_registration + "&stype=reg"

    response = requests.request("GET", url)
    html = response.text

    soup = bs4.BeautifulSoup(html, "html.parser")

    images = soup.find_all("img")
    image_urls = []

    for image in images:
        img_alt = image.get("alt")

        if img_alt is None:
            continue

        if "Vorschau" in img_alt:
            image_url = image.get("src").replace("_TN", "")

            if image_url is not None and image_url not in image_urls:
                image_urls.append("https://www.planepictures.net" + image_url)

    if len(image_urls) > 0:
        logger.info("Found images for registration number " + aircraft_registration)
        return image_urls

    logger.info("No image found for registration number " + aircraft_registration)
    return []
