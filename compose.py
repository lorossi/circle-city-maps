"""Module containing the script to compose multiple maps."""
import logging

from modules.composer import Composer


def main():
    """Script entry point."""
    logging.basicConfig(
        level=logging.INFO,
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
        c.composeCities(style=style, cities=composition_1, frame_width=0)
        c.composeCities(
            style=style,
            cities=composition_2,
            frame_width=0,
            sort_cities=False,
        )
        c.composeCities(style=style, cities=composition_3, frame_width=0)


if __name__ == "__main__":
    main()
