"""Module for interfacing with the API and caching responses."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time

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
        logging.debug(f"Using cache folder {self._cache_folder}")
        if not os.path.exists(self._cache_folder):
            os.makedirs(self._cache_folder)
            logging.debug(f"Created cache folder {self._cache_folder}")

    def _requestUrl(self, url: str, max_retries: int, max_timeout: int) -> str:
        logging.debug(f"Making request to {url}")
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=max_timeout)
                if response.status_code != 200:
                    logging.error(
                        f"Request failed with status code {response.status_code}"
                    )
                return response.text
            except requests.exceptions.Timeout:
                logging.warning(f"Request timed out, retrying ({i+1}/{max_retries})")
                continue

        logging.error(f"Request failed after {max_retries} retries")
        raise ApiError(f"Request failed after {max_retries} retries")

    def _loadCache(self, filename: str) -> ApiRequest:
        cache_file = os.path.join(self._cache_folder, f"{filename}.json")
        logging.debug(f"Loading cache from {cache_file}")
        if os.path.exists(cache_file):
            logging.debug(f"Using cached response from {cache_file}")
            with open(cache_file, "r") as f:
                logging.debug("Returning response")
                cached_response = ApiRequest.from_json(f.read())
                return cached_response
        else:
            logging.debug("No cached response found")
            return None

    def _saveCache(self, filename: str, api_request: ApiRequest) -> None:
        cache_file = os.path.join(self._cache_folder, f"{filename}.json")
        logging.debug(f"Caching response to {cache_file}")
        with open(cache_file, "w") as f:
            f.write(api_request.to_json())

    def makeRequest(
        self,
        url: str,
        max_retries: int = 3,
        max_timeout: int = 10,
        cache_expire: bool = False,
        cached_age: int = 3600,
    ) -> ApiRequest:
        """Make a GET request to an url, caching the response in a file inside the \
            cache folder.

        Args:
            url (str): url to make the request to
            max_retries (int, optional): maximum number of retries. Defaults to 3.
            max_timeout (int, optional): maximum timeout in seconds. Defaults to 10.
            cache_expire (bool, optional): whether the cached response expires. \
                Defaults to False.
            cached_age (int, optional): maximum age of the cached response in seconds. \
                Defaults to 3600.

        Raises:
            ApiError: if the request fails

        Returns:
            ApiRequest: the response to the request
        """
        logging.debug(f"Making request to {url}")

        filename = hashlib.md5(url.encode("utf-8")).hexdigest()
        cached_request = self._loadCache(filename)
        if cached_request is not None:
            if time.time() - cached_request.timestamp < cached_age or not cache_expire:
                logging.debug("Returning cached response")
                return cached_request

            logging.debug("Cached response expired, making new request")

        response = self._requestUrl(url, max_retries, max_timeout)

        api_request = ApiRequest(
            timestamp=time.time(),
            url=url,
            response=response,
        )

        self._saveCache(filename, api_request)

        logging.debug("Returning response")
        return api_request
