"""Sensor platform for Intex Pool."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorEntityDescription, SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import decode_reading
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class IntexSensorDescription(SensorEntityDescription):
    pass


SENSORS: tuple[IntexSensorDescription, ...] = (
    IntexSensorDescription(key="ph", name="pH", native_unit_of_measurement="pH",
                           state_class=SensorStateClass.MEASUREMENT, icon="mdi:ph"),
    IntexSensorDescription(key="orp_mv", name="ORP",
                           device_class=SensorDeviceClass.VOLTAGE,
                           native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
                           state_class=SensorStateClass.MEASUREMENT),
    IntexSensorDescription(key="free_chlorine_ppm", name="Free chlorine",
                           native_unit_of_measurement="ppm",
                           state_class=SensorStateClass.MEASUREMENT, icon="mdi:test-tube"),
    IntexSensorDescription(key="temp_c", name="Temperature",
                           device_class=SensorDeviceClass.TEMPERATURE,
                           native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                           state_class=SensorStateClass.MEASUREMENT),
    IntexSensorDescription(key="battery_pct", name="Battery",
                           device_class=SensorDeviceClass.BATTERY,
                           native_unit_of_measurement=PERCENTAGE,
                           state_class=SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    dev = coordinator.data
    dev_id = dev.get("devId", entry.entry_id)
    name = dev.get("name", "Intex WA510")
    async_add_entities(IntexSensor(coordinator, desc, dev_id, name) for desc in SENSORS)


class IntexSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: IntexSensorDescription,
                 dev_id: str, dev_name: str) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._dev_id = dev_id
        self._attr_unique_id = f"{dev_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dev_id)}, name=dev_name,
            manufacturer="Intex", model="WA510 Water Analyzer")

    @property
    def native_value(self):
        dps = (self.coordinator.data.get("dataPointInfo") or {}).get("dps") or {}
        return decode_reading(dps).get(self.entity_description.key)
