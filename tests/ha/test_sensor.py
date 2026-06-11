from custom_components.intex_pool.sensor import SENSORS, IntexSensor


class _Coord:
    data = {"devId": "d1", "name": "WA510", "dataPointInfo": {"dps": {"108": 790, "118": 810, "111": 25}}}


def test_ph_sensor_value():
    desc = next(s for s in SENSORS if s.key == "ph")
    ent = IntexSensor(_Coord(), desc, "d1", "WA510")
    assert ent.native_value == 7.9
    assert ent.unique_id == "d1_ph"


def test_missing_dp_is_none():
    desc = next(s for s in SENSORS if s.key == "battery_pct")
    ent = IntexSensor(_Coord(), desc, "d1", "WA510")
    assert ent.native_value is None
