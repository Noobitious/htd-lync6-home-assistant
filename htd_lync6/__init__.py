"""
Home Assistant integration for the HTD Lync6 system.
This module handles the configuration and setup of the integration.
It provides the connection between the HTD Lync6 hardware and Home Assistant entities.
"""

import voluptuous as vol
from homeassistant.helpers import discovery
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.typing import ConfigType
import logging

from .htd_lync6 import DEFAULT_HTD_LYNC6_PORT, HtdLync6Client

_LOGGER = logging.getLogger(__name__)

DOMAIN = "htd_lync6"
CONF_ZONES = "zones"
CONF_SOURCES = "sources"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_HTD_LYNC6_PORT): int,
                vol.Optional(CONF_ZONES, default=[]): vol.All(vol.Coerce(list), [str]),
                vol.Optional(CONF_SOURCES, default=[]): vol.All(vol.Coerce(list), [str]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass, config: ConfigType):
    """
    Set up the HTD Lync6 integration using YAML configuration.
    This method initializes the client and prepares data for entity setup.
    """
    htd_config = config.get(DOMAIN)

    if not htd_config:
        _LOGGER.error("HTD Lync6 configuration is missing from configuration.yaml.")
        return False

    host = htd_config[CONF_HOST]
    port = htd_config[CONF_PORT]
    zones = htd_config.get(CONF_ZONES, [])
    sources = htd_config.get(CONF_SOURCES, [])

    # Fill in defaults if zones or sources are incomplete
    for i in range(len(zones), 6):
        zones.append(f"Zone {i + 1}")
    for i in range(len(sources), 12):
        sources.append(f"Source {i + 1}")

    # Initialize the client and store it in hass.data
    try:
        client = HtdLync6Client(host, port)
        hass.data[DOMAIN] = {
            "client": client,
            "zones": zones,
            "sources": sources,
        }
        _LOGGER.info("HTD Lync6 client initialized successfully.")
    except Exception as e:
        _LOGGER.error(f"Failed to initialize HTD Lync6 client: {e}")
        return False

    # Load platforms
    for component in ["media_player"]:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
