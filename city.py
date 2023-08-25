import logging

from modules.city_map import CityMap


def main():
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, in %(funcName)s) "
            "- %(message)s"
        ),
    )
    c = CityMap("Milano")
    c.load(radius=1000)
    c.draw()


if __name__ == "__main__":
    main()
