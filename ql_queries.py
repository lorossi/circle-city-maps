from __future__ import annotations

import logging
import random

import requests
from PIL import Image, ImageDraw, ImageOps

from modules.overpass import Node, Relation, Role, Way


def extract_nodes(response: dict) -> dict[int, Node]:
    logging.debug("Extracting nodes")
    nodes = {}
    for node in response["elements"]:
        if node["type"] != "node":
            continue

        nodes[node["id"]] = Node(
            lat=node["lat"],
            lon=node["lon"],
            node_id=node["id"],
        )

    logging.debug(f"Extracted {len(nodes)} nodes")
    return nodes


def extract_ways(response: dict, nodes: dict[int, Node]) -> dict[int, Way]:
    logging.debug("Extracting ways")
    ways = {}
    for way in response["elements"]:
        if way["type"] != "way":
            continue

        ways[way["id"]] = Way(
            way_id=way["id"],
            nodes=[nodes[node_id] for node_id in way["nodes"]],
        )

    logging.debug(f"Extracted {len(ways)} ways")
    return ways


def extract_relations(response: dict, ways: dict[int, Way]) -> dict[int, Relation]:
    logging.debug("Extracting relations")
    relations = {}
    for relation in response["elements"]:
        if relation["type"] != "relation":
            continue

        relation_ways = []
        for way in relation["members"]:
            if way["type"] != "way":
                continue

            current_way = ways[way["ref"]]
            current_way.role = Role(way["role"])
            relation_ways.append(current_way)

        relations[relation["id"]] = Relation(
            relation_id=relation["id"],
            ways=relation_ways,
        )

    logging.debug(f"Extracted {len(relations)} relations")
    return relations


def combine_polygons(
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


def extract_polygons(
    relations: dict[int, Relation],
) -> tuple[list[list[Node]], list[list[Node]]]:
    logging.debug("Extracting polygons")
    # discard outer
    polygons = []

    for relation in relations.values():
        new_polygon = []

        for way in relation.outer_ways:
            if not new_polygon:
                new_polygon.extend(way.nodes)
                continue

            combined = combine_polygons(new_polygon, way.nodes)
            if combined:
                new_polygon = combined
            else:
                polygons.append(new_polygon)
                new_polygon = way.nodes

        if new_polygon:
            polygons.append(new_polygon)

    return polygons, []


def format_query(query: str) -> str:
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


def extract_bbox(nodes: dict) -> tuple[float, float, float, float]:
    logging.debug("Extracting bounding box")
    min_lat = min([node.lat for node in nodes.values()])
    min_lon = min([node.lon for node in nodes.values()])
    max_lat = max([node.lat for node in nodes.values()])
    max_lon = max([node.lon for node in nodes.values()])
    logging.debug(f"Extracted bounding box: {min_lat},{min_lon},{max_lat},{max_lon}")
    return min_lat, min_lon, max_lat, max_lon


def normalize_coordinates(
    nodes: list[Node],
    bbox: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float]:
    scaled = []
    for node in nodes:
        x = (node.lon - bbox[1]) / (bbox[3] - bbox[1]) * width
        y = (node.lat - bbox[0]) / (bbox[2] - bbox[0]) * height
        scaled.append((int(x), int(y)))

    return scaled


def random_color() -> tuple[int, int, int]:
    return tuple(random.randint(0, 255) for _ in range(3))


def make_request(query: str) -> str:
    clean_query = format_query(query)
    url = f"https://overpass-api.de/api/interpreter?data={clean_query}"
    logging.debug(f"Making request to {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")

    return response.json()


def main():
    logging.basicConfig(level=logging.DEBUG)
    # coordinates of Budapest
    lat = 47.498381
    lon = 19.040470
    # coordinates of Rome
    # lat = 41.902782
    # lon = 12.496366

    radius = 2000
    # query to extract the polygon containing the river in a city
    query = f"""
        [out:json];
        relation["natural"="water"](around:{radius},{lat},{lon});
        foreach
        {{
            (
            ._;
            >;
            );
            out;
        }}
        out body geom;
    """
    response = make_request(query)

    nodes = extract_nodes(response)
    ways = extract_ways(response, nodes)
    relations = extract_relations(response, ways)
    outer, inner = extract_polygons(relations)

    bbox = extract_bbox(nodes)

    width = 1000
    height = 1000

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # for r in relations.values():
    #     scaled = []
    #     for way in r.inner_ways:
    #         scaled.extend(normalize_coordinates(way.nodes, bbox, width, height))
    #     draw.line(scaled, fill=random_color())

    for polygon in outer:
        scaled = normalize_coordinates(polygon, bbox, width, height)
        draw.polygon(scaled, fill="blue")

    img = ImageOps.flip(img)
    img.save("test.png")


if __name__ == "__main__":
    main()
