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
    c = CityMap("Milano")
    c.load(radius=500)
    c.draw(path="map.png")


if __name__ == "__main__":
    main()
