const RANGES = {
  ph:                {min: 7.2, max: 7.6, lo: 6.8, hi: 8.0, label: "pH",            unit: ""},
  orp_mv:            {min: 650, max: 750, lo: 550, hi: 850, label: "ORP",           unit: "mV"},
  free_chlorine_ppm: {min: 1,   max: 3,   lo: 0,   hi: 5,   label: "Free chlorine", unit: "ppm"},
  temp_c:            {min: 0,   max: 40,  lo: 0,   hi: 40,  label: "Temp",          unit: "°C"},
  battery_pct:       {min: 20,  max: 100, lo: 0,   hi: 100, label: "Battery",       unit: "%"},
};
// Default entity-id suffixes (from the sensor names) + the canonical order.
const SUFFIX = {ph: "ph", orp_mv: "orp", free_chlorine_ppm: "free_chlorine",
                temp_c: "temperature", battery_pct: "battery"};
const KEYS = Object.keys(RANGES);

class IntexPoolCard extends HTMLElement {
  setConfig(config) {
    if (!config.entities) throw new Error("intex-pool-card: 'entities' (5 sensor ids) required");
    this._config = config;
  }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 4; }

  _byKey(key) {
    const ents = this._config.entities || [];
    const suf = "_" + SUFFIX[key];
    return ents.find((e) => e.endsWith(suf)) || ents[KEYS.indexOf(key)];
  }
  _state(key) {
    const id = this._byKey(key);
    const st = id && this._hass && this._hass.states[id];
    if (!st || st.state === "unavailable" || st.state === "unknown") return null;
    const n = parseFloat(st.state);
    return Number.isNaN(n) ? null : n;
  }
  _status(key, v) {
    if (v === null || Number.isNaN(v)) return "na";
    const r = RANGES[key];
    if (v < r.lo || v > r.hi) return "bad";
    if (v < r.min || v > r.max) return "warn";
    return "ok";
  }
  _color(status) {
    return {bad: "var(--error-color)", warn: "var(--warning-color)",
            ok: "var(--success-color, #2e7d32)", na: "var(--disabled-text-color)"}[status];
  }
  _verdict() {
    const bad = ["ph", "free_chlorine_ppm"].some((k) => {
      const v = this._state(k); const r = RANGES[k];
      return v !== null && (v < r.min || v > r.max);
    });
    return bad ? {text: "Check water", color: "var(--warning-color)"}
               : {text: "Water OK", color: "var(--success-color, #2e7d32)"};
  }
  _render() {
    if (!this._hass) return;
    const v = this._verdict();
    const gauges = Object.keys(RANGES).map((k) => {
      const val = this._state(k);
      const r = RANGES[k];
      const st = this._status(k, val);
      const txt = val === null ? "—" : val;
      const flag = (st === "warn" || st === "bad") ? ' <span class="warn-ico">⚠</span>' : "";
      return `<div class="cell cell--${st}" style="--c:${this._color(st)}">
          <div class="val">${txt}<span class="u">${r.unit}</span></div>
          <div class="lbl">${r.label}${flag}</div>
        </div>`;
    }).join("");
    const anyId = this._byKey("ph");
    const updated = anyId && this._hass.states[anyId]
      ? new Date(this._hass.states[anyId].last_updated).toLocaleString() : "";
    const icon = this._config.icon || "/intex_pool/icon.png";
    this.innerHTML = `
      <ha-card>
        <div class="hdr">
          <img class="ico" src="${icon}" alt="" onerror="this.style.display='none'">
          <span class="ttl">${this._config.title || "Pool"}</span>
        </div>
        <div class="banner" style="background:${v.color}">${v.text}</div>
        <div class="grid">${gauges}</div>
        <div class="foot">Updated ${updated}</div>
      </ha-card>
      <style>
        .hdr{display:flex;align-items:center;gap:10px;padding:12px 16px 4px}
        .ico{width:34px;height:34px;border-radius:8px}
        .ttl{font-size:1.3em;font-weight:500}
        .banner{color:#fff;padding:6px 16px;font-weight:600}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(96px,1fr));gap:10px;padding:12px 16px}
        .cell{text-align:center;padding:8px 6px;border-radius:10px;border:1px solid transparent;transition:background .2s}
        .cell--warn,.cell--bad{border-color:var(--c);background:rgba(255,255,255,.04)}
        @supports (background:color-mix(in srgb,red 10%,transparent)){
          .cell--warn,.cell--bad{background:color-mix(in srgb,var(--c) 15%,transparent);border-color:color-mix(in srgb,var(--c) 50%,transparent)}
        }
        .val{font-size:1.6em;font-weight:600;color:var(--c)}
        .warn-ico{font-size:.8em}
        .u{font-size:.5em;margin-left:2px;color:var(--secondary-text-color)}
        .lbl{font-size:.8em;color:var(--secondary-text-color)}
        .foot{padding:4px 16px 12px;font-size:.75em;color:var(--secondary-text-color)}
      </style>`;
  }
}
customElements.define("intex-pool-card", IntexPoolCard);
window.customCards = window.customCards || [];
window.customCards.push({type: "intex-pool-card", name: "Intex Pool Card",
  description: "pH / ORP / chlorine / temp / battery for an Intex WA510"});
