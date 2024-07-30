# pylint: disable=too-few-public-methods
class MessagesV1:
    """
    Native messaging messages
    For current version on Windows
    """
    get_locations = "GetLocations"
    get_status = "GetStatus"
    connect = "Connect"
    disconnect = "Disconnect"


class MessagesV2:
    """
    Native messaging messages
    For Linux, MacOS and old version on Windows
    """
    get_locations = "GetLocations"
    get_status = "GetStatus"
    connect = "Connect"
    disconnect = "Disconnect"
    get_engine_preferences = "GetEnginePreferences"
    get_logs = "GetLogs"
    stop_speed_test = "StopSpeedTest"
    retry_connect = "RetryConnect"
    reset = "Reset"
    sign_out = "SignOut"
    open_location_picker = "OpenLocationPicker"
    open_chrome_preferences = "OpenChromePreferences"
    open_preferences = "OpenPreferences"
    select_location = "SelectLocation"
    get_messages = "GetMessages"  # Added this line

# Version number update
__version__ = "1.1.1"
