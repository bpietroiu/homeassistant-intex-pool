const RANGES = {
  ph:                {min: 7.2, max: 7.6, lo: 6.8, hi: 8.0, label: "pH",            unit: ""},
  orp_mv:            {min: 650, max: 750, lo: 550, hi: 850, label: "ORP",           unit: "mV"},
  free_chlorine_ppm: {min: 1,   max: 3,   lo: 0,   hi: 5,   label: "Free chlorine", unit: "ppm"},
  temp_c:            {min: 0,   max: 40,  lo: 0,   hi: 40,  label: "Temp",          unit: "°C"},
  battery_pct:       {min: 20,  max: 100, lo: 0,   hi: 100, label: "Battery",       unit: "%"},
};

class IntexPoolCard extends HTMLElement {
  setConfig(config) {
    if (!config.entities) throw new Error("intex-pool-card: 'entities' (5 sensor ids) required");
    this._config = config;
  }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 4; }

  _byKey(key) {
    return (this._config.entities || []).find((e) => e.endsWith("_" + key) || e.includes(key));
  }
  _state(key) {
    const id = this._byKey(key);
    const st = id && this._hass && this._hass.states[id];
    return st ? parseFloat(st.state) : null;
  }
  _color(key, v) {
    if (v === null || Number.isNaN(v)) return "var(--disabled-text-color)";
    const r = RANGES[key];
    if (v < r.lo || v > r.hi) return "var(--error-color)";
    if (v < r.min || v > r.max) return "var(--warning-color)";
    return "var(--success-color, #2e7d32)";
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
      const txt = val === null ? "—" : val;
      return `<div class="cell">
          <div class="val" style="color:${this._color(k, val)}">${txt}<span class="u">${r.unit}</span></div>
          <div class="lbl">${r.label}</div>
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
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px;padding:12px 16px}
        .cell{text-align:center}
        .val{font-size:1.6em;font-weight:600}
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
