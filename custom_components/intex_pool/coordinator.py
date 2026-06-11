"""DataUpdateCoordinator for Intex Pool."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IntexApi, IntexApiError, IntexAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IntexPoolCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: IntexApi, gid: int,
                 interval_min: int, creds: tuple[str, str, str]) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=timedelta(minutes=interval_min))
        self.entry = entry
        self.api = api
        self.gid = gid
        self._creds = creds

    async def _login_and_persist(self) -> None:
        """Log in and save the new session on the entry so restarts don't re-login
        (Tuya rate-limits the login endpoint)."""
        email, password, country = self._creds
        await self.api.login(email, password, country)
        self.hass.config_entries.async_update_entry(
            self.entry, data={**self.entry.data, "sid": self.api.sid, "ecode": self.api.ecode})

    async def _async_update_data(self) -> dict:
        try:
            if not self.api.sid:
                await self._login_and_persist()
            devices = await self.api.get_devices(self.gid)
        except IntexAuthError:
            # session expired -> re-login once
            self.api.sid = ""
            try:
                await self._login_and_persist()
                devices = await self.api.get_devices(self.gid)
            except IntexAuthError as err2:
                raise ConfigEntryAuthFailed(str(err2)) from err2
            except IntexApiError as err2:
                raise UpdateFailed(str(err2)) from err2
        except IntexApiError as err:
            raise UpdateFailed(str(err)) from err
        if not devices:
            raise UpdateFailed("no devices returned")
        # WA510 is the device carrying dataPointInfo.dps
        for dev in devices:
            if (dev.get("dataPointInfo") or {}).get("dps"):
                return dev
        return devices[0]
