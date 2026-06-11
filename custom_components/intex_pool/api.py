"""Async, dependency-free client for the Intex Link (Tuya) mobile API."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid

import aiohttp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .const import APP_KEY, BASE_URL, CH_KEY, DP_MAP, SECRET, TTID

SIGN_KEYS = {"a", "v", "lat", "lon", "lang", "deviceId", "appVersion", "ttid", "h5",
             "h5Token", "os", "clientId", "postData", "time", "requestId", "et",
             "n4h5", "sid", "chKey", "sp"}


class IntexApiError(Exception):
    """Transport or server error."""


class IntexAuthError(IntexApiError):
    """Invalid credentials or dead session."""


def _swap(md5hex: str) -> str:
    return md5hex[8:16] + md5hex[0:8] + md5hex[24:32] + md5hex[16:24]


def _sign(params: dict) -> str:
    parts = []
    for k in sorted(params):
        if k in SIGN_KEYS and params.get(k):
            v = params[k]
            if k == "postData":
                v = _swap(hashlib.md5(v.encode()).hexdigest())
            parts.append(f"{k}={v}")
    return hmac.new(SECRET.encode(), "||".join(parts).encode(), hashlib.sha256).hexdigest()


def _enc_key(request_id: str, ecode: str | None) -> bytes:
    msg = SECRET + ("_" + ecode if ecode else "")
    return hmac.new(request_id.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16].encode()


def _encrypt(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, plaintext.encode(), None)  # ct||tag
    return base64.b64encode(nonce + ct).decode()


def _decrypt(b64: str, key: bytes) -> str:
    blob = base64.b64decode(b64)
    return AESGCM(key).decrypt(blob[:12], blob[12:], None).decode()


def generate_device_id() -> str:
    return (uuid.uuid4().hex + uuid.uuid4().hex)[:44]


def decode_reading(dps: dict) -> dict:
    out: dict[str, float] = {}
    for name, (dp, scale) in DP_MAP.items():
        if dp in dps and isinstance(dps[dp], (int, float)):
            out[name] = round(dps[dp] * scale, 2) if scale != 1 else dps[dp]
    return out


class IntexApi:
    def __init__(self, session: aiohttp.ClientSession, device_id: str,
                 sid: str = "", ecode: str = ""):
        self._session = session
        self.device_id = device_id
        self.sid = sid
        self.ecode = ecode

    async def call(self, action: str, version: str, post: dict | None = None) -> dict:
        import time
        rid = str(uuid.uuid4())
        params = {
            "a": action, "v": version, "appVersion": "1.1.11", "os": "Android",
            "lang": "en_US", "clientId": APP_KEY, "ttid": TTID, "deviceId": self.device_id,
            "chKey": CH_KEY, "et": "3", "time": str(int(time.time())), "requestId": rid,
        }
        if self.sid:
            params["sid"] = self.sid
        if post is not None:
            key = _enc_key(rid, self.ecode if self.sid else None)
            params["postData"] = _encrypt(json.dumps(post, separators=(",", ":")), key)
        params["sign"] = _sign(params)
        try:
            async with self._session.post(f"{BASE_URL}/api.json", data=params) as resp:
                body = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise IntexApiError(str(err)) from err
        if isinstance(body.get("result"), str):
            key = _enc_key(rid, self.ecode if self.sid else None)
            body["result"] = json.loads(_decrypt(body["result"], key))
        return body

    @staticmethod
    def _unwrap(body: dict) -> dict:
        res = body.get("result")
        if isinstance(res, dict):
            if res.get("success") is False:
                raise IntexAuthError(res.get("errorMsg") or res.get("errorCode") or "error")
            return res.get("result", res)
        return res

    async def login(self, email: str, password: str | None = None, country_code: str = "40",
                    password_md5: str | None = None) -> dict:
        """Two-step RSA login: fetch token+pubkey, RSA-encrypt MD5(password), then sign in."""
        from cryptography.hazmat.primitives.asymmetric import padding, rsa

        passwd_md5 = (password_md5 or hashlib.md5(password.encode()).hexdigest()).lower()
        tk = self._unwrap(await self.call(
            "smartlife.m.user.username.token.get", "2.0",
            post={"countryCode": country_code, "isUid": False, "username": email}))
        pub = rsa.RSAPublicNumbers(int(tk["exponent"]), int(tk["publicKey"])).public_key()
        passwd = pub.encrypt(passwd_md5.encode(), padding.PKCS1v15()).hex()
        res = self._unwrap(await self.call(
            "smartlife.m.user.email.password.login", "3.0",
            post={"countryCode": country_code, "email": email, "ifencrypt": 1,
                  "options": '{"group": 1,"mfaCode": ""}', "passwd": passwd, "token": tk["token"]}))
        self.sid = res["sid"]
        self.ecode = res["ecode"]
        return res

    async def homes(self) -> list[dict]:
        body = await self.call("tuya.m.location.list", "1.0")
        res = body.get("result")
        rows = res.get("result", res) if isinstance(res, dict) else (res or [])
        return [{"gid": h["groupId"], "name": h.get("name", "")} for h in rows]

    async def get_devices(self, gid: int) -> list[dict]:
        body = await self.call("m.life.my.group.device.list", "2.2", post={"gid": gid})
        res = body.get("result")
        return res.get("result", res) if isinstance(res, dict) else (res or [])
