from __future__ import annotations

import logging

from PIL import Image, ImageDraw, ImageOps

from modules.nominatim import NominatimCity
from modules.osm import OSM
from modules.overpass import Node, OverpassElement


class CityMap:
    _osm: OSM
    _buildings: list[OverpassElement]
    _buildings_bbox: tuple[float, float, float, float]
    _city_name: str
    _city: NominatimCity

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

    def draw(self, width: int = 1000, height: int = 1000, path: str = "map.png") -> str:
        logging.info(f"Drawing map {width}x{height}")
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        for building in self._buildings:
            normalized_nodes = [
                self._normalizeCoordinate(nodes, width=width, height=height)
                for nodes in building.nodes
            ]

            draw.polygon(
                xy=normalized_nodes,
                fill="black",
                outline="black",
            )

        # flip the image to account for the fact that PIL uses (0, 0)
        # as the top left corner, while OSM uses (0, 0) as the bottom left corner

        if self._city.lat > 0:
            img = ImageOps.flip(img)
        if self._city.lon < 0:
            img = ImageOps.mirror(img)

        logging.info(f"Saving map to {path}")
        img.save(path)
