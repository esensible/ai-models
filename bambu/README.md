# Bambu P1S — LAN status tool

Read live status from a Bambu Lab **P1S** over its local MQTT broker.
LAN-only, no cloud.

## Use it
```bash
./bambu/run.sh            # one-shot snapshot (temps, state, progress)
./bambu/run.sh --watch    # live-updating feed (Ctrl-C to stop)
./bambu/run.sh --raw      # dump full JSON the printer emits
```
No arguments needed — `run.sh` auto-loads creds from `printer.env` and sets up `uv`.

## How it works
- Printer: `$BAMBU_HOST` (set in `printer.env`), MQTT over TLS on port `8883`, self-signed cert.
- Auth: username `bblp`, password = 8-digit LAN access code.
- Subscribe `device/<serial>/report`; publish `{"pushing":{"sequence_id":"0","command":"pushall"}}`
  to `device/<serial>/request` to trigger a full status push.
- `bambu_status.py` uses `uv` + `paho-mqtt` (PEP 723 inline deps).

## Files
- `bambu_status.py` — the client.
- `run.sh` — wrapper: loads `printer.env`, sets writable uv cache/PATH (this box's $HOME is read-only).
- `printer.env` — host / access code / serial. **Gitignored** (holds a live access code). If missing,
  read the access code + serial off the printer (Settings → WLAN / Device) and recreate it:
  ```
  BAMBU_HOST=<printer-lan-ip>
  BAMBU_CODE=<8-digit access code>
  BAMBU_SERIAL=<serial>
  ```

## Gotchas
- Bambu's broker rejects the bare `#` wildcard (disconnect loop) and won't push to `device/#`
  passively — you must know the exact serial.
- We run in a container, not on the LAN: reachable via NAT for single TCP connections, but a
  full-subnet parallel scan exhausts NAT/conntrack and kills LAN access for a while. Don't mass-scan.
