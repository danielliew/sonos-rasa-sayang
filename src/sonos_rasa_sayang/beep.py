"""Orchestrate: synthesize → serve → tell Sonos to play."""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path

from sonos_rasa_sayang import config
from sonos_rasa_sayang.discover import local_ipv4, resolve_sonos_ip
from sonos_rasa_sayang.melody import synthesize_rasa_sayang
from sonos_rasa_sayang.serve import start_file_server
from sonos_rasa_sayang.upnp import play_uri, set_volume


def beep(
    volume: int | None = None,
    host: str | None = None,
    ip: str | None = None,
) -> None:
    """Synthesize Rasa Sayang and play it on a Sonos speaker via UPnP."""
    if not (host or ip or config.SONOS_HOST or config.SONOS_IP):
        config.require_sonos_target()

    volume = config.SONOS_VOL if volume is None else volume
    label = ip or host or config.SONOS_IP or config.SONOS_HOST
    print(f"Resolving {label} …")
    sonos_ip = resolve_sonos_ip(host=host, ip=ip)
    print(f"Sonos at {sonos_ip}:{config.UPNP_PORT}")

    bind_ip = local_ipv4()
    print(f"This machine (file server) at {bind_ip}")

    with tempfile.TemporaryDirectory(prefix="sonos-rasa-sayang-") as tmp:
        tmp_path = Path(tmp)
        wav_path = tmp_path / "rasa-sayang.wav"

        print("Synthesizing Rasa Sayang …")
        duration = synthesize_rasa_sayang(
            wav_path, quarter_sec=config.SONOS_QUARTER_SEC
        )
        print(f"  → {wav_path.name} ({duration:.1f}s)")

        httpd, port = start_file_server(tmp_path, preferred_port=config.SONOS_HTTP_PORT)
        uri = f"http://{bind_ip}:{port}/{wav_path.name}"
        print(f"Serving {uri}")

        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            print(f"Setting volume={volume}, unmuting …")
            set_volume(sonos_ip, volume)

            print("SetAVTransportURI + Play …")
            play_uri(sonos_ip, uri)

            wait = duration + 2.0
            print(f"Waiting {wait:.0f}s for playback to finish …")
            time.sleep(wait)
            print("Done.")
        finally:
            httpd.shutdown()
