"""Intex Pool integration."""
from __future__ import annotations

import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import IntexApi
from .const import (CONF_COUNTRY, CONF_DEVICE_ID, CONF_GID, CONF_SCAN_INTERVAL,
                    DEFAULT_SCAN_INTERVAL, DOMAIN)
from .coordinator import IntexPoolCoordinator

PLATFORMS = [Platform.SENSOR]

CARD_URL = "/intex_pool/intex-pool-card.js"
ICON_URL = "/intex_pool/icon.png"


async def _register_card(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_card_registered"):
        return
    www = os.path.join(os.path.dirname(__file__), "www")
    files = [(CARD_URL, os.path.join(www, "intex-pool-card.js")),
             (ICON_URL, os.path.join(www, "icon.png"))]
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(url, path, cache_headers=False) for url, path in files])
    except (ImportError, AttributeError):
        # HA < 2024.6: synchronous API
        for url, path in files:
            hass.http.register_static_path(url, path, cache_headers=False)
    from homeassistant.components.frontend import add_extra_js_url
    add_extra_js_url(hass, CARD_URL)
    hass.data[f"{DOMAIN}_card_registered"] = True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the Lovelace card once at component load, so it is available even
    if a config entry later fails to set up (e.g. cloud rate-limit)."""
    await _register_card(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await _register_card(hass)
    session = async_get_clientsession(hass)
    # Reuse the session captured at config time so setup doesn't log in again
    # (Tuya rate-limits the login endpoint).
    api = IntexApi(session, entry.data[CONF_DEVICE_ID],
                   sid=entry.data.get("sid", ""), ecode=entry.data.get("ecode", ""))
    coordinator = IntexPoolCoordinator(
        hass, entry, api, gid=entry.data[CONF_GID],
        interval_min=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        creds=(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD], entry.data[CONF_COUNTRY]))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
