"""Module for composing maps."""
from __future__ import annotations

import logging
from glob import glob
import os
from PIL import Image


class Composer:
    """Class representing a composition of maps."""

    _maps = dict[str, dict[str, Image.Image]]

    def __init__(
        self,
        source_folder: str = "maps",
        dest_folder: str = "composed",
    ) -> Composer:
        """Initialise a Compose object."""
        logging.info(
            f"Creating Compose object with source folder {source_folder}"
            f" and destination folder {dest_folder}"
        )
        self._source_folder = source_folder
        self._dest_folder = dest_folder
        self._maps = self._loadMaps(self._source_folder)

    def _loadMaps(self, source_folder: str) -> dict[str, list[Image.Image]]:
        """Load maps from source folder."""
        maps: dict[str, list[Image.Image]] = dict()
        logging.debug(f"Loading maps from {source_folder}")

        for filename in glob(f"{source_folder}/*.png"):
            city, style, *_ = (
                filename.split("/")[-1].split(".")[0].replace("_", " ").split("-")
            )
            logging.debug(f"Found map for {city} in style {style}")
            if style not in maps:
                maps[style] = dict()

            maps[style][city] = Image.open(filename)

        return maps

    def compose(self, style: str, cities: list[str], sort_cities: bool = False) -> str:
        """Compose a map from a list of cities.

        Args:
            style (str): style to use
            cities (list[str]): cities to compose

        Returns:
            str: path to composed map
        """
        if style not in self.styles:
            logging.error(f"Style {style} not found in {self.styles}")
            raise ValueError(f"Style {style} not found in {self.styles}")

        cols = int(len(cities) ** 0.5)

        if cols**2 != len(cities):
            logging.error(
                f"Number of cities ({len(cities)}) "
                f"does not match number of columns ({cols})"
            )
            raise ValueError(
                f"Number of cities ({len(cities)}) "
                f"does not match number of columns ({cols})"
            )

        cities = [c.title() for c in cities]
        if sort_cities:
            cities.sort()

        logging.info(f"Composing map for {cities} in style {style}")

        maps = [self._maps[style][city] for city in cities]

        out_size = max(m.width for m in maps)

        logging.debug(f"Output size: {out_size}x{out_size}")
        out_image = Image.new("RGB", (out_size * cols, out_size * cols))

        for i, m in enumerate(maps):
            x = i % cols
            y = i // cols

            logging.debug(f"Composing map {i} at ({x}, {y})")
            out_image.paste(m, (x * out_size, y * out_size))

        if not os.path.exists(self._dest_folder):
            os.makedirs(self._dest_folder)

        out_folder = f"{self._dest_folder}/{style.lower()}"
        if not os.path.exists(out_folder):
            os.makedirs(out_folder)

        out_path = f"{out_folder}/{'-'.join(cities).lower()}.png"
        out_image.save(out_path)
        logging.info(f"Saved composed map to {out_path}")
        return out_path

    @property
    def styles(self) -> list[str]:
        """Return a list of styles."""
        return list(self._maps.keys())

    @property
    def cities(self) -> list[str]:
        """Return a list of cities."""
        return list(set(city for style in self._maps.values() for city in style.keys()))
