import argparse
import logging

from modules.city_map import CityMap


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate city maps.")

    p.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )

    p.add_argument(
        "-c",
        "--city",
        type=str,
        help="City to generate map for.",
    )

    p.add_argument(
        "-s",
        "--style",
        type=str,
        help="Style to use.",
    )

    p.add_argument(
        "-r",
        "--radius",
        type=int,
        help="Radius of the map.",
    )

    p.add_argument(
        "-f",
        "--random-fill",
        action="store_true",
        help="Randomly fill the map.",
    )

    p.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file.",
    )

    p.add_argument(
        "--width",
        type=int,
        help="Width of the map.",
        default=1000,
    )

    p.add_argument(
        "--height",
        type=int,
        help="Height of the map.",
        default=1000,
    )

    p.add_argument(
        "-l",
        "--list-styles",
        action="store_true",
        help="List available styles.",
    )

    p.add_argument(
        "--seed",
        type=int,
        help="Seed for random generation.",
        default=None,
    )

    return p.parse_args()


def main():
    args = parse_args()

    if args.debug:
        level = logging.DEBUG
        format = (
            (
                "%(asctime)s - %(levelname)s - %(module)s (%(lineno)d, "
                "in %(funcName)s - %(message)s"
            ),
        )
    else:
        level = logging.INFO
        format = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=format)

    if args.list_styles:
        print("\n".join(CityMap.getStyles()))
        return

    if not args.city:
        logging.error("No city specified.")
        return

    if not args.style:
        logging.error("No style specified.")
        return

    city_map = CityMap(args.city)
    city_map.load(
        radius=args.radius,
        random_fill=args.random_fill,
    )

    city_map.draw(
        style=args.style,
        path=args.output,
        width=args.width,
        height=args.height,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
