"""Module for Overpass API interface."""
from __future__ import annotations

import logging

from modules.api_interface import ApiInterface
from modules.data import Data


class Node(Data):
    """Class representing a node returned by Overpass."""

    lat: float
    lon: float
    node_id: int

    def __eq__(self, other: Node) -> bool:
        """Twp nodes are equal if they have the same latitude and longitude."""
        return self.node_id == other.node_id

    def __hash__(self) -> int:
        """Hash of the node."""
        return hash(self.node_id)


class OverpassElement(Data):
    """Class representing an element returned by Overpass."""

    nodes: list[Node]
    center: tuple[float, float]
    boundingbox: tuple[float, float, float, float]

    def __post__init__(self):
        """Post-initialisation hook."""
        self.boundingbox = (
            min([n.lat for n in self.nodes]),
            min([n.lon for n in self.nodes]),
            max([n.lat for n in self.nodes]),
            max([n.lon for n in self.nodes]),
        )
        self.center = (
            (self.boundingbox[0] + self.boundingbox[2]) / 2,
            (self.boundingbox[1] + self.boundingbox[3]) / 2,
        )


class Building(OverpassElement):
    """Class representing a building returned by Overpass."""

    ...


class Road(OverpassElement):
    """Class representing a road returned by Overpass."""

    ...


class Park(OverpassElement):
    """Class representing a park returned by Overpass."""

    ...


class Water(OverpassElement):
    """Class representing a water body returned by Overpass."""

    ...


class Overpass(ApiInterface):
    """Class representing an interface to the Overpass API."""

    def _formatQuery(self, query: str) -> str:
        """Format a query to be sent to the Overpass API.

        Args:
            query (str): Query to format.

        Returns:
            str
        """
        query = query.replace("\n", " ")
        while "  " in query:
            query = query.replace("  ", " ")

        return query.strip()

    def _makeRequest(self, **kwargs: str) -> dict:
        """Make a request to the Overpass API.

        Returns:
            dict: TOML response from the API.
        """
        logging.info(f"Making Overpass request with {kwargs}")
        query = self._formatQuery(kwargs["query"])
        logging.info(f"Formatted query: {query}")
        url = f"https://overpass-api.de/api/interpreter?data={query}"

        return self.makeRequest(url).response_json

    def _extractWayNodes(self, way: dict) -> list[Node]:
        """Extract the nodes from a way returned by Overpass.

        Args:
            way (dict): Way returned by Overpass.

        Returns:
            list[Node]
        """
        if "geometry" not in way:
            logging.warning(f"Way {way['id']} has no geometry")
            return []

        nodes = []
        for x, node in enumerate(way["geometry"]):
            nodes.append(
                Node(lat=node["lat"], lon=node["lon"], node_id=way["nodes"][x]),
            )

        return nodes

    def _extractFeatures(
        self,
        data: dict,
        feature_instance: OverpassElement,
    ) -> list[OverpassElement]:
        """Extract features from a response returned by Overpass.

        Args:
            data (dict): Response returned by Overpass.
            feature (OverpassElement): Feature to extract.

        Returns:
            list[OverpassElement]
        """
        logging.info(f"Extracting {feature_instance.__name__}s")
        features = []
        for f in data["elements"]:
            nodes = self._extractWayNodes(way=f)

            if not nodes:
                continue

            features.append(feature_instance(nodes=nodes))

        logging.info(f"Extracted {len(features)} {feature_instance.__name__}s")

        return features

    def getBuildings(self, lat: float, lon: float, radius: float) -> list[Building]:
        """Get buildings around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Building]
        """
        logging.info(f"Getting buildings around {lat},{lon} with radius {radius}")
        query_way = f"""
            [out:json];
            way["building"](around:{radius},{lat},{lon});
            out geom;
        """
        way_data = self._makeRequest(query=query_way)
        query_relation = f"""
            [out:json];
            relation["building"](around:{radius},{lat},{lon}) -> . relations;
            (
                way(r.relations);
            );
            out geom;
        """
        relation_data = self._makeRequest(query=query_relation)
        way_data["elements"].extend(relation_data["elements"])

        logging.info(f"Got {len(way_data['elements'])} buildings")
        return self._extractFeatures(data=way_data, feature_instance=Building)

    def getRoads(self, lat: float, lon: float, radius: float) -> list[Road]:
        """Get roads around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Road]
        """
        logging.info(f"Getting roads around {lat},{lon} with radius {radius}")
        query = f"""
            [out:json];
            (
                way["highway"](around:{radius},{lat},{lon});
                relation["highway"](around:{radius},{lat},{lon});
            );
            out geom;
        """

        data = self._makeRequest(query=query)
        logging.info(f"Got {len(data['elements'])} roads")
        return self._extractFeatures(data=data, feature_instance=Road)

    def getParks(self, lat: float, lon: float, radius: float) -> list[Park]:
        """Get parks around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Park]
        """
        logging.info(f"Getting parks around {lat},{lon} with radius {radius}")
        query = f"""
            [out:json];
            (
                way["leisure"](around:{radius},{lat},{lon});
                relation["leisure"](around:{radius},{lat},{lon});
            );
            out geom;
        """

        data = self._makeRequest(query=query)
        logging.info(f"Got {len(data['elements'])} parks")
        return self._extractFeatures(data=data, feature_instance=Park)

    def getWater(self, lat: float, lon: float, radius: float) -> list[Water]:
        """Get water bodies around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Water]
        """
        logging.info(f"Getting water bodies around {lat},{lon} with radius {radius}")
        query = f"""
            [out:json];
            (
                way["natural"](around:{radius},{lat},{lon});
                relation["natural"](around:{radius},{lat},{lon});
            );
            out geom;
        """

        data = self._makeRequest(query=query)
        logging.info(f"Got {len(data['elements'])} water bodies")
        return self._extractFeatures(data=data, feature_instance=Water)
