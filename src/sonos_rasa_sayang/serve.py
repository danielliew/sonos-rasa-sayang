"""Temporary HTTP file server — Sonos pulls the WAV from this Mac.

Sonos is the HTTP *client*; we are the *server*. Typical behaviour:

* it may open two connections (probe, then play)
* it may abort one early → ``BrokenPipeError`` is normal
* it likes ``Accept-Ranges: bytes``
"""

from __future__ import annotations

import os
import subprocess
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wav": "audio/wav",
    }

    def log_message(self, fmt: str, *args) -> None:
        return

    def end_headers(self) -> None:
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Connection", "close")
        super().end_headers()

    def copyfile(self, source, outputfile) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            pass


class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True


def free_port(port: int) -> None:
    """Kill a leftover listener from a previous run."""
    try:
        out = subprocess.check_output(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    for pid in out.split():
        try:
            os.kill(int(pid), 15)
        except OSError:
            pass
    time.sleep(0.25)


def start_file_server(
    directory: Path, preferred_port: int | None = None
) -> tuple[ReusableServer, int]:
    """Serve ``directory`` on ``preferred_port``, or any free port if busy."""
    from sonos_rasa_sayang import config

    if preferred_port is None:
        preferred_port = config.SONOS_HTTP_PORT
    free_port(preferred_port)
    dir_str = str(directory)

    class Handler(QuietHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=dir_str, **kwargs)

    try:
        httpd = ReusableServer(("0.0.0.0", preferred_port), Handler)
    except OSError:
        httpd = ReusableServer(("0.0.0.0", 0), Handler)

    return httpd, httpd.server_address[1]
