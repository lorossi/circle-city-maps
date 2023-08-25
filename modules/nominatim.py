from __future__ import annotations

import logging

import requests

from modules.data import Data


class NominatimCity(Data):
    place_id: int
    lat: float
    lon: float
    name: str
    display_name: str
    boundingbox: list[float]

    def __post__init__(self):
        self.boundingbox = [float(x) for x in self.boundingbox]


class Nominatim:
    def _makeSearchRequest(self, **kwargs) -> dict:
        logging.info(f"Making Nominatim request with {kwargs}")
        query = "&".join([f"{key}={value}" for key, value in kwargs.items()])
        url = f"https://nominatim.openstreetmap.org/search?{query}"
        logging.info(f"Requesting {url}")
        r = requests.get(url)

        if r.status_code != 200:
            logging.error(f"Request failed with code {r.status_code}")
            raise Exception(f"Request failed with code {r.status_code}")

        logging.info(f"Request successful with code {r.status_code}")
        return r.json()

    def findCity(
        self,
        city_name: str,
        administrative_level: int = 8,
    ) -> NominatimCity:
        logging.info(f"Finding city {city_name}")
        data = self._makeSearchRequest(
            city=city_name,
            administrative_level=administrative_level,
            format="jsonv2",
        )
        # find the most important city
        city = sorted(data, key=lambda x: x["importance"], reverse=True)[0]

        logging.info(f"Found city {city['display_name']}")

        return NominatimCity(
            place_id=city["place_id"],
            lat=float(city["lat"]),
            lon=float(city["lon"]),
            name=city["name"],
            display_name=city["display_name"],
            boundingbox=city["boundingbox"],
        )
