# Bambu P1S — LAN status tool

Read live status from a Bambu Lab **P1S** over its local MQTT broker.
LAN-only, no cloud.

## Use it
```bash
./printer/run.sh            # one-shot snapshot (temps, state, progress)
./printer/run.sh --watch    # live-updating feed (Ctrl-C to stop)
./printer/run.sh --raw      # dump full JSON the printer emits
```
No arguments needed — `run.sh` auto-loads creds from `$BAMBU_ENV_FILE` (the `printer`
volume in-container, else a local `printer/printer.env`) and sets up `uv`.

## How it works
- Printer: `$BAMBU_HOST` (set in `printer.env`), MQTT over TLS on port `8883`, self-signed cert.
- Auth: username `bblp`, password = 8-digit LAN access code.
- Subscribe `device/<serial>/report`; publish `{"pushing":{"sequence_id":"0","command":"pushall"}}`
  to `device/<serial>/request` to trigger a full status push.
- `bambu_status.py` uses `uv` + `paho-mqtt` (PEP 723 inline deps).

## Files
- `bambu_status.py` — the client.
- `run.sh` — wrapper: loads creds from `$BAMBU_ENV_FILE` (fallback `printer/printer.env`), sets up `uv`.
- **Creds** — `BAMBU_HOST` / `BAMBU_CODE` / `BAMBU_SERIAL`, loaded from `$BAMBU_ENV_FILE`.
  In the dev container that points at the **`printer` named volume**
  (`/root/.config/ai-models/printer.env`) — creds live **only in the volume**, never in the repo
  or on the host, and survive restart/rebuild. Outside a container the wrappers fall back to a
  gitignored `printer/printer.env`. The file is just three lines (read off the printer,
  Settings → WLAN / Device):
  ```
  BAMBU_HOST=<printer-lan-ip>
  BAMBU_CODE=<8-digit access code>
  BAMBU_SERIAL=<serial>
  ```
  Seed/replace the volume copy with:
  `podman run --rm -i -v printer:/v ai-models-dev:latest -c 'cat > /v/printer.env'`
  then paste those three lines and Ctrl-D.

## Gotchas
- Bambu's broker rejects the bare `#` wildcard (disconnect loop) and won't push to `device/#`
  passively — you must know the exact serial.
- We run in a container, not on the LAN: reachable via NAT for single TCP connections, but a
  full-subnet parallel scan exhausts NAT/conntrack and kills LAN access for a while. Don't mass-scan.
