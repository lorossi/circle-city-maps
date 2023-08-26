from __future__ import annotations

import logging
import os
import random
from datetime import datetime
from glob import glob

from PIL import Image, ImageDraw, ImageFont, ImageOps

from modules.nominatim import NominatimCity
from modules.osm import OSM
from modules.overpass import Node, OverpassElement


class CityMap:
    #! TODO: add border as a derker color of the fill for each building
    #! TODO: create antialiased circle around the city
    _osm: OSM
    _buildings: list[OverpassElement]
    _buildings_bbox: tuple[float, float, float, float]
    _city_name: str
    _city: NominatimCity

    _background_color: str = "#F1E3BC"
    _fonts_dir: str = "fonts"
    _text_color = "#0F0F0F"
    _palette: list[str] = [
        "#23827e",
        "#f99c3d",
        "#ec3c51",
    ]

    def __init__(self, city_name: str) -> CityMap:
        self._osm = OSM()
        self._city_name = city_name

    def _normalizeCoordinate(
        self,
        node: Node,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        x = (node.lon - self._buildings_bbox[1]) / (
            self._buildings_bbox[3] - self._buildings_bbox[1]
        )
        y = (node.lat - self._buildings_bbox[0]) / (
            self._buildings_bbox[2] - self._buildings_bbox[0]
        )

        return int(x * width), int(y * height)

    def load(self, radius: int = 1000):
        logging.info(f"Loading city {self._city_name}")
        self._city = self._osm.getCity(self._city_name)
        logging.info(f"Loading buildings around {self._city}, radius {radius}m")
        self._buildings = self._osm.getBuildings(self._city, radius=radius)
        logging.info("Finding buildings bounding box")
        self._buildings_bbox = (
            min([building.boundingbox[0] for building in self._buildings]),
            min([building.boundingbox[1] for building in self._buildings]),
            max([building.boundingbox[2] for building in self._buildings]),
            max([building.boundingbox[3] for building in self._buildings]),
        )
        logging.info(f"Found buildings bounding box {self._buildings_bbox}")
        return len(self._buildings)

    def _drawBuildings(self, width: int, height: int, scl: float) -> Image.Image:
        city_img = Image.new("RGB", (width, height), color=self._background_color)
        city_draw = ImageDraw.Draw(city_img)

        logging.info("Drawing buildings")

        for building in self._buildings:
            normalized_nodes = [
                self._normalizeCoordinate(nodes, width=width, height=height)
                for nodes in building.nodes
            ]

            fill = random.choice(self._palette)
            city_draw.polygon(
                xy=normalized_nodes,
                fill=fill,
                outline="black",
            )

        # flip the image to account for the fact that PIL uses (0, 0)
        # as the top left corner, while OSM uses (0, 0) as the bottom left corner
        if self._city.lat > 0:
            logging.info("Flipping image")
            city_img = ImageOps.flip(city_img)
        if self._city.lon < 0:
            logging.info("Mirroring image")
            city_img = ImageOps.mirror(city_img)

        # resize the image to the desired size
        new_w, new_h = int(width * scl), int(height * scl)
        logging.info(f"Resizing image to {new_w}x{new_h}")
        city_img = city_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return city_img

    def _createImage(
        self, width: int, height: int, bottom_ratio: float, city_img: Image.Image
    ) -> Image.Image:
        logging.info("Creating image")
        img = Image.new("RGB", (width, height), color=self._background_color)
        img_draw = ImageDraw.Draw(img)

        # calculate the position of the city image
        dx = int((width - city_img.width) / 2)
        dy = int((height - city_img.height) * (1 - bottom_ratio))

        # create a mask for the city image
        mask = Image.new("L", (city_img.width, city_img.height), color=0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse(
            (
                0,
                0,
                city_img.width,
                city_img.height,
            ),
            fill=255,
        )

        # paste the city image into the final image
        img.paste(
            im=city_img,
            box=(dx, dy),
            mask=mask,
        )

        # draw a circle around the city
        img_draw.ellipse(
            (
                dx,
                dy,
                dx + city_img.width,
                dy + city_img.height,
            ),
            outline=self._text_color,
            width=2,
        )

        # draw the city name
        bottom_space = height - dy - city_img.height
        font_size = int(bottom_space / 2)
        font = self._loadFont(size=font_size)
        anchor = "mm"
        img_draw.text(
            (
                width / 2,
                height - bottom_space / 2,
            ),
            text=self._city_name.upper(),
            fill=self._text_color,
            font=font,
            anchor=anchor,
        )

        return img

    def _saveImage(self, img: Image.Image, path: str | None) -> str:
        out_dir = os.path.dirname(path)
        if out_dir and not os.path.exists(out_dir):
            logging.info(f"Creating directory {out_dir}")
            os.makedirs(out_dir)

        if path is None:
            timestamp = int(datetime.now().timestamp() * 1000)
            path = f"{self._out_dir}/{self._city_name}-{timestamp}.png"
        elif not path.endswith(".png"):
            path = f"{path}.png"

        logging.info(f"Saving image to {path}")
        img.save(path)
        return path

    def _loadFont(self, size: int) -> ImageFont:
        fonts = glob(f"{self._fonts_dir}/*.ttf")
        if not fonts:
            raise RuntimeError(f"No .ttf fonts found in {self._fonts_dir}")

        return ImageFont.truetype(fonts[0], size=size)

    def draw(
        self,
        width: int = 1000,
        height: int = 1000,
        scl: float = 0.7,
        bottom_ratio: float = 0.8,
        path: str | None = None,
        seed: int | None = None,
    ) -> str:
        logging.info(f"Drawing map {width}x{height}")

        if seed is None:
            seed = int(datetime.now().timestamp() * 1000)
        logging.info(f"Initializing random with seed {seed}")
        random.seed(seed)

        # draw the buildings
        city_img = self._drawBuildings(width, height, scl)
        # create the final image
        final_img = self._createImage(width, height, bottom_ratio, city_img)
        # save the image
        path = self._saveImage(final_img, path)
