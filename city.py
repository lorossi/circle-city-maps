"""Main file for the city map generator."""
import logging
import os

from modules.city_map import CityMap


def main(argv: list[str]):
    """Script entry point."""
    debug_mode = "--debug" in argv
    if debug_mode in argv:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, in %(funcName)s) "
            "- %(message)s"
        ),
    )

    cities = [
        "Andorra la Vella",
        "Athens",
        "Berlin",
        "Bratislava",
        "Brussels",
        "Bucharest",
        "Budapest",
        "Copenhagen",
        "Den Haag",
        "Dublin",
        "Helsinki",
        "Lisbon",
        "Ljubljana",
        "London",
        "Luxembourg",
        "Madrid",
        "Nicosia",
        "Oslo",
        "Paris",
        "Prague",
        "Riga",
        "Rome",
        "Sofia",
        "Stockholm",
        "Tallinn",
        "Vaduz",
        "Valletta",
        "Vienna",
        "Vilnius",
        "Warsaw",
        "Zagreb",
    ]

    logging.info("Generating city maps...")
    for city in cities:
        logging.info(f"Generating map for {city}")
        city_map = CityMap(city)
        city_map.load(radius=1000, random_fill=debug_mode)
        for style in city_map.styles:
            logging.info(f"Generating map for {city} in style {style}")
            path = city_map.draw(width=5000, height=5000, style=style, scl=0.8)
            logging.info(f"Map for {city} in style {style} saved to {path}")

    logging.info("Done!")


if __name__ == "__main__":
    main(os.sys.argv[1:])
