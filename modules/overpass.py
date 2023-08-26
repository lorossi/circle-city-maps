from __future__ import annotations

import logging


from modules.data import Data
from modules.api_interface import ApiInterface


class Node(Data):
    lat: float
    lon: float

    def __eq__(self, other: Node) -> bool:
        return self.lat == other.lat and self.lon == other.lon

    def __hash__(self) -> int:
        return hash(f"{self.lat}+{self.lon}")


class OverpassElement(Data):
    nodes: list[Node]

    @property
    def boundingbox(self) -> tuple[float, float, float, float]:
        return (
            min([node.lat for node in self.nodes]),
            min([node.lon for node in self.nodes]),
            max([node.lat for node in self.nodes]),
            max([node.lon for node in self.nodes]),
        )


class Building(OverpassElement):
    ...


class Overpass(ApiInterface):
    def _formatQuery(self, query) -> str:
        query = query.replace("\n", " ")
        while "  " in query:
            query = query.replace("  ", " ")

        return query

    def _makeRequest(self, **kwargs: str) -> dict:
        logging.info(f"Making Overpass request with {kwargs}")
        query = self._formatQuery(kwargs["query"])
        logging.info(f"Formatted query: {query}")
        url = f"https://overpass-api.de/api/interpreter?data={query}"

        return self.makeRequest(url).response_json

    def _extractWayNodes(self, way: dict) -> list[Node]:
        return [Node(lat=node["lat"], lon=node["lon"]) for node in way["geometry"]]

    def _extractRelationNodes(self, relation: dict) -> list[list[Node]]:
        nodes = []
        for m in relation["members"]:
            if m["role"] == "inner":
                continue

            nodes.append(self._extractWayNodes(m))

        return nodes

    def getBuildings(self, lat: float, lon: float, radius) -> list[Building]:
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

        buildings = []
        for b in data["elements"]:
            match b["type"]:
                case "way":
                    buildings.append(OverpassElement(nodes=self._extractWayNodes(b)))
                case "relation":
                    for nodes in self._extractRelationNodes(b):
                        buildings.append(OverpassElement(nodes=nodes))
                case _:
                    raise Exception(f"Unknown element type {b['type']}")

        logging.info(f"Extracted {len(buildings)} buildings")
        return buildings
