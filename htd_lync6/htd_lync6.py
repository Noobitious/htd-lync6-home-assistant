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
        Parse the response from the controller and extract valid 14-byte zone packets only.
        """
        _LOGGER.debug(f"Parsing message for zone {zone_number}: {message.hex()}")

        if not message or len(message) < 14:
            _LOGGER.warning(f"Incomplete or empty message received: {message}")
            return self.zones.get(zone_number)

        valid_chunks = []
        for i in range(0, len(message) - 13):
            chunk = message[i:i+14]
            if chunk[0] == 0x02 and chunk[1] == 0x00 and chunk[3] == 0x05:
                valid_chunks.append(chunk)

        if not valid_chunks:
            _LOGGER.warning(f"No valid zone records found in message: {message}")
            return self.zones.get(zone_number)

        for chunk in valid_chunks:
            self.parse_message(cmd, chunk, chunk[2])  # zone_number inferred from chunk

        return self.zones if zone_number is None else self.zones.get(zone_number)

    def parse_message(self, cmd, message, zone_number):
        """
        Parse a 14-byte message for a specific zone.
        """
        if len(message) != 14:
            _LOGGER.error(f"Invalid message length for Zone {zone_number}: {message}")
            return False

        zone = message[2]
        if zone in range(1, 7):
            self.zones[zone]["power"] = "on" if (message[4] & 1 << 0) else "off"
            self.zones[zone]["source"] = message[8] + 1
            self.zones[zone]["vol"] = message[9] - 196 if message[9] else 0
            self.zones[zone]["mute"] = "on" if (message[4] & 1 << 1) else "off"

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
        if vol not in range(0, 101):
            _LOGGER.warning(f"Invalid Volume: {vol}")
            return

        volume_int = int(math.floor(MAX_HTD_VOLUME * vol / 100))
        volume = 0x00 if volume_int == 60 else 0xFF - (59 - volume_int)
        cmd = bytearray([0x02, 0x01, zone, 0x15, volume])
        self.send_command(cmd, zone)

    def toggle_mute(self, zone, mute):
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x1E if mute else 0x1F])
        self.send_command(cmd, zone)

    def query_zone(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return None

        cmd = bytearray([0x02, 0x00, zone, 0x05, 0x00])
        return self.send_command(cmd, zone)

    def query_all(self):
        cmd = bytearray([0x02, 0x00, 0x00, 0x05, 0x00])
        return self.send_command(cmd)

    def set_power(self, zone, power):
        if zone not in range(1, 7):
            _LOGGER.warning(f"Invalid Zone: {zone}")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x57 if power else 0x58])
        self.send_command(cmd, zone)

    def send_command(self, cmd, zone=None):
        cmd.append(self.checksum(cmd))
        _LOGGER.debug(f"Sending command: {cmd}")

        try:
            with socket.create_connection((self.ip_address, self.port), timeout=1) as sock:
                sock.sendall(cmd)
                data = sock.recv(2048)

            if not data:
                _LOGGER.warning(f"No response received for command: {cmd}")
                return None

            _LOGGER.debug(f"Response received: {data}")
            return self.parse(cmd, data, zone)
        except (socket.timeout, ConnectionError) as e:
            _LOGGER.error(f"Failed to communicate with HTD controller: {e}")
            return None

    def checksum(self, message):
        return sum(message) & 0xFF
