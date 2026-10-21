"""Find the Sonos speaker on the LAN."""

from __future__ import annotations

import socket

from sonos_rasa_sayang import config


def resolve_sonos_ip(host: str | None = None, ip: str | None = None) -> str:
    """Resolve to IPv4.

    Priority: explicit ``ip`` arg → ``SONOS_IP`` → ``host`` arg → ``SONOS_HOST``.
    """
    if ip:
        return ip
    if config.SONOS_IP:
        return config.SONOS_IP

    target = host or config.SONOS_HOST
    if not target:
        config.require_sonos_target()  # raises SystemExit
        raise AssertionError("unreachable")

    if all(part.isdigit() for part in target.split(".")):
        return target

    # On macOS, getaddrinfo for *.local goes through mDNSResponder (Bonjour).
    infos = socket.getaddrinfo(
        target, config.UPNP_PORT, socket.AF_INET, socket.SOCK_STREAM
    )
    return infos[0][4][0]


def local_ipv4() -> str:
    """IPv4 Sonos should use to reach *this* machine.

    Override with ``SONOS_BIND_IP`` if auto-detect picks the wrong interface
    (VPN, multiple NICs, etc.).
    """
    if config.SONOS_BIND_IP:
        return config.SONOS_BIND_IP

    # UDP connect does not send packets; it only asks which source address
    # the OS would use for that route.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
