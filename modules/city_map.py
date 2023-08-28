"""Module for drawing a map of a city."""
from __future__ import annotations

import logging
import os
import random
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps

from modules.data import Data
from modules.nominatim import NominatimCity
from modules.osm import OSM
from modules.overpass import Building, Node, Park, Road, Water
from modules.style import Style, StyleFactory


class MapBuilding(Data):
    """Class representing a building in the map."""

    nodes: list[Node]
    center: tuple[float, float]
    boundingbox: tuple[float, float, float, float]
    neighbors: set[MapBuilding]
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
        # if the bounding box does not overlap, the buildings do not border
        if (
            self.boundingbox[0] > other.boundingbox[2]
            or self.boundingbox[2] < other.boundingbox[0]
            or self.boundingbox[1] > other.boundingbox[3]
            or self.boundingbox[3] < other.boundingbox[1]
        ):
            return False

        # if the buildings share at least two nodes, they border
        shared_nodes = 0
        this_nodes = {node.node_id for node in self.nodes}
        other_nodes = {node.node_id for node in other.nodes}
        for node in this_nodes:
            if node in other_nodes:
                shared_nodes += 1
            if shared_nodes >= 2:
                return True

    def __eq__(self, other: MapBuilding) -> bool:
        """Two buildings are equal if they have the same nodes."""
        return all([node in other.nodes for node in self.nodes])

    def __hash__(self) -> int:
        """Hash the building."""
        return hash(self.center)


