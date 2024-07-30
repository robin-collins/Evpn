from pathlib import Path
from functools import lru_cache
from subprocess import call
from typing import List, Dict, Any
from .base_api import BaseApi, Location

class LinuxApi(BaseApi):
    """Class for controlling ExpressVPN daemon on Linux"""

    @property
    def _program_proc_name(self) -> str:
        return "ExpressVPN"

    @property
    def _program_path(self) -> str:
        return "/usr/bin/expressvpn"

    @property
    def _service_path(self) -> Path:
        return Path("/usr/bin/expressvpn-browser-helper")

    @property
    @lru_cache
    def locations(self) -> List[Location]:
        locations_data = self._get_locations()
        return [
            Location(
                id=loc["id"],
                name=loc["country"],
                country_code=loc["country_code"],
                region=loc.get("region", ""),
                recommended=loc.get("recommended", False),
                sort_order=loc.get("sort_order", 0),
                protocols=loc.get("protocols", []),
                is_smart_location=loc.get("is_smart_location", False),
                is_country=loc.get("is_country", False),
                coords=loc.get("coords", {"lat": 0, "lon": 0})
            )
            for loc in locations_data["locations"]
        ]

    def start_express_vpn(self) -> bool:
        stat = call(["systemctl", "start", "--quiet", "expressvpn.service"])
        return stat == 0

    @property
    def express_vpn_running(self) -> bool:
        stat = call(["systemctl", "is-active", "--quiet", "expressvpn.service"])
        return stat == 0

    def get_engine_preferences(self) -> Dict[str, Any]:
        return self._call(self._messages.get_engine_preferences)

    def get_logs(self) -> str:
        return self._call(self._messages.get_logs)

    def cancel_speed_test(self) -> None:
        self._call(self._messages.stop_speed_test)

    def retry_connect(self) -> None:
        self._call(self._messages.retry_connect)

    def reset(self) -> None:
        self._call(self._messages.reset)

    def open_location_picker(self) -> None:
        self._call(self._messages.open_location_picker)

    def open_preferences(self) -> None:
        self._call(self._messages.open_preferences)

# Additional requirements:
# - Update BaseApi class to include new methods and updated Location class
# - Update _messages in BaseApi to include new message types
# - Implement error handling for new methods
# - Update typing information for all methods
