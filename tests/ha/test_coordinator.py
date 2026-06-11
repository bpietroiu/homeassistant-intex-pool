from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.intex_pool.api import IntexApiError, IntexAuthError
from custom_components.intex_pool.coordinator import IntexPoolCoordinator


def _make(hass, api):
    entry = MagicMock()
    entry.data = {}
    return IntexPoolCoordinator(hass, entry, api, gid=123, interval_min=15,
                                creds=("a@b.c", "pw", "40"))


async def test_existing_session_does_not_relogin(hass: HomeAssistant):
    api = AsyncMock()
    api.sid = "S"
    api.login = AsyncMock()
    api.get_devices = AsyncMock(return_value=[{"devId": "d1", "dataPointInfo": {"dps": {"108": 720}}}])
    coord = _make(hass, api)
    data = await coord._async_update_data()
    assert data["devId"] == "d1"
    api.login.assert_not_called()


async def test_relogin_then_fail_raises_auth(hass: HomeAssistant):
    api = AsyncMock()
    api.sid = ""
    api.login = AsyncMock(side_effect=IntexAuthError("bad"))
    coord = _make(hass, api)
    with pytest.raises(ConfigEntryAuthFailed):
        await coord._async_update_data()


async def test_rate_limit_at_login_raises_updatefailed(hass: HomeAssistant):
    api = AsyncMock()
    api.sid = ""
    api.login = AsyncMock(side_effect=IntexApiError("Requests are too frequent"))
    coord = _make(hass, api)
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_transport_error_raises_updatefailed(hass: HomeAssistant):
    api = AsyncMock()
    api.sid = "S"
    api.get_devices = AsyncMock(side_effect=IntexApiError("net"))
    coord = _make(hass, api)
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
