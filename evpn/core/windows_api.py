import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Any
import subprocess
import psutil
from .base_api import BaseApi, Location





class WindowsApi(BaseApi):
    """Class for controlling ExpressVPN daemon on Windows"""

    @property
    def _program_proc_name(self) -> List[str]:
        return [
            "ExpressVPN.exe",
            "expressvpnd.exe"
        ]

    @property
    def _program_path(self) -> str:
        return "C:\\Program Files (x86)\\ExpressVPN\\expressvpn-ui\\ExpressVPN.exe"

    @property
    def _service_path(self) -> Path:
        paths = [
            Path("C:\\Program Files (x86)\\ExpressVPN\\services\\ExpressVPN.BrowserHelper.exe"),
            Path("C:\\Program Files (x86)\\ExpressVPN\\expressvpnd\\expressvpn-browser-helper.exe")
        ]
        for path in paths:
            if path.exists():
                return path
        raise FileNotFoundError("ExpressVPN browser helper service not found")

    @property
    @lru_cache()
    def locations(self) -> List[Dict[str, Any]]:
        """
        Get list of locations with updated fields

        Returns:
            List[Dict[str, Any]]: List of location dictionaries with updated fields
        """
        locs = self._get_locations()
        self._locations = [
            Location(
                id=i["id"],
                name=i["name"],
                country_code=i["country_code"],
                region=i.get("region", ""),
                recommended=i.get("recommended", False),
                sort_order=i.get("sort_order", 0),
                protocols=i.get("protocols", []),
                is_smart_location=i.get("is_smart_location", False),
                is_country=i.get("is_country", False),
                coords=i.get("coords", {"lat": 0, "lon": 0})
            )
            for i in locs["locations"]
        ]
        return self._locations

    def get_engine_preferences(self) -> Dict[str, Any]:
        """
        Get engine preferences

        Returns:
            Dict[str, Any]: Engine preferences
        """
        return self._call(self._messages.get_engine_preferences)

    def get_logs(self) -> str:
        """
        Get connection logs

        Returns:
            str: Connection logs
        """
        return self._call(self._messages.get_logs)

    def cancel_speed_test(self) -> None:
        """Cancel ongoing speed test"""
        self._call(self._messages.stop_speed_test)

    def retry_connect(self) -> None:
        """Retry connection"""
        self._call(self._messages.retry_connect)

    def reset(self) -> None:
        """Reset ExpressVPN"""
        self._call(self._messages.reset)

    def sign_out(self) -> None:
        """Sign out from ExpressVPN"""
        self._call(self._messages.sign_out)

    def open_location_picker(self) -> None:
        """Open location picker"""
        self._call(self._messages.open_location_picker)

    def open_preferences(self) -> None:
        """Open preferences"""
        self._call(self._messages.open_preferences)

    def is_installed(self) -> bool:
        """
        Check if ExpressVPN is installed

        Returns:
            bool: True if installed, False otherwise
        """
        return os.path.exists(self._program_path) and os.path.exists(str(self._service_path))

    def start_express_vpn(self) -> None:
        """Start ExpressVPN application"""
        subprocess.Popen(self._program_path)

    @property
    def express_vpn_running(self) -> bool:
        """
        Check if ExpressVPN is running

        Returns:
            bool: True if running, False otherwise
        """
        return any(proc.name() in self._program_proc_name for proc in psutil.process_iter())
