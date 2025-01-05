import logging
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define the supported features for the HTD Lync6 media player
SUPPORT_HTD_LYNC6 = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """
    Set up HTD Lync6 media player entities from the YAML configuration.
    This function initializes media player entities based on zones and sources defined in the integration.
    """
    htd_data = hass.data.get(DOMAIN)
    if not htd_data:
        _LOGGER.error("HTD Lync6 integration data not found in hass.data.")
        return

    client = htd_data["client"]
    zones = htd_data["zones"]
    sources = htd_data["sources"]

    _LOGGER.debug(f"Setting up media player entities: zones={zones}, sources={sources}")

    entities = []
    for i, zone_name in enumerate(zones, start=1):
        _LOGGER.debug(f"Creating media player entity for zone: {zone_name} (Zone {i})")
        entities.append(HtdLync6MediaPlayer(client, i, zone_name, sources))

    async_add_entities(entities, update_before_add=True)
    _LOGGER.debug("Media player entities added successfully.")

class HtdLync6MediaPlayer(MediaPlayerEntity):
    """
    Represents a single zone of the HTD Lync6 system as a media player in Home Assistant.
    Includes basic media player features like power control, volume adjustment, and source selection.
    """
    def __init__(self, client, zone, zone_name, sources):
        """
        Initialize the media player entity for a specific zone.
        :param client: The HTD Lync6 client for communication.
        :param zone: The zone number (1-6).
        :param zone_name: The user-friendly name of the zone.
        :param sources: The list of available audio sources.
        """
        self._client = client
        self._zone = zone
        self._zone_name = zone_name
        self._sources = sources
        self._state = STATE_UNKNOWN
        self._volume = 0
        self._is_muted = False
        self._source = None
        self.update()

    @property
    def supported_features(self):
        """Return the supported features for this media player."""
        return SUPPORT_HTD_LYNC6

    @property
    def name(self):
        """Return the name of the zone."""
        return self._zone_name

    @property
    def state(self):
        """Return the current state of the zone."""
        return self._state

    def turn_on(self):
        """Turn the zone on."""
        self._client.set_power(self._zone, 1)
        self.update()

    def turn_off(self):
        """Turn the zone off."""
        self._client.set_power(self._zone, 0)
        self.update()

    @property
    def volume_level(self):
        """Return the volume level of the zone (0-1 scale)."""
        return self._volume / 100

    def set_volume_level(self, volume):
        """Set the volume level of the zone."""
        self._client.set_volume(self._zone, int(volume * 100))
        self.update()

    @property
    def is_volume_muted(self):
        """Return whether the volume is muted."""
        return self._is_muted

    def mute_volume(self, mute):
        """Mute or unmute the volume."""
        self._client.toggle_mute(self._zone, mute)
        self.update()

    @property
    def source(self):
        """Return the currently selected source."""
        return self._source

    @property
    def source_list(self):
        """Return the list of available sources."""
        return self._sources

    def select_source(self, source):
        """Select a new source."""
        if source in self._sources:
            source_index = self._sources.index(source) + 1
            self._client.set_source(self._zone, source_index)
            self.update()
        else:
            _LOGGER.warning(f"Source {source} not available in zone {self._zone}.")

    def update(self):
        """Fetch the latest state of the zone from the controller."""
        try:
            zone_info = self._client.query_zone(self._zone)
            self._state = STATE_ON if zone_info["power"] == "on" else STATE_OFF
            self._volume = zone_info["vol"]
            self._is_muted = zone_info["mute"] == "on"
            self._source = self._sources[zone_info["source"] - 1] if zone_info["source"] > 0 else None
            _LOGGER.debug(f"Zone {self._zone} updated: {zone_info}")
        except Exception as e:
            _LOGGER.error(f"Failed to update zone {self._zone}: {e}")
