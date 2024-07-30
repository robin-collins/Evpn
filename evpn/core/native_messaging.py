import struct
import sys
import json


class NativeMessaging:
    """
    Class for sending native messages using native messaging protocol
    https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging
    """

    @staticmethod
    def get_message(fd):
        """
        Read a message from the file descriptor.

        Args:
            fd: File descriptor to read from.

        Returns:
            dict: Decoded message.
        """
        raw_length = fd.read(4)
        if len(raw_length) == 0:
            sys.exit(0)
        message_length = struct.unpack("@I", raw_length)[0]
        message = fd.read(message_length).decode("utf-8")
        return json.loads(message)

    @staticmethod
    def encode_message(message_content, is_new_protocol=False):
        """
        Encode a message for transmission, given its content.

        Args:
            message_content (dict): The message content to encode.
            is_new_protocol (bool): Flag to indicate if the new protocol should be used.

        Returns:
            dict: Encoded message with length and content.
        """
        if is_new_protocol:
            # For new protocol, only include method and params
            encoded_content = json.dumps({
                "method": message_content.get("method"),
                "params": message_content.get("params", {})
            }).encode("utf-8")
        else:
            # For old protocol, include all fields
            encoded_content = json.dumps(message_content).encode("utf-8")

        encoded_length = struct.pack("@I", len(encoded_content))
        return {"length": encoded_length, "content": encoded_content}

    @staticmethod
    def send_message(fd, encoded_message):
        """
        Send an encoded message to stdout.

        Args:
            fd: File descriptor to write to.
            encoded_message (dict): The encoded message to send.
        """
        fd.write(encoded_message["length"])
        fd.write(encoded_message["content"])
        fd.flush()

    def __init__(self):
        """Initialize the NativeMessaging class."""
        self.is_new_protocol = False  # Flag to determine which protocol to use

    def set_protocol_version(self, is_new_protocol):
        """
        Set the protocol version to use.

        Args:
            is_new_protocol (bool): True if using the new protocol, False otherwise.
        """
        self.is_new_protocol = is_new_protocol

    def encode_and_send_message(self, fd, message_content):
        """
        Encode and send a message using the appropriate protocol.

        Args:
            fd: File descriptor to write to.
            message_content (dict): The message content to encode and send.
        """
        encoded_message = self.encode_message(message_content, self.is_new_protocol)
        self.send_message(fd, encoded_message)
