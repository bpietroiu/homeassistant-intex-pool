"""Self-contained crypto tests (no network, no captured traffic)."""
from custom_components.intex_pool import api


def test_encrypt_decrypt_roundtrip():
    key = api._enc_key("a-request-id", None)
    blob = api._encrypt('{"devId":"x","gid":1}', key)
    assert api._decrypt(blob, key) == '{"devId":"x","gid":1}'


def test_session_key_differs_from_non_session():
    assert api._enc_key("rid", None) != api._enc_key("rid", "ecode123")


def test_enc_key_is_16_ascii_hex():
    k = api._enc_key("rid", None)
    assert len(k) == 16 and all(c in b"0123456789abcdef" for c in k)


def test_sign_is_deterministic_and_includes_whitelist_only():
    params = {"a": "x", "v": "1.0", "time": "1", "clientId": api.APP_KEY, "ignored": "zzz"}
    s1 = api._sign(dict(params))
    s2 = api._sign(dict(params))
    assert s1 == s2 and len(s1) == 64
    # an out-of-whitelist field must not change the signature
    assert api._sign(dict(params, ignored="different")) == s1


def test_decode_reading_scales():
    out = api.decode_reading({"108": 790, "118": 810, "102": 400, "111": 25, "122": 98})
    assert out == {"ph": 7.9, "orp_mv": 810, "free_chlorine_ppm": 4.0,
                   "temp_c": 25, "battery_pct": 98}
