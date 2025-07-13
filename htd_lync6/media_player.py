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
    Represents a single zone of the HTD Lync6 system as a media player.
    """

    def __init__(self, client, zone, zone_name, sources):
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
        return SUPPORT_HTD_LYNC6

    @property
    def name(self):
        return self._zone_name

    @property
    def state(self):
        return self._state

    def turn_on(self):
        self._client.set_power(self._zone, 1)
        self.update()

    def turn_off(self):
        self._client.set_power(self._zone, 0)
        self.update()

    @property
    def volume_level(self):
        return self._volume / 100

    def set_volume_level(self, volume):
        self._client.set_volume(self._zone, int(volume * 100))
        self.update()

    @property
    def is_volume_muted(self):
        return self._is_muted

    def mute_volume(self, mute):
        self._client.toggle_mute(self._zone, mute)
        self.update()

    @property
    def source(self):
        return self._source

    @property
    def source_list(self):
        return self._sources

    def select_source(self, source):
        if source in self._sources:
            source_index = self._sources.index(source) + 1
            self._client.set_source(self._zone, source_index)
            self.update()
        else:
            _LOGGER.warning(f"Source '{source}' not available in zone {self._zone}.")

    def update(self):
        try:
            zone_info = self._client.query_zone(self._zone)
            if not zone_info:
                _LOGGER.warning(f"No data received for zone {self._zone}")
                return

            self._state = STATE_ON if zone_info["power"] == "on" else STATE_OFF
            self._volume = zone_info["vol"]
            self._is_muted = zone_info["mute"] == "on"
            self._source = (
                self._sources[zone_info["source"] - 1]
                if zone_info["source"] and 0 < zone_info["source"] <= len(self._sources)
                else None
            )
            _LOGGER.debug(f"Zone {self._zone} updated: {zone_info}")

        except Exception as e:
            _LOGGER.error(f"Failed to update zone {self._zone}: {e}")
