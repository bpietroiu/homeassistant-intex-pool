"""Config flow for Intex Pool."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IntexApi, IntexApiError, IntexAuthError, generate_device_id
from .const import (CONF_COUNTRY, CONF_DEVICE_ID, CONF_GID, CONF_SCAN_INTERVAL,
                    DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL)

USER_SCHEMA = vol.Schema({
    vol.Required(CONF_EMAIL): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_COUNTRY, default="40"): str,
})


class IntexPoolConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            device_id = generate_device_id()
            api = IntexApi(session, device_id)
            try:
                await api.login(user_input[CONF_EMAIL], user_input[CONF_PASSWORD],
                                user_input[CONF_COUNTRY])
                homes = await api.homes()
            except IntexAuthError:
                errors["base"] = "invalid_auth"
            except IntexApiError:
                errors["base"] = "cannot_connect"
            else:
                gid = homes[0]["gid"] if homes else 0
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=homes[0]["name"] if homes else "Intex Pool",
                    data={**user_input, CONF_DEVICE_ID: device_id, CONF_GID: gid,
                          "sid": api.sid, "ecode": api.ecode})
        return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return IntexPoolOptionsFlow(entry)


class IntexPoolOptionsFlow(OptionsFlow):
    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current):
                vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