class CityMap:
    """Class representing a map of a city."""

    _osm: OSM
    _styleFactory: StyleFactory

    _buildings: list[MapBuilding]
    _roads: list[Road]
    _parks: list[Park]
    _water: list[Water]
    _buildings_bbox: tuple[float, float, float, float]
    _city_name: str
    _city: NominatimCity
    _style: Style

    _fonts_dir: str = "fonts"
    _out_dir: str = "maps"

    def __init__(self, city_name: str) -> CityMap:
        """Initialise the class.

        Args:
            city_name (str): name of the city to draw
                a map of.

        Returns:
            CityMap
        """
        self._city_name = city_name

        self._osm = OSM()
        self._styleFactory = StyleFactory()

    def _normalizeCoordinate(
        self,
        nodes: list[Node],
        width: int,
        height: int,
    ) -> list[tuple[int, int]]:
        """Normalize a coordinate to the image size with respect to \
            the bounding box of the buildings.

        Args:
            node (Node): node to normalize.
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            tuple[int, int]: (x, y) coordinates of the normalized node.
        """
        normalized_nodes = []

        for node in nodes:
            x = (node.lon - self._buildings_bbox[1]) / (
                self._buildings_bbox[3] - self._buildings_bbox[1]
            )
            y = (node.lat - self._buildings_bbox[0]) / (
                self._buildings_bbox[2] - self._buildings_bbox[0]
            )

            if x < 0 or x > 1 or y < 0 or y > 1:
                logging.debug(
                    f"Node {node} is outside the bounding box of the buildings, "
                    "so it will be skipped"
                )
                continue

            normalized_nodes.append((int(x * width), int(y * height)))

        return normalized_nodes

    def _assignNeighbors(self, radius: float, max_dist: float = 50) -> float:
        percent = 0
        increment = 0.1

        # approximate max_dist in degrees by the average of the bounding box sides
        # (this is not accurate, but it's good enough)
        d_lat = (
            (self._buildings_bbox[2] - self._buildings_bbox[0])
            / (2 * radius)
            * max_dist
        )
        d_lon = (
            (self._buildings_bbox[3] - self._buildings_bbox[1])
            / (2 * radius)
            * max_dist
        )

        logging.info(
            "Max distance between buildings: "
            f"{d_lat*1000:.2f}*10^-3 deg (lat), {d_lon*1000:.2f}*10^-3 deg (lon), "
            f"or approximately {max_dist}m"
        )

        started = datetime.now()
        buildings_checked = 0
        for x, building in enumerate(self._buildings):
            others = [
                other
                for other in self._buildings
                if (
                    abs(building.center[0] - other.center[0]) < d_lat
                    and abs(building.center[1] - other.center[1]) < d_lon
                )
                and building != other
            ]
            buildings_checked += len(others)

            building.neighbors = {other for other in others if building.borders(other)}
            new_percent = x / len(self._buildings)
            if new_percent >= percent + increment:
                elapsed = (datetime.now() - started).total_seconds()
                remaining = elapsed * (1 - new_percent) / new_percent
                total = elapsed + remaining
                logging.info(
                    f"Progress: {new_percent*100:.2f}%. "
                    f"Remaining: {remaining:.2f}s, Total: {total:.2f}s"
                )
                percent += increment

        logging.info(
            f"Checked {buildings_checked} buildings "
            f"averaging {buildings_checked/len(self._buildings):.2f} neighbours "
            f"each in {(datetime.now() - started).total_seconds():.2f}s"
        )

        return (datetime.now() - started).total_seconds()

    def load(self, radius: int = 1000, random_fill: bool = False) -> int:
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
            MapBuilding(
                nodes=building.nodes,
                boundingbox=building.boundingbox,
                center=building.center,
            )
            for building in osm_buildings
        ]
        logging.info("Finding buildings bounding box")
        self._buildings_bbox = (
            min([building.boundingbox[0] for building in osm_buildings]),
            min([building.boundingbox[1] for building in osm_buildings]),
            max([building.boundingbox[2] for building in osm_buildings]),
            max([building.boundingbox[3] for building in osm_buildings]),
        )
        logging.debug(f"Found bounding box {self._buildings_bbox}")

        if not random_fill:
            logging.info("Assigning neighbours to buildings (this might take a while)")
            elapsed = self._assignNeighbors(radius=radius)
            logging.info(f"Assigned neighbours in {elapsed:.2f}s")
        else:
            logging.debug("Buildings won't be paired; color assignment will be random")

        logging.info(f"Loading roads around {self._city}, radius {radius}m")
        self._roads = self._osm.getRoads(self._city, radius=radius)
        logging.info(f"Loaded {len(self._roads)} roads")

        logging.info(f"Loading parks around {self._city}, radius {radius}m")
        self._parks = self._osm.getParks(self._city, radius=radius)
        logging.info(f"Loaded {len(self._parks)} parks")

        logging.info(f"Loading water around {self._city}, radius {radius}m")
        self._water = self._osm.getWater(self._city, radius=radius)
        logging.info(f"Loaded {len(self._water)} water features")

        loaded_nodes = (
            sum([len(building.nodes) for building in self._buildings])
            + sum([len(road.nodes) for road in self._roads])
            + sum([len(park.nodes) for park in self._parks])
            + sum([len(water.nodes) for water in self._water])
        )
        logging.info(f"Loaded {loaded_nodes} nodes")
        return loaded_nodes

    def _pickBuildingsColors(self, buildings: list[MapBuilding]) -> int:
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
        logging.info("Picking colours for buildings")
        if any(building.neighbors is None for building in buildings):
            logging.debug(
                "Some buildings have no neighbours. Aborting color assignment."
            )
            return 0

        logging.debug("Sorting buildings by number of neighbours")
        buildings.sort(key=lambda b: len(b.neighbors), reverse=True)

        logging.debug("Assigning colours to buildings")
        fails = 0
        for building in buildings:
            available_colors_ids = list(range(len(self._style.buildings_fill)))
            for n in building.neighbors:
                if n.color_id in available_colors_ids:
                    available_colors_ids.remove(n.color_id)

            if not available_colors_ids:
                logging.debug("No available colours. Leaving building as is.")
                available_colors_ids = None
                fails += 1
            else:
                building.color_id = random.choice(available_colors_ids)
                building.outline_color_id = building.color_id

        logging.info(
            f"Assigned colors to {len(buildings)} buildings. "
            f"{fails} fails have been encountered."
        )

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
            style (Style): style to use.

        Returns:
            Image.Image
        """
        buildings_img = Image.new("RGBA", (width, height))
        buildings_draw = ImageDraw.Draw(buildings_img)

        logging.info("Drawing buildings")

        for building in self._buildings:
            normalized_nodes = self._normalizeCoordinate(building.nodes, width, height)

            if len(normalized_nodes) < 3:
                logging.debug(
                    f"Building {building} has less than 3 nodes. Skipping it."
                )

            if building.color_id is None:
                logging.debug("Building has no color. filling it with random color")
                random_id = random.randint(
                    0,
                    len(self._style.buildings_fill) - 1,
                )
                fill_color = self._style.buildings_fill[random_id]
                outline_color = self._style.buildings_outline[random_id]
            else:
                fill_color = self._style.buildings_fill[building.color_id]
                outline_color = self._style.buildings_outline[building.outline_color_id]

            buildings_draw.polygon(
                xy=normalized_nodes,
                fill=fill_color,
                outline=outline_color,
            )

        return buildings_img

    def _drawParks(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Draw the parks on an image.

        Args:
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            Image.Image: _description_
        """
        parks_img = Image.new("RGBA", (width, height))
        parks_draw = ImageDraw.Draw(parks_img)

        logging.info("Drawing parks")

        for park in self._parks:
            normalized_nodes = self._normalizeCoordinate(park.nodes, width, height)

            if len(normalized_nodes) < 3:
                logging.debug(f"Park {park} has less than 3 nodes. Skipping it.")
                continue

            parks_draw.polygon(
                xy=normalized_nodes,
                fill=self._style.parks_color,
                outline=self._style.parks_color,
            )

        return parks_img

    def _drawWater(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Draw the water on an image.

        Args:
            width (int): width of the image.
            height (int): height of the image.

        Returns:
            Image.Image: _description_
        """
        water_img = Image.new("RGBA", (width, height))
        water_draw = ImageDraw.Draw(water_img)

        logging.info("Drawing water")

        for water in self._water:
            normalized_nodes = self._normalizeCoordinate(water.nodes, width, height)

            if len(normalized_nodes) < 3:
                logging.debug(f"Water {water} has less than 3 nodes. Skipping it.")
                continue

            water_draw.polygon(
                xy=normalized_nodes,
                fill=self._style.water_color,
                outline=self._style.water_color,
            )

        return water_img

    def _drawRoads(
        self,
        width: int,
        height: int,
    ) -> Image.Image:
        """Draw the roads on an image.

        Args:
            width (int): width of the image.
            height (int): height of the image.
            style (Style): style to use.

        Returns:
            Image.Image
        """
        roads_img = Image.new("RGBA", (width, height))
        roads_draw = ImageDraw.Draw(roads_img)

        logging.info("Drawing roads")

        for road in self._roads:
            normalized_nodes = self._normalizeCoordinate(road.nodes, width, height)

            roads_draw.line(
                xy=normalized_nodes,
                fill=self._style.roads_color,
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
            style (Style): style to use.

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
            logging.debug("Flipping composite images")
            to_composite = [ImageOps.flip(img) for img in to_composite]
        if self._city.lon < 0:
            logging.debug("Mirroring composite images")
            to_composite = [ImageOps.mirror(img) for img in to_composite]

        # resize the images to the desired size
        new_width, new_height = int(width * scl), int(height * scl)
        logging.debug(f"Resizing images to {new_width}x{new_height}")
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
            color=self._style.background_color,
        )

        # paste all the images
        for img in to_composite:
            composite_img = Image.alpha_composite(composite_img, img)

        # create the output image
        img = Image.new("RGBA", (width, height), color=self._style.background_color)
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
        font_size = int((height - new_height) * 0.4)
        font = self._loadFont(name=self._style.font_family, size=font_size)
        ex = img_draw.textlength("x", font=font)
        text_x = int(width * 0.9)
        text_y = int(height - ex)
        img_draw.text(
            (text_x, text_y),
            text=self._city_name.upper(),
            fill=self._style.text_color,
            font=font,
            anchor="rb",
        )

        logging.info("Image created")

        return img

    def _saveImage(self, img: Image.Image, path: str | None, style: str = None) -> str:
        """Save an image to a file.

        Args:
            img (Image.Image): image to save.
            path (str | None): path to save the image to. If None, the image will be \
                saved in the same folder as the script, with the name \
                <city_name>-<style>.png. Defaults to None.

        Returns:
            str: image path.
        """
        logging.info("Saving image")
        if path is not None:
            out_dir = os.path.dirname(path)
        else:
            out_dir = self._out_dir
            path = f"{out_dir}/{self._city_name}-{style}.png".replace(" ", "_")

        if not path.endswith(".png"):
            path = f"{path}.png"

        if out_dir and not os.path.exists(out_dir):
            logging.debug(f"Creating directory {out_dir}")
            os.makedirs(out_dir)

        logging.info(f"Saving image to {path}")
        img.save(path)
        return path

    def _loadFont(self, name: str, size: int) -> ImageFont:
        """Load a font from the fonts folder.

        Supported fonts are .ttf and .otf.

        Args:
            size (int): size of the font.

        Raises:
            RuntimeError: no matching supported fonts were found.

        Returns:
            ImageFont
        """
        logging.debug(f"Loading font {name} of size {size}")

        path = os.path.join(self._fonts_dir, name)
        if not os.path.exists(path):
            logging.error(f"Font {name} not found")
            raise RuntimeError(f"Font {name} not found")

        return ImageFont.truetype(path, size=size)

    def draw(
        self,
        width: int = 1000,
        height: int = 1000,
        scl: float = 0.9,
        path: str | None = None,
        seed: int | None = None,
        style: str = "Bauhaus",
        draw_buildings: bool = True,
        draw_roads: bool = True,
        draw_parks: bool = True,
        draw_water: bool = True,
    ) -> str:
        """Draw the map.

        Args:
            width (int, optional): width of the final image. Defaults to 1000.
            height (int, optional): height of the final image. Defaults to 1000.
            scl (float, optional): ratio of the city image to the whole image. \
                Defaults to 0.9.
            path (str | None, optional): path to save the image to. If None, the image \
                will be saved in the same folder as the script, with the name \
                <city_name>-<style>.png. Defaults to None.
            seed (int | None, optional): seed for the random number generator. \
                Defaults to None (current timestamp in milliseconds).
            style (str, optional): name of the style to use. Defaults to "Bauhaus".

        Returns:
            str: path to the saved image.
        """
        logging.info(f"Drawing map {width}x{height}")

        # initialize the random number generator
        if seed is None:
            seed = int(datetime.now().timestamp() * 1000)
        logging.debug(f"Initializing random with seed {seed}")
        random.seed(seed)

        # load a style
        logging.info(f"Loading style {style}")
        self._style = self._styleFactory.getStyle(style)

        to_composite = []

        # draw the roads
        if draw_roads:
            to_composite.append(
                self._drawRoads(
                    width=width,
                    height=height,
                )
            )

        # draw the parks
        if draw_parks:
            to_composite.append(
                self._drawParks(
                    width=width,
                    height=height,
                )
            )

        # draw the water
        if draw_water:
            to_composite.append(
                self._drawWater(
                    width=width,
                    height=height,
                )
            )

        # draw the buildings
        if draw_buildings:
            # pick the colours for the buildings
            self._pickBuildingsColors(
                buildings=self._buildings,
            )
            to_composite.append(
                self._drawBuildings(
                    width=width,
                    height=height,
                )
            )

        # create the final image
        final_img = self._createImage(
            width=width,
            height=height,
            scl=scl,
            to_composite=to_composite,
        )
        # save the image
        out_path = self._saveImage(final_img, path, style)
        return out_path

    @property
    def styles(self) -> list[str]:
        """Return the available styles.

        Returns:
            list[str]: list of available styles.
        """
        return self._styleFactory.map_styles
