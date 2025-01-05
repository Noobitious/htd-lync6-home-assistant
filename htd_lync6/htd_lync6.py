import socket
import logging
import math

MAX_HTD_VOLUME = 60
DEFAULT_HTD_LYNC6_PORT = 10006

_LOGGER = logging.getLogger(__name__)

class HtdLync6Client:
    """
    Client for communicating with the HTD Lync6 hardware.
    Provides methods for controlling zones and querying their states.
    """

    def __init__(self, ip_address, port=DEFAULT_HTD_LYNC6_PORT):
        self.ip_address = ip_address
        self.port = port
        self.zones = {
            k: {
                "zone": k,
                "power": None,
                "input": None,
                "vol": None,
                "mute": None,
                "source": None,
            } for k in range(1, 7)
        }

    def parse(self, cmd, message, zone_number):
        """
        Parse the response message from the HTD controller.
        :param cmd: Command sent to the controller.
        :param message: Response received from the controller.
        :param zone_number: Zone number related to the query.
        :return: Parsed data for zones.
        """
        _LOGGER.debug(f"Parsing message for zone {zone_number}: {message}")

        if len(message) > 14:
            # Split the message into chunks for each zone (14 bytes each)
            zones = [message[i:i + 14] for i in range(14, len(message), 14)]

            success = False
            for i, zone_data in enumerate(zones):
                if self.parse_message(cmd, zone_data, i + 1):
                    success = True

            if not success:
                _LOGGER.warning(f"Update for Zone #{zone_number} failed.")
        elif len(message) == 14:
            self.parse_message(cmd, message, zone_number)

        return self.zones if zone_number is None else self.zones[zone_number]

    def parse_message(self, cmd, message, zone_number):
        """
        Parse a 14-byte message for a specific zone.
        :param cmd: Command sent to the controller.
        :param message: Response received from the controller.
        :param zone_number: Zone number related to the query.
        :return: True if parsing is successful, False otherwise.
        """
        if len(message) != 14:
            _LOGGER.error(f"Invalid message length for Zone {zone_number}: {message}")
            return False

        zone = message[2]
        if zone in range(1, 7):
            self.zones[zone]["power"] = "on" if (message[4] & 1 << 0) >> 0 else "off"
            self.zones[zone]["source"] = message[8] + 1
            self.zones[zone]["vol"] = message[9] - 196 if message[9] else 0
            self.zones[zone]["mute"] = "on" if (message[4] & 1 << 1) >> 1 else "off"

            _LOGGER.debug(
                f"Zone #{zone} updated (requested #{zone_number}): {self.zones[zone]}"
            )
            return True
        else:
            _LOGGER.warning(
                f"Command for Zone #{zone_number} returned invalid Zone #{zone}: {message}"
            )

        return False

    def set_source(self, zone, input):
        """
        Set the source input for a specific zone.
        :param zone: Zone number.
        :param input: Input number (1-12).
        """
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return

        if input not in range(1, 13):
            _LOGGER.warning(f"Invalid Input: {input}")
            return

        input_code = input + 15 if input < 13 else input + 86
        cmd = bytearray([0x02, 0x00, zone, 0x04, input_code])
        self.send_command(cmd, zone)

    def set_volume(self, zone, vol):
        """
        Set the volume level for a specific zone.
        :param zone: Zone number.
        :param vol: Volume level (0-100).
        """
        if vol not in range(0, 101):
            _LOGGER.warning(f"Invalid Volume: {vol}")
            return

        volume_int = int(math.floor(MAX_HTD_VOLUME * vol / 100))
        volume = 0x00 if volume_int == 60 else 0xFF - (59 - volume_int)

        cmd = bytearray([0x02, 0x01, zone, 0x15, volume])
        self.send_command(cmd, zone)

    def toggle_mute(self, zone, mute):
        """
        Toggle mute state for a specific zone.
        :param zone: Zone number.
        :param mute: True to mute, False to unmute.
        """
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x1E if mute else 0x1F])
        self.send_command(cmd, zone)

    def query_zone(self, zone):
        """
        Query the current state of a specific zone.
        :param zone: Zone number.
        :return: Zone state data.
        """
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return None

        cmd = bytearray([0x02, 0x00, zone, 0x05, 0x00])
        return self.send_command(cmd, zone)

    def query_all(self):
        """
        Query the state of all zones.
        :return: All zones state data.
        """
        cmd = bytearray([0x02, 0x00, 0x00, 0x05, 0x00])
        return self.send_command(cmd)

    def set_power(self, zone, power):
        """
        Set the power state of a specific zone.
        :param zone: Zone number.
        :param power: 1 to turn on, 0 to turn off.
        """
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x57 if power else 0x58])
        self.send_command(cmd, zone)

    def send_command(self, cmd, zone=None):
        """
        Send a command to the HTD controller and parse the response.
        :param cmd: Command to send.
        :param zone: Zone number.
        :return: Parsed response data.
        """
        cmd.append(self.checksum(cmd))
        _LOGGER.debug(f"Sending command: {cmd}")

        try:
            with socket.create_connection((self.ip_address, self.port), timeout=1) as sock:
                sock.sendall(cmd)
                data = sock.recv(1024)

            _LOGGER.debug(f"Response received: {data}")
            return self.parse(cmd, data, zone)
        except (socket.timeout, ConnectionError) as e:
            _LOGGER.error(f"Failed to communicate with HTD controller: {e}")
            return None

    def checksum(self, message):
        """
        Calculate the checksum for a command message.
        :param message: Command message.
        :return: Checksum value.
        """
        return sum(message) & 0xFF
