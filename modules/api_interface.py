"""Module for interfacing with the API and caching responses."""
from __future__ import annotations

import hashlib
import json
import logging
import os

import requests

from modules.data import Data


class ApiRequest(Data):
    """Class representing a request to the API."""

    timestamp: int
    url: str
    response: str

    @property
    def response_json(self) -> dict:
        """Return the json response as a dict.

        Returns:
            dict
        """
        return json.loads(self.response)


class ApiError(Exception):
    """Class representing an error from the API."""

    pass


class ApiInterface:
    """Class representing an interface to the API."""

    def __init__(self, cache_folder: str = "cache") -> ApiInterface:
        """Initialise the class.

        Args:
            cache_folder (str, optional): folder in which the requests will be stored. \
            Defaults to "cache".

        Returns:
            ApiInterface
        """
        self._cache_folder = cache_folder
        logging.info(f"Using cache folder {self._cache_folder}")
        if not os.path.exists(self._cache_folder):
            os.makedirs(self._cache_folder)
            logging.info(f"Created cache folder {self._cache_folder}")

    def makeRequest(self, url: str) -> ApiRequest:
        """Make a GET request to an url, caching the response in a file inside the \
            cache folder.

        Args:
            url (str): url to make the request to

        Raises:
            ApiError: if the request fails

        Returns:
            ApiRequest: the response to the request
        """
        logging.info(f"Making request to {url}")

        filename = hashlib.md5(url.encode("utf-8")).hexdigest()
        cache_file = os.path.join(self._cache_folder, f"{filename}.toml")

        if os.path.exists(cache_file):
            logging.info(f"Using cached response from {cache_file}")
            with open(cache_file, "r") as f:
                logging.info("Returning response")
                return ApiRequest.from_json(f.read())

        logging.info(f"Making request to {url}")
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f"Request failed with status code {response.status_code}")
            raise ApiError(f"Request failed with status code {response.status_code}")

        api_request = ApiRequest(
            timestamp=response.headers["Date"],
            url=url,
            response=response.text,
        )

        logging.info(f"Caching response to {cache_file}")
        with open(cache_file, "w") as f:
            f.write(api_request.to_json())

        logging.info("Returning response")
        return api_request
