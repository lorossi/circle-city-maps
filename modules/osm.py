"""Module containing the main class for interfacing with the OSM API."""

from __future__ import annotations

import logging

from modules.nominatim import Nominatim, NominatimCity
from modules.overpass import Overpass, Building, Road, Park, Water


class OSM:
    """Class representing an interface to the OSM API."""

    _nominatim: Nominatim
    _overpass: Overpass
    _city: NominatimCity

    def __init__(self) -> OSM:
        """Initialise the class.

        Returns:
            OSM
        """
        self._nominatim = Nominatim()
        self._overpass = Overpass()

    def getCity(self, city_name: str) -> NominatimCity:
        """Get a city by name.

        Args:
            city_name (str): name of the city.

        Returns:
            NominatimCity
        """
        logging.debug(f"Getting city {city_name}")
        self._city = self._nominatim.findCity(city_name)
        logging.debug(f"Found city {self._city}")
        return self._city

    def getBuildings(self, city: NominatimCity, radius: int) -> list[Building]:
        """Get buildings in a city.

        Args:
            city (NominatimCity): city in which to search.
            radius (int): maximum distance from the city centre.

        Returns:
            list[Building]
        """
        logging.debug(
            f"Getting buildings around city {city.display_name}, "
            f"({city.lat}, {city.lon}) with radius {radius}"
        )
        buildings = self._overpass.getBuildings(
            city.lat,
            city.lon,
            radius,
        )
        logging.debug(f"Found {len(buildings)} buildings")
        return buildings

    def getRoads(self, city: NominatimCity, radius: int) -> list[Road]:
        """Get roads in a city.

        Args:
            city (NominatimCity): city in which to search.
            radius (int): maximum distance from the city centre.

        Returns:
            list[Road]
        """
        logging.debug(
            f"Getting roads around city {city.display_name}, "
            f"({city.lat}, {city.lon}) with radius {radius}"
        )
        roads = self._overpass.getRoads(
            city.lat,
            city.lon,
            radius,
        )
        logging.debug(f"Found {len(roads)} roads")
        return roads

    def getParks(self, city: NominatimCity, radius: int) -> list[Park]:
        """Get parks in a city.

        Args:
            city (NominatimCity): city in which to search.
            radius (int): maximum distance from the city centre.

        Returns:
            list[Park]
        """
        logging.debug(
            f"Getting parks around city {city.display_name}, "
            f"({city.lat}, {city.lon}) with radius {radius}"
        )
        parks = self._overpass.getParks(
            city.lat,
            city.lon,
            radius,
        )
        logging.debug(f"Found {len(parks)} parks")
        return parks

    def getWater(self, city: NominatimCity, radius: int) -> list[Water]:
        """Get water in a city.

        Args:
            city (NominatimCity): city in which to search.
            radius (int): maximum distance from the city centre.

        Returns:
            list[Water]
        """
        logging.debug(
            f"Getting water around city {city.display_name}, "
            f"({city.lat}, {city.lon}) with radius {radius}"
        )
        water = self._overpass.getWater(
            city.lat,
            city.lon,
            radius,
        )
        logging.debug(f"Found {len(water)} water")
        return water
