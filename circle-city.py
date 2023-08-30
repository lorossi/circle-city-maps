"""Main file for the city map generator."""
import logging
import sys

from modules.city_map import CityMap


def main(argv: list[str]):
    """Script entry point."""
    debug_mode = "--debug" in argv

    if debug_mode:
        level = logging.DEBUG
        format = (
            "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, in %(funcName)s) "
            "- %(message)s"
        )
    else:
        level = logging.INFO
        format = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format,
    )

    cities = [
        "Berlin",
        "Bucharest",
        "Budapest",
        "Florence",
        "Madrid",
        "Milan",
        "Paris",
        "Prague",
        "Rome",
        "Turin",
        "Vienna",
        "Warsaw",
    ]

    if debug_mode:
        width = 1000
        height = 1000
    else:
        width = 5000
        height = 5000

    logging.info("Generating city maps...")
    for city in cities:
        logging.info(f"Generating map for {city}")
        city_map = CityMap(city)
        city_map.load(radius=1000, random_fill=debug_mode)
        for style in city_map.styles:
            logging.info(f"Generating map for {city} in style {style}")
            path = city_map.draw(width=width, height=height, style=style, scl=0.8)
            logging.info(f"Map for {city} in style {style} saved to {path}")

    logging.info("Done!")


if __name__ == "__main__":
    main(sys.argv)
