"""Module for composing maps."""
from __future__ import annotations

import logging
import os
from glob import glob

from PIL import Image, ImageDraw


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

    def _shadeColor(self, source_color: str, shades: int = 4) -> str:
        """Shade a color."""
        logging.debug(f"Shading color {source_color}")
        r, g, b = [
            int(c, 16)
            for c in [source_color[1:3], source_color[3:5], source_color[5:7]]
        ]
        logging.debug(f"RGB: {r}, {g}, {b}")
        r, g, b = (int(c / shades) for c in [r, g, b])
        logging.debug(f"Shaded RGB: {r}, {g}, {b}")
        return f"#{r:02x}{g:02x}{b:02x}"

    def compose(
        self,
        style: str,
        cities: list[str],
        scl: float = 0.9,
        sort_cities: bool = False,
        frame_width: int = 2,
    ) -> str:
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

        if frame_width % 2 != 0:
            logging.error(f"Frame width ({frame_width}) must be even")
            raise ValueError(f"Frame width ({frame_width}) must be even")

        cities = [c.title() for c in cities]
        if sort_cities:
            cities.sort()

        logging.info(f"Composing map for {cities} in style {style}")

        maps = [self._maps[style][city] for city in cities]

        background_color = maps[0].getpixel((0, 0))
        logging.debug(f"Background color: {background_color}")
        frame_color = self._shadeColor(background_color, shades=2)

        out_size = max(m.width for m in maps)

        logging.debug(f"Output size: {out_size}x{out_size}")
        out_image = Image.new(
            "RGB", (out_size * cols, out_size * cols), color=background_color
        )
        out_draw = ImageDraw.Draw(out_image)

        for i, m in enumerate(maps):
            x = i % cols
            y = i // cols

            logging.debug(f"Resizing map {i} to {out_size * scl}x{out_size * scl}")
            m = m.resize((int(out_size * scl), int(out_size * scl)))
            dx = (out_size - m.width) // 2
            dy = (out_size - m.height) // 2

            logging.debug(f"Composing map {i} at ({x}, {y})")
            out_image.paste(m, (x * out_size + dx, y * out_size + dy))
            # draw 2px frame
            out_draw.rectangle(
                [
                    (
                        x * out_size + dx - frame_width // 2,
                        y * out_size + dy - frame_width // 2,
                    ),
                    (
                        x * out_size + dx + m.width + frame_width // 2,
                        y * out_size + dy + m.height + frame_width // 2,
                    ),
                ],
                outline=frame_color,
            )

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
        return sorted(list(self._maps[self.styles[0]].keys()))
