"""Synthesize Rasa Sayang as a 16-bit mono WAV (no sample file on disk).

Score (key of C, 4/4)::

    8 = eighth, 4 = quarter, 2 = minim
    upbeat: 8,E4; 8,F4;
    bar 1:  4,G4; 4,G4; 4,c5; 8,B4; 8,A4
    bar 2:  8,G4; 8,G4; 8,E4; 8,F4; 4,G4; 4,B4
    bar 3:  8,A4; 8,A4; 8,G4; 8,F4; 8,E4; 8,G4; 8,C4; 8,E4;
    bar 4:  8,D4; 8,F4; 8,B3; 8,D4; 2,C4;
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

PITCH_TO_MIDI = {
    "B3": 59,
    "C4": 60,
    "D4": 62,
    "E4": 64,
    "F4": 65,
    "G4": 67,
    "A4": 69,
    "B4": 71,
    "C5": 72,
    "c5": 72,
}

# duration code → beats (one quarter note = 1 beat)
DUR_BEATS = {"8": 0.5, "4": 1.0, "2": 2.0}

RASA_SAYANG: list[tuple[str, str]] = [
    # upbeat
    ("8", "E4"),
    ("8", "F4"),
    # bar 1
    ("4", "G4"),
    ("4", "G4"),
    ("4", "c5"),
    ("8", "B4"),
    ("8", "A4"),
    # bar 2
    ("8", "G4"),
    ("8", "G4"),
    ("8", "E4"),
    ("8", "F4"),
    ("4", "G4"),
    ("4", "B4"),
    # bar 3
    ("8", "A4"),
    ("8", "A4"),
    ("8", "G4"),
    ("8", "F4"),
    ("8", "E4"),
    ("8", "G4"),
    ("8", "C4"),
    ("8", "E4"),
    # bar 4
    ("8", "D4"),
    ("8", "F4"),
    ("8", "B3"),
    ("8", "D4"),
    ("2", "C4"),
]


def midi_to_hz(midi: int) -> float:
    """Equal temperament: A4 (MIDI 69) = 440 Hz."""
    return 440.0 * (2 ** ((midi - 69) / 12.0))


def synthesize_rasa_sayang(
    out_path: Path,
    *,
    sample_rate: int = 44100,
    quarter_sec: float = 0.50,
    amplitude: float = 0.75,
) -> float:
    """Write a WAV file; return duration in seconds."""
    samples: list[int] = []
    total_beats = 0.0

    for dur_code, pitch in RASA_SAYANG:
        beats = DUR_BEATS[dur_code]
        total_beats += beats
        freq = midi_to_hz(PITCH_TO_MIDI[pitch])
        n = int(sample_rate * beats * quarter_sec)

        # Tiny trailing silence so notes don't smear together.
        gap = min(int(sample_rate * 0.02), max(0, n // 10))
        voiced = max(1, n - gap)

        for i in range(voiced):
            # Attack / release avoids clicks at note boundaries.
            env = min(1.0, i / 450.0, (voiced - i) / 700.0)
            t = i / sample_rate
            # Fundamental + light harmonics → less sterile than a pure sine.
            wave_s = (
                0.70 * math.sin(2 * math.pi * freq * t)
                + 0.20 * math.sin(4 * math.pi * freq * t)
                + 0.08 * math.sin(6 * math.pi * freq * t)
            )
            samples.append(int(amplitude * env * 32767 * wave_s))

        samples.extend([0] * (n - voiced))

    with wave.open(str(out_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(struct.pack("<h", s) for s in samples))

    return total_beats * quarter_sec
