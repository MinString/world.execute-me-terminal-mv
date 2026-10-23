"""Packed RMS energy envelope of the song: 20 frames/second, 0..255.

Generated from the audio; lets the visuals react to loudness without any
runtime dependency on numpy or ffmpeg.
"""

import base64
import zlib

_DATA = (
    "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"
)

_RAW = zlib.decompress(base64.b64decode(_DATA))
RATE = 20.0
ENERGY = list(_RAW)


def at(t):
    """Energy 0..1 at song time t (seconds)."""
    i = int(t * RATE)
    if i < 0:
        i = 0
    if i >= len(ENERGY):
        i = len(ENERGY) - 1
    return ENERGY[i] / 255.0
