"""Constants for the Intex Pool integration."""
from __future__ import annotations

DOMAIN = "intex_pool"
DEFAULT_SCAN_INTERVAL = 15  # minutes; WA510 samples ~hourly
MIN_SCAN_INTERVAL = 5

# --- App-level constants (Intex Link APK; identical for every user) ---
PACKAGE = "com.intex.spa"
APP_KEY = "mtsv5smaw8gyhws3a5w7"
CH_KEY = "eefe5a0d"
_CERT = "63:D6:FF:87:5B:5D:20:A3:42:DD:15:A9:19:C1:5A:08:58:5A:16:A7:9A:52:7B:F5:ED:81:72:EB:5B:EC:F1:B4"
_SECRET1 = "kpuu8s8f43sfsrguehvsyqradgegecef"
_SECRET2 = "c49n45ude4scf3jasrnuc8dpsyd3tftm"
SECRET = f"{PACKAGE}_{_CERT}_{_SECRET1}_{_SECRET2}"
TTID = "sdk_international@" + APP_KEY
BASE_URL = "https://a1.tuyaeu.com"

# DP map: reading_key -> (dp_id, scale)
DP_MAP: dict[str, tuple[str, float]] = {
    "ph": ("108", 0.01),
    "orp_mv": ("118", 1),
    "free_chlorine_ppm": ("102", 0.01),
    "temp_c": ("111", 1),
    "battery_pct": ("122", 1),
}

CONF_COUNTRY = "country_code"
CONF_DEVICE_ID = "device_id"
CONF_GID = "gid"
CONF_SCAN_INTERVAL = "scan_interval"
