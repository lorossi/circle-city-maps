"""Module for drawing a map of a city."""
from __future__ import annotations

import logging
import os
import random
from datetime import datetime
from glob import glob

from PIL import Image, ImageDraw, ImageFont, ImageOps

from modules.data import Data
from modules.nominatim import NominatimCity
from modules.osm import OSM
from modules.overpass import Building, Node, Road


class MapBuilding(Data):
    """Class representing a building in the map."""

    nodes: list[Node]
    neighbors: list[MapBuilding]
    color_id: int
    outline_color_id: int

    def borders(self, other: Building) -> bool:
        """Check if the building borders another building.

        Two buildings border if they share at least two nodes. \
        This might include some false positives, but it's good enough.

        Args:
            other (Building)

        Returns:
            bool
        """
        return len(set(self.nodes) & set(other.nodes)) >= 2


class CityMap:
    """Class representing a map of a city."""

    # TODO: draw rivers and lakes as well
    # TODO: draw parks and forests as well
    # TODO: add support for different map styles (via different palette and background)

    _osm: OSM
    _buildings: list[MapBuilding]
    _roads: list[Road]
    _buildings_bbox: tuple[float, float, float, float]
    _city_name: str
    _city: NominatimCity

    _fonts_dir: str = "fonts"
    _background_color: str = "#E8DFB8"
    _text_color = "#222222"
    _roads_color = "#222222"
    _buildings_palette: list[str] = [
        "#154084",
        "#9D2719",
        "#BA6E19",
        "#D7B418",
    ]
    _buildings_outline_palette: list[str] = [
        "#103369",
        "#7D1F14",
        "#945814",
        "#AC9013",
    ]

    def __init__(self, city_name: str) -> CityMap:
        """Initialise the class.

        Args:
            city_name (str): name of the city to draw
                a map of.

        Returns:
            CityMap
        """
        self._osm = OSM()
        self._city_name = city_name

        if len(self._buildings_palette) < 4:
            raise AssertionError("Palette must have at least 4 colors")

    def _normalizeCoordinate(
        self,
        node: Node,
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Normalize a coordinate to the image size with respect to \
            the bounding box of the buildings.

        Args:
            node (Node): node to normalize.
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            tuple[int, int]: (x, y) coordinates of the normalized node.
        """
        x = (node.lon - self._buildings_bbox[1]) / (
            self._buildings_bbox[3] - self._buildings_bbox[1]
        )
        y = (node.lat - self._buildings_bbox[0]) / (
            self._buildings_bbox[2] - self._buildings_bbox[0]
        )

        return int(x * width), int(y * height)

    def load(self, radius: int = 1000) -> int:
        """Load a city with its features from OSM.

        Args:
            radius (int, optional): maximum distance of the features from the city \
                 centre. Defaults to 1000.

        Returns:
            int: number of nodes loaded.
        """
        logging.info(f"Loading city {self._city_name}")
        self._city = self._osm.getCity(self._city_name)
        logging.info(f"Loading buildings around {self._city}, radius {radius}m")
        osm_buildings = self._osm.getBuildings(self._city, radius=radius)
        logging.info(f"Loaded {len(osm_buildings)} buildings")
        self._buildings = [
            MapBuilding(nodes=building.nodes) for building in osm_buildings
        ]
        logging.info("Finding buildings bounding box")
        self._buildings_bbox = (
            min([building.boundingbox[0] for building in osm_buildings]),
            min([building.boundingbox[1] for building in osm_buildings]),
            max([building.boundingbox[2] for building in osm_buildings]),
            max([building.boundingbox[3] for building in osm_buildings]),
        )
        logging.info(f"Found bounding box {self._buildings_bbox}")
        logging.info(f"Loading roads around {self._city}, radius {radius}m")
        self._roads = self._osm.getRoads(self._city, radius=radius)
        logging.info(f"Loaded {len(self._roads)} roads")

        return sum([len(building.nodes) for building in self._buildings]) + sum(
            [len(road.nodes) for road in self._roads]
        )

    def _pickColors(self, buildings: list[MapBuilding]) -> int:
        """Pick colours for each building.

        This ensures that no two buildings with a common border have the same colour.

        Args:
            buildings (list[MapBuilding])

        Raises:
            RuntimeError: the algorithm failed to find a solution. \
                This won't happen as long as 4 colours are available.

        Returns:
            int: number of buildings coloured.
        """
        logging.info("Picking colours")

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

        logging.info("Assigning colours to buildings")
        for building in buildings:
            available_colors = list(range(len(self._buildings_palette)))
            for n in building.neighbors:
                if n.color_id in available_colors:
                    available_colors.remove(n.color_id)

            if not available_colors:
                logging.error("No available colours. Failing.")
                raise RuntimeError("No available colours")

            building.color_id = random.choice(available_colors)
            building.outline_color_id = building.color_id

        logging.info(f"Assigned colors to {len(buildings)} buildings in {elapsed:.2f}s")

        return len(buildings)

    def _drawBuildings(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Draw the buildings on an image.

        Args:
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            Image.Image
        """
        buildings_img = Image.new("RGBA", (width, height))
        buildings_draw = ImageDraw.Draw(buildings_img)

        logging.info("Drawing buildings")

        for building in self._buildings:
            normalized_nodes = [
                self._normalizeCoordinate(node, width, height)
                for node in building.nodes
            ]

            fill_color = self._buildings_palette[building.color_id]
            outline_color = self._buildings_outline_palette[building.outline_color_id]

            buildings_draw.polygon(
                xy=normalized_nodes,
                fill=fill_color,
                outline=outline_color,
            )

        return buildings_img

    def _drawRoads(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Draw the roads on an image.

        Args:
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            Image.Image
        """
        roads_img = Image.new("RGBA", (width, height))
        roads_draw = ImageDraw.Draw(roads_img)

        logging.info("Drawing roads")

        for road in self._roads:
            normalized_nodes = [
                self._normalizeCoordinate(node, width, height) for node in road.nodes
            ]

            roads_draw.line(
                xy=normalized_nodes,
                fill=self._roads_color,
                width=2,
            )

        return roads_img

    def _createImage(
        self,
        width: int,
        height: int,
        scl: float,
        to_composite: list[Image.Image],
    ) -> Image.Image:
        """Create the final image.

        Args:
            width (int): width of the image.
            height (int): height of the image.
            scl (float): ratio of the city image to the whole image.
            to_composite (list[Image.Image): images to composite.

        Raises:
            AssertionError: an image has a different width than the others.
            AssertionError: an image has a different height than the others.

        Returns:
            Image.Image
        """
        logging.info("Creating image")

        # check that all the images have the same size
        for x in range(1, len(to_composite)):
            if to_composite[x].width != to_composite[x - 1].width:
                raise AssertionError("Images must have the same width")

            if to_composite[x].height != to_composite[x - 1].height:
                raise AssertionError("Images must have the same height")

        # flip the buildings and roads images to account for the fact that PIL uses
        #  (0, 0) as the top left corner, while OSM uses (0, 0) as
        # the bottom left corner
        if self._city.lat > 0:
            logging.info("Flipping images")
            to_composite = [ImageOps.flip(img) for img in to_composite]
        if self._city.lon < 0:
            logging.info("Mirroring images")
            to_composite = [ImageOps.mirror(img) for img in to_composite]

        # resize the images to the desired size
        new_width, new_height = int(width * scl), int(height * scl)
        logging.info(f"Resizing images to {new_width}x{new_height}")
        to_composite = [
            img.resize((new_width, new_height), resample=Image.LANCZOS)
            for img in to_composite
        ]

        # calculate the position of the city image
        dx = int((width - new_width) / 2)
        dy = int((height - new_height) / 2)

        # create the composite image destination
        composite_img = Image.new(
            "RGBA",
            (new_width, new_height),
            color=self._background_color,
        )

        # paste all the images
        for img in to_composite:
            composite_img = Image.alpha_composite(composite_img, img)

        # create the output image
        img = Image.new("RGBA", (width, height), color=self._background_color)
        img_draw = ImageDraw.Draw(img)
        # create a mask for the city image
        mask = Image.new(
            "L",
            (composite_img.width, composite_img.height),
            color=0,
        )
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse(
            (
                0,
                0,
                composite_img.width,
                composite_img.height,
            ),
            fill=255,
        )

        # paste the city image
        img.paste(
            composite_img,
            box=(dx, dy),
            mask=mask,
        )

        # draw the city name
        font_size = int((height - new_height) / 2)
        font = self._loadFont(size=font_size)
        ex = img_draw.textlength("x", font=font)
        img_draw.text(
            (width - ex / 2, height - ex / 2),
            text=self._city_name.upper(),
            fill=self._text_color,
            font=font,
            anchor="rb",
        )

        return img

    def _saveImage(self, img: Image.Image, path: str | None) -> str:
        """Save an image to a file.

        Args:
            img (Image.Image): image to save.
            path (str | None): path to save the image to. If None, the image will be \
                saved in the same folder as the script, with the name \
                <city_name>-<timestamp>.png. Defaults to None.

        Returns:
            str: image path.
        """
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
        """Load a font from the fonts folder.

        Supported fonts are .ttf and .otf.

        Args:
            size (int): size of the font.

        Raises:
            RuntimeError: no supported fonts were found.

        Returns:
            ImageFont
        """
        logging.info(f"Loading font of size {size}")
        extensions = {"*.ttf", "*.otf"}
        logging.info(
            f"Searching for fonts with extensions {extensions} "
            f"in folder {self._fonts_dir}"
        )

        fonts = set()
        for ext in extensions:
            fonts |= set(glob(f"{self._fonts_dir}/{ext}"))

        logging.info(f"Found {len(fonts)} font(s)")

        if len(fonts) == 0:
            logging.error("No supported fonts found")
            raise RuntimeError(f"No supported fonts found in {self._fonts_dir}")

        if len(fonts) > 1:
            picked_font = fonts.pop()
            logging.warning(f"Multiple fonts found. Using font {picked_font}")
        else:
            picked_font = fonts.pop()
            logging.info(f"Using font {picked_font}")

        return ImageFont.truetype(picked_font, size=size)

    def draw(
        self,
        width: int = 1000,
        height: int = 1000,
        scl: float = 0.9,
        path: str | None = None,
        seed: int | None = None,
    ) -> str:
        """Draw the map.

        Args:
            width (int, optional): width of the final image. Defaults to 1000.
            height (int, optional): height of the final image. Defaults to 1000.
            scl (float, optional): ratio of the city image to the whole image. \
                Defaults to 0.9.
            path (str | None, optional): path to save the image to. If None, the image \
                will be saved in the same folder as the script, with the name \
                <city_name>-<timestamp>.png. Defaults to None.
            seed (int | None, optional): seed for the random number generator. \
                Defaults to None (current timestamp in milliseconds).

        Returns:
            str: path to the saved image.
        """
        logging.info(f"Drawing map {width}x{height}")

        if seed is None:
            seed = int(datetime.now().timestamp() * 1000)
        logging.info(f"Initializing random with seed {seed}")
        random.seed(seed)

        # pick the colours for the buildings
        self._pickColors(self._buildings)
        # draw the buildings
        buildings_img = self._drawBuildings(width, height)
        # draw the roads
        roads_img = self._drawRoads(width, height)
        # create the final image
        final_img = self._createImage(
            width=width,
            height=height,
            scl=scl,
            to_composite=[buildings_img, roads_img],
        )
        # save the image
        path = self._saveImage(final_img, path)
