# sonos-rasa-sayang

A small **Rasa Sayang** probe/player for Sonos: synthesize the melody in pure
Python and play it on a speaker over the LAN via UPnP.

Works with any Sonos zone player that exposes UPnP on port `1400` (Arc, Beam,
One, Five, …). Point it at your speaker with env vars — nothing device-specific
is hard-coded.

## How it works

1. **Discover** — resolve `SONOS_HOST` (mDNS) or use `SONOS_IP`.
2. **Synthesize** — turn the Rasa Sayang score into a 16-bit mono WAV.
3. **Serve** — temporary HTTP server on this machine hosts the WAV.
4. **Play** — UPnP/SOAP on `:1400` → `SetAVTransportURI` + `Play`;
   Sonos pulls the file and plays it.

Deeper walkthrough (state diagrams, protocol ownership, Spotify takeover,
links): **[docs/README.md](docs/README.md)**.

## Setup

```bash
cd sonos-rasa-sayang
uv sync
cp .env.example .env   # then edit SONOS_HOST or SONOS_IP
```

Find your speaker’s hostname:

```bash
dns-sd -B _sonos._tcp local.
# → host is often Sonos-<MAC>.local
```

Or set the IP from your router / Sonos app. A local `.env` is loaded
automatically if present (gitignored); process env always wins.

## Play

```bash
export SONOS_HOST=Sonos-AABBCCDDEEFF.local   # or SONOS_IP=…
uv run beep

uv run beep --vol 40
uv run beep --ip 192.168.1.50
uv run sonos-rasa-sayang --host Sonos-AABBCCDDEEFF.local
```

## Environment

| Variable | Required | Default | Meaning |
|----------|----------|---------|---------|
| `SONOS_HOST` | one of host/ip | — | mDNS name, e.g. `Sonos-….local` |
| `SONOS_IP` | one of host/ip | — | IPv4 (wins over host) |
| `SONOS_VOL` | no | `45` | Master volume 0–100 |
| `SONOS_HTTP_PORT` | no | `8765` | Preferred port for the WAV server |
| `SONOS_BIND_IP` | no | auto | IP Sonos should use to reach you |
| `SONOS_QUARTER_SEC` | no | `0.50` | Tempo (seconds per quarter note) |

## Layout

| Module | Role |
|--------|------|
| `config.py` | Env → settings |
| `discover.py` | Host/IP → Sonos address; local bind IP |
| `upnp.py` | SOAP volume / play URI |
| `melody.py` | Rasa Sayang WAV synthesis |
| `serve.py` | Temporary HTTP file server |
| `beep.py` | Orchestration |
| `cli.py` | CLI |
