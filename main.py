import logging
from bs4 import BeautifulSoup
import requests
import re
from PIL import Image

logger = logging.getLogger(__name__)

LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"


def download_jpeg_image(url, path: str) -> None:
    response = requests.get(url)

    # If the request is not successful (response code is not 200), log the failure and return early
    if response.status_code != 200:
        logger.error("Failed to download image from URL: %s", url)
        return

    with open(path, 'wb') as f:
        f.write(response.content)


def get_high_resolution_album_cover_url(url):
    # Use a regular expression to extract the values
    m = re.search(r'\d+x\d+', url)

    if not m:
        logger.warning("No match found in URL: %s", url)
        return None

    # Replace the values with 10000x10000
    new_url = re.sub(m.group(0), "10000x10000", url)

    # Return the new URL
    return new_url


def download_cover_art(url: str, path: str) -> None:
    # Send HTTP request to the URL
    response = requests.get(url)

    # If the request is not successful (response code is not 200), return early
    if response.status_code != 200:
        logger.error("Failed to extract the image URL from the provided URL: %s", url)
        return

    # Parse the response HTML using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the div element with the "artwork-component" class
    div = soup.find('div', class_='artwork-component')
    # Find the picture element within the div
    jpeg_source = div.find('source', {'type': 'image/jpeg'})

    # Extract the image URL from the srcset attribute
    image_urls = jpeg_source['srcset'].split(',')
    # Get the last URL with the width specification
    image_url_with_width = image_urls[-1]
    # Extract the URL
    image_url = image_url_with_width.split(" ")[0]

    # Get an URL pointing to the highest quality version of the album cover
    hq_image_url = get_high_resolution_album_cover_url(image_url)

    # Actually download and save the image to the filesystem
    logging.info("Downloading image from URL: %s", hq_image_url)
    download_jpeg_image(hq_image_url, path)


def format_cover_size(number):
    # If the number can be rounded to thousands without loss,
    # return it as a string with the format 1k
    if number % 1000 == 0:
        return f"{number / 1000:.0f}k"

    # If the number can be rounded to hundreds without loss,
    # return it as a string with the format 1.5k
    if number % 100 == 0:
        return f"{number / 1000:.1f}k"

    # Otherwise, return the number as is
    return str(number)


def square_cover_image(path):
    with Image.open(path) as img:
        width, height = img.size

        # Calculate the maximum of width and height and use that for both dimensions in resize_size
        side_size = max(width, height)

        # Print the dimensions of the downloaded image in the format {width}x{height}
        logger.info("Image dimensions: %sx%s", width, height)
        logger.info("Cover size: %s", format_cover_size(side_size))

        # Check if we actually have to resize
        if width == height:
            return

        resize_size = (side_size, side_size)

        # Resize the image
        img = img.resize(resize_size, Image.Resampling.BICUBIC)

        logger.info("Image resized to %sx%s", side_size, side_size)

        # Save the resized image
        img.save(path)


def init_logging():
    """Initialize the logging for this module."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def main():
    init_logging()
    # Prompt user for an URL
    url = input("Enter the URL of the album cover art: ")
    # Call download_cover_art with the entered URL
    download_cover_art(url, "cover.jpeg")
    # Resize the cover to be square
    square_cover_image("cover.jpeg")


if __name__ == "__main__":
    main()
