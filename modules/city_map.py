from __future__ import annotations

import logging
import os
import random
from datetime import datetime
from glob import glob

from PIL import Image, ImageDraw, ImageFont, ImageOps

from modules.nominatim import NominatimCity
from modules.osm import OSM
from modules.overpass import Node, Building
from modules.data import Data


class MapBuilding(Data):
    nodes: list[Node]
    neighbors: list[MapBuilding]
    color: str
    outline_color: str

    def borders(self, other: Building) -> bool:
        # two elements border if they share at least two nodes
        return len(set(self.nodes) & set(other.nodes)) >= 2


class CityMap:
    # TODO: add border as a darker color of the fill for each building
    # TODO: create antialiased circle around the city
    # TODO: draw roads as well
    # TODO: draw rivers and lakes as well
    # TODO: find a better way to draw the city name

    _osm: OSM
    _buildings: list[Building]
    _buildings_bbox: tuple[float, float, float, float]
    _city_name: str
    _city: NominatimCity

    _background_color: str = "#E8DFB8"
    _fonts_dir: str = "fonts"
    _circle_color = "#222222"
    _text_color = "#222222"

    _palette: list[str] = [
        "#154084",
        "#9D2719",
        "#BA6E19",
        "#D7B418",
    ]

    def __init__(self, city_name: str) -> CityMap:
        self._osm = OSM()
        self._city_name = city_name

        if len(self._palette) < 4:
            raise AssertionError("Palette must have at least 4 colors")

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

    def load(self, radius: int = 1000) -> int:
        logging.info(f"Loading city {self._city_name}")
        self._city = self._osm.getCity(self._city_name)
        logging.info(f"Loading buildings around {self._city}, radius {radius}m")
        osm_buildings = self._osm.getBuildings(self._city, radius=radius)
        logging.info(f"Loaded {len(osm_buildings)} buildings")
        self._buildings = [
            MapBuilding(nodes=building.nodes, neighbors=None, color=None)
            for building in osm_buildings
        ]
        logging.info("Finding buildings bounding box")
        self._buildings_bbox = (
            min([building.boundingbox[0] for building in osm_buildings]),
            min([building.boundingbox[1] for building in osm_buildings]),
            max([building.boundingbox[2] for building in osm_buildings]),
            max([building.boundingbox[3] for building in osm_buildings]),
        )
        logging.info(f"Found bounding box {self._buildings_bbox}")
        return len(self._buildings)

    def _pickColors(self, buildings: list[MapBuilding]) -> int:
        logging.info("Picking colors")

        logging.info("Assigning neighbours to each building")
        started = datetime.now()
        for building in buildings:
            building.neighbors = [
                other for other in buildings if building.borders(other)
            ]
        elapsed = (datetime.now() - started).total_seconds()
        logging.info(f"Assigned neighbours in {elapsed:.2f}s")

        logging.info("Sorting buildings by number of neighbours")
        buildings.sort(key=lambda b: len(b.neighbors), reverse=True)

        logging.info("Assigning colors to buildings")
        for building in buildings:
            available_colors = self._palette.copy()
            for n in building.neighbors:
                if n.color in available_colors:
                    available_colors.remove(n.color)

            if not available_colors:
                logging.error("No available colors. Failing.")
                raise RuntimeError("No available colors")

            building.color = random.choice(available_colors)

        logging.info(f"Assigned colors to {len(buildings)} buildings in {elapsed:.2f}s")

        return len(buildings)

    def _drawBuildings(
        self,
        width: int,
        height: int,
        scl: float,
    ) -> Image.Image:
        city_img = Image.new("RGB", (width, height), color=self._background_color)
        city_draw = ImageDraw.Draw(city_img)

        logging.info("Drawing buildings")

        for building in self._buildings:
            normalized_nodes = [
                self._normalizeCoordinate(node, width, height)
                for node in building.nodes
            ]

            city_draw.polygon(
                xy=normalized_nodes,
                fill=building.color,
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
            outline=self._circle_color,
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
            path = f"{out_dir}/{self._city_name}-{timestamp}.png"
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

        # pick the colors for the buildings
        self._pickColors(self._buildings)
        # draw the buildings
        city_img = self._drawBuildings(width, height, scl)
        # create the final image
        final_img = self._createImage(width, height, bottom_ratio, city_img)
        # save the image
        path = self._saveImage(final_img, path)
