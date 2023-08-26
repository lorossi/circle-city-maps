from __future__ import annotations

import hashlib
import json
import logging
import os

import requests

from modules.data import Data


class ApiRequest(Data):
    timestamp: int
    url: str
    response: str

    @property
    def response_json(self) -> dict:
        return json.loads(self.response)


class ApiError(Exception):
    pass


class ApiInterface:
    def __init__(self, cache_folder: str = "cache") -> ApiInterface:
        self._cache_folder = cache_folder
        logging.info(f"Using cache folder {self._cache_folder}")
        if not os.path.exists(self._cache_folder):
            os.makedirs(self._cache_folder)
            logging.info(f"Created cache folder {self._cache_folder}")

    def makeRequest(self, url: str) -> ApiRequest:
        logging.info(f"Making request to {url}")

        filename = hashlib.md5(url.encode("utf-8")).hexdigest()
        cache_file = os.path.join(self._cache_folder, f"{filename}.json")

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
