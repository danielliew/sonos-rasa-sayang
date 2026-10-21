"""Runtime config from environment (safe for a public repo — no personal defaults).

Required (one of):
  SONOS_HOST   mDNS name, e.g. Sonos-AABBCCDDEEFF.local
  SONOS_IP     dotted IPv4, e.g. 192.168.1.50  (wins over HOST if both set)

Optional:
  SONOS_VOL         master volume 0–100          (default: 45)
  SONOS_HTTP_PORT   preferred WAV serve port     (default: 8765)
  SONOS_BIND_IP     IP Sonos should use to reach this machine
                    (default: auto-detect via outbound route)
  SONOS_QUARTER_SEC seconds per quarter note     (default: 0.50)

A gitignored ``.env`` in the project (or cwd) is loaded if present; real
process env always wins. See ``.env.example``.
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal KEY=VALUE loader. Does not override existing os.environ."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",  # project root
    ]
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value
        break


_load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if raw is None:
        return default
    return float(raw)


# SONOS_IP wins over SONOS_HOST when both are set.
SONOS_IP = _env("SONOS_IP")
SONOS_HOST = _env("SONOS_HOST")

SONOS_VOL = _env_int("SONOS_VOL", 45)
SONOS_HTTP_PORT = _env_int("SONOS_HTTP_PORT", 8765)
SONOS_BIND_IP = _env("SONOS_BIND_IP")  # None → auto-detect
SONOS_QUARTER_SEC = _env_float("SONOS_QUARTER_SEC", 0.50)

UPNP_PORT = 1400  # fixed by Sonos firmware; not sensitive


def require_sonos_target() -> None:
    """Exit with a helpful message if no speaker target is configured."""
    if not SONOS_HOST and not SONOS_IP:
        raise SystemExit(
            "No Sonos target configured.\n"
            "Set one of:\n"
            "  export SONOS_HOST=Sonos-AABBCCDDEEFF.local\n"
            "  export SONOS_IP=192.168.1.50\n"
            "\n"
            "Or copy .env.example → .env and edit it.\n"
            "Find the hostname via:\n"
            "  dns-sd -B _sonos._tcp local."
        )
