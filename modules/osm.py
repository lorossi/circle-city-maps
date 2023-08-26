from __future__ import annotations

import logging

from modules.nominatim import Nominatim, NominatimCity
from modules.overpass import Overpass, Building


class OSM:
    _nominatim: Nominatim
    _overpass: Overpass
    _city: NominatimCity

    def __init__(self) -> OSM:
        self._nominatim = Nominatim()
        self._overpass = Overpass()

    def getCity(self, city_name: str) -> NominatimCity:
        logging.info(f"Getting city {city_name}")
        self._city = self._nominatim.findCity(city_name)
        logging.info(f"Found city {self._city}")
        return self._city

    def getBuildings(self, city: NominatimCity, radius: int) -> list[Building]:
        logging.info(
            f"Getting buildings around {city.lat},{city.lon} with radius {radius}"
        )
        buildings = self._overpass.getBuildings(
            city.lat,
            city.lon,
            radius,
        )
        logging.info(f"Found {len(buildings)} buildings")
        return buildings
