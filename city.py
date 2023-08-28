"""Main file for the city map generator."""
import logging

from modules.city_map import CityMap


def main():
    """Script entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, in %(funcName)s) "
            "- %(message)s"
        ),
    )

    cities = [
        "Amsterdam",
        "Andorra la Vella",
        "Athens",
        "Berlin",
        "Bratislava",
        "Brussels",
        "Bucharest",
        "Budapest",
        "Copenhagen",
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

    for city in cities:
        logging.info(f"Generating map for {city}")
        c = CityMap(city)
        c.load(radius=2000)
        for style in c.styles:
            c.draw(width=5000, height=5000, style=style)


if __name__ == "__main__":
    main()
