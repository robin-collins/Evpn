from pathlib import Path
from functools import lru_cache
from .base_api import BaseApi

class Location:
    """
    Represents a VPN location with various attributes.

    This class encapsulates information about a VPN location, including its
    identifier, geographical information, and various flags and properties.

    Attributes:
        id (str): Unique identifier for the location.
        name (str): Name of the location.
        country (str): Country where the location is situated.
        country_code (str): Two-letter country code.
        region (str): Region within the country.
        recommended (bool): Flag indicating if the location is recommended.
        sort_order (int): Order in which the location should be sorted.
        protocols (list): List of supported VPN protocols.
        is_smart_location (bool): Flag indicating if it's a smart location.
        is_country (bool): Flag indicating if it represents an entire country.
    """
    def __init__(self, id, name, country, country_code, region, recommended, sort_order, protocols, is_smart_location=False, is_country=False):
        """
        Initialize a new Location instance.

        Args:
            id (str): Unique identifier for the location.
            name (str): Name of the location.
            country (str): Country where the location is situated.
            country_code (str): Two-letter country code.
            region (str): Region within the country.
            recommended (bool): Whether the location is recommended.
            sort_order (int): Order in which the location should be sorted.
            protocols (list): List of supported VPN protocols.
            is_smart_location (bool, optional): Whether it's a smart location. Defaults to False.
            is_country (bool, optional): Whether it represents an entire country. Defaults to False.
        """
        self.id = id
        self.name = name
        self.country = country
        self.country_code = country_code
        self.region = region
        self.recommended = recommended
        self.sort_order = sort_order
        self.protocols = protocols
        self.is_smart_location = is_smart_location
        self.is_country = is_country

class MacApi(BaseApi):
    """Class for controlling ExpressVPN daemon on MacOS"""

    @property
    def _program_proc_name(self):
        return "ExpressVPN"

    @property
    def _program_path(self):
        return "/Applications/ExpressVPN.app/Contents/MacOS/ExpressVPN"

    @property
    def _service_path(self):
        return Path("/Applications/ExpressVPN.app/Contents/MacOS/expressvpn-browser-helper")

    @property
    @lru_cache()
    def locations(self):
        locations = self._get_locations()
        return [
            Location(
                id=i["id"],
                name=i["name"],
                country=i["country"],
                country_code=i["country_code"],
                region=i.get("region", ""),
                recommended=i.get("recommended", False),
                sort_order=i.get("sort_order", 0),
                protocols=i.get("protocols", []),
                is_smart_location=i.get("is_smart_location", False),
                is_country=i.get("is_country", False)
            ) for i in locations["locations"]
        ]

    def get_engine_preferences(self):
        return self._call(self._messages.get_engine_preferences)

    def get_logs(self):
        return self._call(self._messages.get_logs)

    def cancel_speed_test(self):
        return self._call(self._messages.stop_speed_test)

    def retry_connect(self):
        return self._call(self._messages.retry_connect)

    def reset(self):
        return self._call(self._messages.reset)

    def sign_out(self):
        return self._call(self._messages.sign_out)

    def open_location_picker(self):
        return self._call(self._messages.open_location_picker)

    def open_preferences(self):
        return self._call(self._messages.open_preferences)
