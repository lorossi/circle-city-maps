from modules.composer import Composer
import logging


def main():
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

    c = Composer()

    for style in c.styles:
        c.compose(style=style, cities=composition_1)
        c.compose(style=style, cities=composition_2, sort_cities=False)


if __name__ == "__main__":
    main()
