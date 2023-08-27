"""Module for Overpass API interface."""
from __future__ import annotations

import logging

from modules.api_interface import ApiInterface
from modules.data import Data


class Node(Data):
    """Class representing a node returned by Overpass."""

    lat: float
    lon: float

    def __eq__(self, other: Node) -> bool:
        """Twp nodes are equal if they have the same latitude and longitude."""
        return self.lat == other.lat and self.lon == other.lon

    def __hash__(self) -> int:
        """Hash of the node."""
        return hash((self.lat, self.lon))


class OverpassElement(Data):
    """Class representing an element returned by Overpass."""

    nodes: list[Node]

    @property
    def boundingbox(self) -> tuple[float, float, float, float]:
        """Bounding box of the element."""
        return (
            min([node.lat for node in self.nodes]),
            min([node.lon for node in self.nodes]),
            max([node.lat for node in self.nodes]),
            max([node.lon for node in self.nodes]),
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
        return [Node(lat=node["lat"], lon=node["lon"]) for node in way["geometry"]]

    def _extractRelationNodes(self, relation: dict) -> list[list[Node]]:
        """Extract the nodes from a relation returned by Overpass.

        Args:
            relation (dict): Relation returned by Overpass.

        Returns:
            list[list[Node]]
        """
        nodes = []
        for m in relation["members"]:
            if m["role"] == "inner":
                continue

            nodes.append(self._extractWayNodes(m))

        return nodes

    def _extractFeatures(
        self,
        data: dict,
        feature: OverpassElement,
    ) -> list[OverpassElement]:
        """Extract features from a response returned by Overpass.

        Args:
            data (dict): Response returned by Overpass.
            feature (OverpassElement): Feature to extract.

        Returns:
            list[OverpassElement]
        """
        logging.info(f"Extracting {feature.__name__}s")
        features = []
        for f in data["elements"]:
            match f["type"]:
                case "way":
                    features.append(feature(nodes=self._extractWayNodes(f)))

                case "relation":
                    for nodes in self._extractRelationNodes(f):
                        features.append(feature(nodes=nodes))

                case _:
                    logging.warning(f"Unknown element type {f['type']}")
                    raise Exception(f"Unknown element type {f['type']}")

        logging.info(f"Extracted {len(features)} {feature.__name__}s")

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
        query = f"""
            [out:json];
            (
                way["building"](around:{radius},{lat},{lon});
                relation["building"](around:{radius},{lat},{lon});
            );
            out geom;
        """

        data = self._makeRequest(query=query)
        logging.info(f"Got {len(data['elements'])} buildings")
        return self._extractFeatures(data=data, feature=Building)

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
        return self._extractFeatures(data=data, feature=Road)

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
        return self._extractFeatures(data=data, feature=Park)

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
        return self._extractFeatures(data=data, feature=Water)
