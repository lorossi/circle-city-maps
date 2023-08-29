"""Module containing the script to compose multiple maps."""
import logging

from modules.composer import Composer


def main():
    """Script entry point."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, in %(funcName)s) "
            "- %(message)s"
        ),
    )

    composition_1 = ["Paris", "Berlin", "Rome", "Madrid"]
    composition_2 = [
        "Berlin",
        "Madrid",
        "Rome",
        "Bucharest",
        "Paris",
        "Vienna",
        "Warsaw",
        "Budapest",
        "Prague",
    ]
    composition_3 = ["Milan", "Turin", "Florence", "Rome"]

    c = Composer()

    for style in c.styles:
        c.compose(style=style, cities=composition_1)
        c.compose(style=style, cities=composition_2, sort_cities=False)
        c.compose(style=style, cities=composition_3)


if __name__ == "__main__":
    main()
