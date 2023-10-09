"""Module for Overpass API interface."""
from __future__ import annotations

import logging
from enum import Enum

from modules.api_interface import ApiInterface
from modules.data import Data


class Node(Data):
    """Class representing a node returned by Overpass."""

    lat: float
    lon: float
    node_id: int

    def __eq__(self, other: Node) -> bool:
        """Twp nodes are equal if they have the same latitude and longitude."""
        if not isinstance(other, Node):
            return False

        return self.node_id == other.node_id

    def __hash__(self) -> int:
        """Hash of the node."""
        return self.node_id


class Role(Enum):
    """Enum representing the possible roles of a way in a relation."""

    INNER = "inner"
    OUTER = "outer"
    OUTLINE = "outline"


class Way(Data):
    """Class representing a way returned by Overpass."""

    nodes: list[int]
    boundingbox: tuple[float, float, float, float]
    way_id: int
    role: Role

    def __post__init__(self):
        """Post-initialisation hook."""
        if not self.boundingbox:
            self.boundingbox = (
                min([n.lat for n in self.nodes]),
                min([n.lon for n in self.nodes]),
                max([n.lat for n in self.nodes]),
                max([n.lon for n in self.nodes]),
            )

    def __eq__(self, other: Way) -> bool:
        """Twp nodes are equal if they have the same latitude and longitude."""
        return self.way_id == other.way_id

    def __hash__(self) -> int:
        """Hash of the node."""
        return self.way_id


class Relation(Data):
    """Class representing a relation returned by Overpass."""

    ways: list[Way]
    relation_id: int

    @property
    def outer_ways(self) -> list[Way]:
        """Get the outer ways of the relation."""
        return [way for way in self.ways if way.role in [Role.OUTER, Role.OUTLINE]]

    @property
    def inner_ways(self) -> list[Way]:
        """Get the inner ways of the relation."""
        return [way for way in self.ways if way.role == Role.INNER]

    def __eq__(self, other: Relation) -> bool:
        """Twp nodes are equal if they have the same latitude and longitude."""
        return self.relation_id == other.relation_id

    def __hash__(self) -> int:
        """Hash of the node."""
        return self.relation_id


