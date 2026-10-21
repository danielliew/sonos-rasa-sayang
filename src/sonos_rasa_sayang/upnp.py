"""Talk to Sonos over UPnP / SOAP on TCP :1400.

Control is plain HTTP POST with a SOAP XML body, e.g.::

    POST http://<sonos-ip>:1400/MediaRenderer/AVTransport/Control
    SOAPACTION: "urn:schemas-upnp-org:service:AVTransport:1#Play"

Services we use:

* ``RenderingControl`` — volume / mute (the amp knobs)
* ``AVTransport`` — what to play / play / pause (the transport deck)
"""

from __future__ import annotations

import urllib.request

from sonos_rasa_sayang import config


def soap(ip: str, path: str, service_action: str, inner_xml: str, timeout: float = 4.0) -> str:
    """Send one SOAP action. ``service_action`` looks like ``AVTransport:1#Play``."""
    service, action = service_action.split("#", 1)
    urn = f"urn:schemas-upnp-org:service:{service}"
    body = (
        '<?xml version="1.0"?>'
        '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
        's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
        f'<s:Body><u:{action} xmlns:u="{urn}">{inner_xml}</u:{action}></s:Body>'
        "</s:Envelope>"
    )
    req = urllib.request.Request(
        f"http://{ip}:{config.UPNP_PORT}{path}",
        data=body.encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": 'text/xml; charset="utf-8"',
            "SOAPACTION": f'"{urn}#{action}"',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def set_volume(ip: str, volume: int) -> None:
    """Set master volume (0–100) and unmute."""
    volume = max(0, min(100, volume))
    soap(
        ip,
        "/MediaRenderer/RenderingControl/Control",
        "RenderingControl:1#SetVolume",
        f"<InstanceID>0</InstanceID><Channel>Master</Channel>"
        f"<DesiredVolume>{volume}</DesiredVolume>",
    )
    soap(
        ip,
        "/MediaRenderer/RenderingControl/Control",
        "RenderingControl:1#SetMute",
        "<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredMute>0</DesiredMute>",
    )


def play_uri(ip: str, uri: str) -> None:
    """Point the transport at ``uri``, then Play.

    Sonos HTTP-GETs the URI from this machine's temporary file server.
    """
    safe = (
        uri.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    soap(
        ip,
        "/MediaRenderer/AVTransport/Control",
        "AVTransport:1#SetAVTransportURI",
        f"<InstanceID>0</InstanceID>"
        f"<CurrentURI>{safe}</CurrentURI>"
        f"<CurrentURIMetaData></CurrentURIMetaData>",
    )
    soap(
        ip,
        "/MediaRenderer/AVTransport/Control",
        "AVTransport:1#Play",
        "<InstanceID>0</InstanceID><Speed>1</Speed>",
    )
