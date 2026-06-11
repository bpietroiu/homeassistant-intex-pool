from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.intex_pool.const import DOMAIN


async def _start(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER})


async def test_user_happy_path(hass: HomeAssistant):
    result = await _start(hass)
    assert result["type"] == FlowResultType.FORM
    with patch("custom_components.intex_pool.config_flow.IntexApi") as api_cls:
        api = api_cls.return_value
        api.sid = "S"
        api.ecode = "E"
        api.login = AsyncMock(return_value={"sid": "S", "ecode": "E"})
        api.homes = AsyncMock(return_value=[{"gid": 123, "name": "My Home"}])
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"email": "a@b.c", "password": "pw", "country_code": "40"})
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["gid"] == 123
    assert result["data"]["device_id"]
    assert result["data"]["sid"] == "S"


async def test_user_invalid_auth(hass: HomeAssistant):
    from custom_components.intex_pool.api import IntexAuthError
    result = await _start(hass)
    with patch("custom_components.intex_pool.config_flow.IntexApi") as api_cls:
        api_cls.return_value.login = AsyncMock(side_effect=IntexAuthError("bad"))
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"email": "a@b.c", "password": "x", "country_code": "40"})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"