class OverpassElement(Data):
    """Class representing an element returned by Overpass."""

    nodes: list[Node]
    inner_nodes: list[list[Node]]
    center: tuple[float, float]
    boundingbox: tuple[float, float, float, float]
    element_id: int

    def __post__init__(self):
        """Post-initialisation hook."""
        if not self.nodes:
            raise ValueError(f"OverpassElement {self.__class__.__name__} has no nodes")

        if not self.boundingbox:
            self.boundingbox = (
                min([n.lat for n in self.nodes]),
                min([n.lon for n in self.nodes]),
                max([n.lat for n in self.nodes]),
                max([n.lon for n in self.nodes]),
            )

        if not self.center:
            self.center = (
                (self.boundingbox[0] + self.boundingbox[2]) / 2,
                (self.boundingbox[1] + self.boundingbox[3]) / 2,
            )

        if self.inner_nodes is None:
            self.inner_nodes = []


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
        logging.debug(f"Formatting query: {query}")
        # remove all newlines
        lines = query.split("\n")
        # remove all leading and trailing whitespace
        lines = [line.strip() for line in lines]
        # remove all double spaces
        query = " ".join(lines)
        while "  " in query:
            query = query.replace("  ", " ")

        logging.debug(f"Formatted query: {query}")
        return query

    def _makeRequest(self, **kwargs: str) -> dict:
        """Make a request to the Overpass API.

        Returns:
            dict: TOML response from the API.
        """
        logging.debug(f"Making Overpass request with {kwargs}")
        query = self._formatQuery(kwargs["query"])
        logging.debug(f"Formatted query: {query}")
        url = f"https://overpass-api.de/api/interpreter?data={query}"

        return self.makeRequest(url, max_timeout=60).response_json

    def _extractWays(self, response: dict) -> dict[int, Way]:
        """Extract ways from an Overpass response.

        Args:
            response (dict): Overpass response.

        Returns:
            dict[int, Way]: Dictionary of ways.
        """
        logging.debug("Extracting ways")
        ways = {}
        for element in response["elements"]:
            if element["type"] != "way":
                continue
            way_id = element["id"]
            way_nodes = []
            for x in range(len(element["nodes"])):
                way_nodes.append(
                    Node(
                        lat=element["geometry"][x]["lat"],
                        lon=element["geometry"][x]["lon"],
                        node_id=element["nodes"][x],
                    )
                )
            boundingbox = (
                element["bounds"]["minlat"],
                element["bounds"]["minlon"],
                element["bounds"]["maxlat"],
                element["bounds"]["maxlon"],
            )
            ways[way_id] = Way(
                way_id=way_id,
                nodes=way_nodes,
                boundingbox=boundingbox,
            )

        logging.debug(f"Extracted {len(ways)} ways")
        return ways

    def _extractRelations(self, response: dict) -> dict[int, Relation]:
        logging.debug("Extracting relations")
        ways = self._extractWays(response)
        relations = {}
        for element in response["elements"]:
            if element["type"] != "relation":
                continue
            relation_id = element["id"]
            relation_ways = []
            for way in element["members"]:
                if way["type"] != "way":
                    continue
                if way["role"] == "part":
                    continue

                current_way = ways[way["ref"]]

                try:
                    role = Role(way["role"])
                except ValueError:
                    role = Role.OUTLINE

                current_way.role = role

                relation_ways.append(current_way)

            relations[relation_id] = Relation(
                relation_id=relation_id,
                ways=relation_ways,
            )

        logging.debug(f"Extracted {len(relations)} relations")

        return relations

    def _combinePolygons(
        self,
        p1: list[Node],
        p2: list[Node],
    ) -> list[Node]:
        logging.debug("Combining polygons")
        if p1[0] == p2[0]:
            return p2[::-1] + p1
        elif p1[0] == p2[-1]:
            return p2 + p1
        elif p1[-1] == p2[0]:
            return p1 + p2
        elif p1[-1] == p2[-1]:
            return p1 + p2[::-1]

        return None

    def _buildPolygons(self, ways: list[Way]) -> list[list[Node]]:
        logging.debug("Extracting polygon from ways")
        new_polygon = []
        polygons = []

        for way in ways:
            if not new_polygon:
                new_polygon.extend(way.nodes)
                continue

            combined = self._combinePolygons(new_polygon, way.nodes)
            if combined:
                new_polygon = combined
            else:
                polygons.append(new_polygon)
                new_polygon = way.nodes

        if new_polygon:
            polygons.append(new_polygon)

        return polygons

    def _queryWayFeature(
        self,
        lat: float,
        lon: float,
        radius: float,
        feature: type,
        feature_name: str = None,
    ) -> list[OverpassElement]:
        logging.debug(f"Extracting nodes for {feature.__name__}")
        if feature_name is None:
            feature_name = feature.__name__.lower()

        # query the API for all the ways
        query = f"""
        [out:json];
        way["{feature_name}"](around:{radius},{lat},{lon});
        out body geom;
        """
        response = self._makeRequest(query=query)
        # extract the nodes from the response
        ways = self._extractWays(response)
        # create the features from the ways
        features = []
        for way in ways.values():
            features.append(
                feature(
                    nodes=way.nodes,
                    boundingbox=way.boundingbox,
                    element_id=way.way_id,
                )
            )

        logging.debug(f"Extracted {len(features)} {feature.__name__}")

        return features

    def _queryRelationFeature(
        self,
        lat: float,
        lon: float,
        radius: float,
        feature: type,
        feature_name: str = None,
    ) -> list[OverpassElement]:
        if feature_name is None:
            feature_name = feature.__name__.lower()

        # query the API for all the relations
        query = f"""
        [out:json];
        relation["{feature_name}"](around:{radius},{lat},{lon});
        (._;>>;);
        out body geom;
        """
        response = self._makeRequest(query=query)

        # extract the relations from the response
        relations = self._extractRelations(response)
        # create the features from the relations
        features = []
        for relation in relations.values():
            outer = self._buildPolygons(relation.outer_ways)
            inner = self._buildPolygons(relation.inner_ways)

            if not outer:
                continue

            features.append(
                feature(
                    nodes=outer[0],
                    inner_nodes=inner,
                    element_id=relation.relation_id,
                )
            )

        logging.debug(f"Extracted {len(features)} {feature.__name__}")

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
        building_ways = self._queryWayFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Building,
        )
        building_relations = self._queryRelationFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Building,
        )

        return building_ways + building_relations

    def getRoads(self, lat: float, lon: float, radius: float) -> list[Road]:
        """Get roads around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Road]
        """
        road_ways = self._queryWayFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Road,
            feature_name="highway",
        )
        road_relations = self._queryRelationFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Road,
            feature_name="highway",
        )
        return road_ways + road_relations

    def getParks(self, lat: float, lon: float, radius: float) -> list[Park]:
        """Get parks around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Park]
        """
        park_ways = self._queryWayFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Park,
            feature_name="leisure",
        )
        park_relations = self._queryRelationFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Park,
            feature_name="leisure",
        )
        return park_ways + park_relations

    def getWater(self, lat: float, lon: float, radius: float) -> list[Water]:
        """Get water bodies around a point.

        Args:
            lat (float): centre latitude
            lon (float): centre longitude
            radius (float): maximum distance from the centre

        Returns:
            list[Water]
        """
        water_ways = self._queryWayFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Water,
            feature_name="water",
        )
        water_relations = self._queryRelationFeature(
            lat=lat,
            lon=lon,
            radius=radius,
            feature=Water,
            feature_name="water",
        )
        return water_ways + water_relations
