# Home Assistant brand assets for `intex_pool`

These give the integration its icon in the HA **Settings UI**. The Settings-UI icon
can only come from the official https://github.com/home-assistant/brands repo, so:

1. Fork `home-assistant/brands`.
2. Copy `custom_integrations/intex_pool/` (this folder's `icon.png`, `icon@2x.png`,
   `logo.png`, `logo@2x.png`) into the same path in your fork.
3. Open a PR. Once merged, HA shows the icon for the `intex_pool` domain.

Until then, the integration still works; the **custom Lovelace card** already shows the
icon (served at `/intex_pool/icon.png`), and HACS shows the repo `icon.png`.
