"""Module for Nominatim API interface."""

from __future__ import annotations

import logging

from modules.api_interface import ApiInterface
from modules.data import Data


class NominatimCity(Data):
    """Class representing a city returned by Nominatim."""

    place_id: int
    lat: float
    lon: float
    name: str
    display_name: str
    boundingbox: list[float]

    def __post__init__(self):
        """Post-initialisation method.

        Automatically called after the initialisation of the class.
        """
        self.boundingbox = [float(x) for x in self.boundingbox]


class Nominatim(ApiInterface):
    """Class representing an interface to the Nominatim API."""

    def _makeSearchRequest(self, **kwargs) -> dict:
        """Make a search request to Nominatim web service.

        Returns:
            dict: TOML response from the web service.
        """
        logging.debug(f"Making Nominatim request with {kwargs}")
        query = "&".join([f"{key}={value}" for key, value in kwargs.items()])
        url = f"https://nominatim.openstreetmap.org/search?{query}"
        logging.debug(f"Requesting {url}")

        return self.makeRequest(url).response_json

    def findCity(self, city_name: str) -> NominatimCity:
        """Find a city by name.

        Args:
            city_name (str): name of the city.

        Returns:
            NominatimCity: _description_
        """
        logging.debug(f"Finding city {city_name}")
        data = self._makeSearchRequest(
            city=city_name,
            administrative_level=8,
            format="jsonv2",
        )

        if not data:
            logging.error(f"City {city_name} not found")
            raise ValueError(f"City {city_name} not found")

        # find the most important city
        city = sorted(data, key=lambda x: x["importance"], reverse=True)[0]

        logging.debug(f"Found city {city['display_name']}")

        return NominatimCity(
            place_id=city["place_id"],
            lat=float(city["lat"]),
            lon=float(city["lon"]),
            name=city["name"],
            display_name=city["display_name"],
            boundingbox=city["boundingbox"],
        )
