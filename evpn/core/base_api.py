import json
import time
from abc import abstractmethod
from subprocess import Popen, PIPE
from tempfile import gettempdir
import psutil
from .native_messaging import NativeMessaging
from .messages import MessagesV2

class Location:
    """
    Represents a VPN location with various attributes.

    This class encapsulates information about a VPN location, including its
    identifier, name, country code, and other relevant details.

    Attributes:
        id (str): Unique identifier for the location.
        name (str): Name of the location.
        country_code (str): Two-letter country code for the location.
        region (str, optional): Region within the country, if applicable.
        recommended (bool, optional): Indicates if the location is recommended.
        sort_order (int, optional): Order for sorting locations.
        protocols (list, optional): List of supported VPN protocols.
        is_smart_location (bool, optional): Indicates if it's a smart location.
        is_country (bool, optional): Indicates if it represents an entire country.
        coords (dict, optional): Geographic coordinates of the location.
    """
    def __init__(self, id, name, country_code, region=None, recommended=False,
                 sort_order=0, protocols=None, is_smart_location=False,
                 is_country=False, coords=None):
        self.id = id
        self.name = name
        self.country_code = country_code
        self.region = region
        self.recommended = recommended
        self.sort_order = sort_order
        self.protocols = protocols or []
        self.is_smart_location = is_smart_location
        self.is_country = is_country
        self.coords = coords or {}

class AppInfo:
    """
    Represents information about the application version.

    This class encapsulates details about the current version of the application,
    as well as information about the latest available version.

    Attributes:
        version (str): The current version of the application.
        latest_version (str, optional): The latest available version of the application.
        latest_version_url (str, optional): URL to download or view the latest version.
    """
    def __init__(self, version, latest_version=None, latest_version_url=None):
        self.version = version
        self.latest_version = latest_version
        self.latest_version_url = latest_version_url

class SubscriptionInfo:
    """
    Represents subscription information for a VPN service.

    This class encapsulates details about a user's VPN subscription,
    including its current status, plan type, and expiration date.

    Attributes:
        status (str): The current status of the subscription (e.g., 'active', 'expired').
        plan_type (str): The type of subscription plan (e.g., 'monthly', 'annual').
        expiration_date (str): The date when the subscription expires.
    """
    def __init__(self, status, plan_type, expiration_date):
        self.status = status
        self.plan_type = plan_type
        self.expiration_date = expiration_date

class Preferences:
    """
    Represents user preferences for VPN settings.

    This class encapsulates user-defined preferences for the VPN service,
    including the preferred protocol and traffic guard level.

    Attributes:
        preferred_protocol (str): The user's preferred VPN protocol.
        traffic_guard_level (str or int): The level of traffic guard protection.
    """
    def __init__(self, preferred_protocol, traffic_guard_level):
        self.preferred_protocol = preferred_protocol
        self.traffic_guard_level = traffic_guard_level

