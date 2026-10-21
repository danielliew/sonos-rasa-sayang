"""CLI entry point."""

from __future__ import annotations

import argparse
import socket
import sys
import urllib.error

from sonos_rasa_sayang import config
from sonos_rasa_sayang.beep import beep


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sonos-rasa-sayang",
        description="Rasa Sayang probe/player for Sonos (synthesize + UPnP play).",
        epilog=(
            "Configure the target with SONOS_HOST or SONOS_IP "
            "(see .env.example). CLI flags override env."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--vol",
        type=int,
        default=None,
        help=f"Sonos master volume 0–100 (env SONOS_VOL, default {config.SONOS_VOL})",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Sonos mDNS hostname (env SONOS_HOST)",
    )
    parser.add_argument(
        "--ip",
        default=None,
        help="Sonos IPv4 address (env SONOS_IP; wins over --host)",
    )
    args = parser.parse_args(argv)

    try:
        beep(volume=args.vol, host=args.host, ip=args.ip)
    except socket.gaierror as e:
        print(f"Could not resolve Sonos host: {e}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Sonos HTTP/SOAP failed: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0
