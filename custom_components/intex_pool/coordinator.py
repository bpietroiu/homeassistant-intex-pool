"""DataUpdateCoordinator for Intex Pool."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IntexApi, IntexApiError, IntexAuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class IntexPoolCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, api: IntexApi, gid: int,
                 interval_min: int, creds: tuple[str, str, str]) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=timedelta(minutes=interval_min))
        self.api = api
        self.gid = gid
        self._creds = creds

    async def _ensure_login(self) -> None:
        if not self.api.sid:
            email, password, country = self._creds
            await self.api.login(email, password, country)

    async def _async_update_data(self) -> dict:
        try:
            await self._ensure_login()
            devices = await self.api.get_devices(self.gid)
        except IntexAuthError as err:
            # session may have expired: drop it and retry once
            self.api.sid = ""
            try:
                await self._ensure_login()
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