class BaseApi:
    """
    Base class for the ExpressVPN API.

    This class provides the core functionality for interacting with the ExpressVPN daemon,
    including methods for connecting, disconnecting, and retrieving status information.

    Attributes:
        EXTENSION_ID (str): The ID of the ExpressVPN browser extension.
        MESSAGE_API (NativeMessaging): An instance of the NativeMessaging class for communication.
    """

    EXTENSION_ID = "fgddmllnllkalaagkghckoinaemmogpe"
    MESSAGE_API = NativeMessaging()

    def __init__(self, debug=False):
        """
        Initialize the BaseApi instance.

        Args:
            debug (bool): If True, enables debug printing. Defaults to False.
        """
        self._messages = MessagesV2
        self._locations = None
        self._debug = debug
        self.is_new_protocol = False
        self._start_service()
        self._debug_print("Connecting To Daemon")
        self._wait_for_daemon(timeout=5)
        self._debug_print("Connected To Daemon")

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            BaseApi: The instance itself.
        """
        return self

    def __exit__(self, _type, value, traceback):
        """
        Exit the runtime context related to this object.

        Args:
            _type: The exception type if an exception was raised in the context.
            value: The exception value if an exception was raised in the context.
            traceback: The traceback if an exception was raised in the context.
        """
        self.close()

    def _wait_for_daemon(self, timeout):
        """
        Wait for the daemon to connect within the specified timeout.

        Args:
            timeout (float): The maximum time to wait for the daemon connection in seconds.

        Raises:
            TimeoutError: If the daemon doesn't connect within the specified timeout.
        """
        connected = False
        start_t = time.time()
        while not connected and time.time() - start_t < timeout:
            message = self._get_message()
            connected = message.get("connected")
            if connected:
                self.is_new_protocol = message.get("browser_helper_protocol", 1) == 2
            time.sleep(0.3)
        if not connected:
            raise TimeoutError("Can't connect to ExpressVPN daemon")

    def _debug_print(self, data):
        """
        Print debug information if debug mode is enabled.

        Args:
            data (str): The debug information to print.
        """
        if self._debug:
            print(data[:100] + "...")

    def _build_request(self, method, params=None):
        """
        Build a request dictionary based on the protocol version.

        Args:
            method (str): The method name for the request.
            params (dict, optional): The parameters for the request. Defaults to None.

        Returns:
            dict: A dictionary representing the request.
        """
        if self.is_new_protocol:
            return {
                "method": method.replace("XVPN.", ""),
                "params": params or {}
            }
        else:
            return {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": 200
            }

    def _get_message(self):
        """
        Get a message from the daemon process.

        Returns:
            dict: The received message as a dictionary.
        """
        message = self.MESSAGE_API.get_message(self._proc.stdout)
        self._debug_print(f"Got message: {json.dumps(message)}")
        return message

    def _send_message(self, message):
        """
        Send a message to the daemon process.

        Args:
            message (dict): The message to send.
        """
        self._debug_print("Sending: " + json.dumps(message))
        self._proc.stdout.flush()
        self.MESSAGE_API.send_message(
            self._proc.stdin, self.MESSAGE_API.encode_message(message, self.is_new_protocol))

    def _get_response(self):
        """
        Get a response from the daemon process.

        Returns:
            dict: The response message as a dictionary.

        Raises:
            Exception: If an error is received from the daemon.
        """
        while True:
            message = self.MESSAGE_API.get_message(self._proc.stdout)
            self._debug_print(f"Got message: {json.dumps(message)}")
            if message.get("type") in ("method", "result") or not message.get("name"):
                if "error" in message:
                    raise Exception(f"Error from daemon: {message['error']}")
                return message

    def _call(self, message: str, params=None):
        """
        Send a native message to the daemon and return the response.

        Args:
            message (str): The message to send.
            params (dict, optional): The parameters for the message. Defaults to None.

        Returns:
            dict: The response from the daemon.
        """
        req = self._build_request(message, params)
        self._send_message(req)
        return self._get_response()

    def _start_service(self):
        """
        Start the daemon service process.
        """
        path = self._service_path.absolute()
        self._proc = Popen([
            str(path),
            f"chrome-extension://{self.EXTENSION_ID}/"],
            stdout=PIPE, stdin=PIPE, stderr=PIPE,
            cwd=gettempdir()
        )

    def _get_locations(self):
        """
        Get the list of available VPN locations.

        Returns:
            dict: The response containing the list of locations.
        """
        return self._call(self._messages.get_locations)

    @property
    @abstractmethod
    def _program_proc_name(self):
        """
        Abstract property for the program process name.

        Returns:
            str: The name of the program process.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _program_path(self):
        """
        Abstract property for the program path.

        Returns:
            str: The path to the program executable.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _service_path(self):
        """
        Abstract property for the service path.

        Returns:
            str: The path to the service executable.
        """
        raise NotImplementedError

    def start_express_vpn(self):
        """
        Start the ExpressVPN application.
        """
        path = self._program_path
        Popen([path], start_new_session=True)

    @property
    def express_vpn_running(self):
        """
        Check if ExpressVPN is currently running.

        Returns:
            bool: True if ExpressVPN is running, False otherwise.
        """
        proc_names = [p.name() for p in psutil.process_iter()]
        return any(p in proc_names for p in self._program_proc_name)

    @property
    def is_connected(self):
        """
        Check if the VPN is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        status = self.get_status()
        return bool(status.get("info", {}).get("connected"))

    def get_location_id(self, name):
        """
        Get the location ID for a given location name.

        Args:
            name (str): The name of the location.

        Returns:
            str: The ID of the location.

        Raises:
            ValueError: If the location is not found.
        """
        found = next(
            (l for l in self._locations if l["name"].lower() == name.lower()), None)
        if not found:
            similar = next(
                (l for l in self._locations if name.lower() in l["name"].lower()), None)
            error_msg = f"Country {name} not found. "
            error_msg += f'Did you mean {similar.get("name")}?' if similar else ""
            raise ValueError(error_msg)
        return found["id"]

    def wait_for_connection(self, timeout=30):
        """
        Wait for the VPN connection to be established.

        Args:
            timeout (int): Maximum time to wait in seconds. Defaults to 30.

        Raises:
            TimeoutError: If the connection is not established within the timeout period.
        """
        start = time.time()
        while time.time() - start <= timeout:
            if self.is_connected:
                return
            time.sleep(0.3)
        raise TimeoutError("Connection timeout reached")

    def wait_for_disconnect(self, timeout=30):
        """
        Wait for the VPN to disconnect.

        Args:
            timeout (int): Maximum time to wait in seconds. Defaults to 30.

        Raises:
            TimeoutError: If the disconnection is not completed within the timeout period.
        """
        start = time.time()
        while time.time() - start <= timeout:
            if not self.is_connected:
                return
            time.sleep(0.3)
        raise TimeoutError("Disconnection timeout reached")

    def disconnect(self):
        """
        Disconnect from the VPN.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.disconnect)

    def get_status(self):
        """
        Get the current status of the VPN connection.

        Returns:
            dict: The status information.
        """
        return self._call(self._messages.get_status)

    def select_location(self, location_id):
        """
        Select a VPN location.

        Args:
            location_id (str): The ID of the location to select.

        Returns:
            dict: The response from the daemon.
        """
        params = {"selected_location": {"id": location_id}}
        return self._call(self._messages.select_location, params)

    def connect(self, location_id=None):
        """
        Connect to the VPN, optionally specifying a location.

        Args:
            location_id (str, optional): The ID of the location to connect to. Defaults to None.

        Returns:
            dict: The response from the daemon.
        """
        params = {"change_connected_location": self.is_connected}
        if location_id:
            params["id"] = location_id
        return self._call(self._messages.connect, params)

    def close(self):
        """
        Close the connection to the daemon and terminate the process.
        """
        time.sleep(1.5)
        self._proc.kill()

    @property
    @abstractmethod
    def locations(self):
        """
        Abstract property for getting the list of available locations.

        Returns:
            list: A list of Location objects.
        """
        raise NotImplementedError

    def get_engine_preferences(self):
        """
        Get the current engine preferences.

        Returns:
            dict: The engine preferences.
        """
        return self._call(self._messages.get_engine_preferences)

    def get_logs(self):
        """
        Get the VPN connection logs.

        Returns:
            dict: The log information.
        """
        return self._call(self._messages.get_logs)

    def cancel_speed_test(self):
        """
        Cancel an ongoing speed test.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.stop_speed_test)

    def retry_connect(self):
        """
        Retry the VPN connection.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.retry_connect)

    def reset(self):
        """
        Reset the VPN connection.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.reset)

    def sign_out(self):
        """
        Sign out from the VPN service.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.sign_out)

    def get_messages(self):
        """
        Get messages from the VPN service.

        Returns:
            dict: The messages from the daemon.
        """
        return self._call(self._messages.get_messages)

    def open_location_picker(self):
        """
        Open the location picker interface.

        Note: This method may not be applicable in a non-GUI environment.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.open_location_picker)

    def open_preferences(self):
        """
        Open the preferences interface.

        Note: This method may not be applicable in a non-GUI environment.

        Returns:
            dict: The response from the daemon.
        """
        return self._call(self._messages.open_preferences)

    def parse_location(self, location_data):
        """
        Parse raw location data into a Location object.

        Args:
            location_data (dict): Raw location data from the daemon.

        Returns:
            Location: A Location object representing the parsed data.
        """
        return Location(
            id=location_data['id'],
            name=location_data['name'],
            country_code=location_data['country_code'],
            region=location_data.get('region'),
            recommended=location_data.get('recommended', False),
            sort_order=location_data.get('sort_order', 0),
            protocols=location_data.get('protocols', []),
            is_smart_location=location_data.get('is_smart_location', False),
            is_country=location_data.get('is_country', False),
            coords=location_data.get('coords', {})
        )

    def parse_app_info(self, app_data):
        """
        Parse raw app info data into an AppInfo object.

        Args:
            app_data (dict): Raw app info data from the daemon.

        Returns:
            AppInfo: An AppInfo object representing the parsed data.
        """
        return AppInfo(
            version=app_data['version'],
            latest_version=app_data.get('latest_version'),
            latest_version_url=app_data.get('latest_version_url')
        )

    def parse_subscription_info(self, subscription_data):
        """
        Parse raw subscription data into a SubscriptionInfo object.

        Args:
            subscription_data (dict): Raw subscription data from the daemon.

        Returns:
            SubscriptionInfo: A SubscriptionInfo object representing the parsed data.
        """
        return SubscriptionInfo(
            status=subscription_data['status'],
            plan_type=subscription_data['plan_type'],
            expiration_date=subscription_data['expiration_date']
        )

    def parse_preferences(self, preferences_data):
        """
        Parse raw preferences data into a Preferences object.

        Args:
            preferences_data (dict): Raw preferences data from the daemon.

        Returns:
            Preferences: A Preferences object representing the parsed data.
        """
        return Preferences(
            preferred_protocol=preferences_data['preferred_protocol'],
            traffic_guard_level=preferences_data['traffic_guard_level']
        )

# Version number update
__version__ = "1.2.0"
