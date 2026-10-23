"""Scene base class and alpha-composite helpers."""

import math

from renderer import Canvas, shade, mix, h01, P, sw

# cue times harvested from the lyric timeline so scenes stay in sync
from lyrics import LINES

CUES = {}
for _t0, _t1, _en, _zh in LINES:
    CUES.setdefault(_en, []).append(_t0)


def cue(en, i=0):
    try:
        return CUES[en][i]
    except (KeyError, IndexError):
        return 0.0


# The lyric timeline is the song clock; a few scenes are designed on a
# slightly different clock (see Scene.cue_off), so they call Scene.cue().


class Ctx:
    __slots__ = ("t", "beat", "bar", "energy", "section", "w", "h", "frameno")

    def __init__(self, t, beat, bar, energy, section, w, h, frameno=0):
        self.t = t
        self.beat = beat
        self.bar = bar
        self.energy = energy
        self.section = section
        self.w = w
        self.h = h
        self.frameno = frameno

    def e_at(self, t):
        try:
            return self.energy(t)
        except Exception:
            return 0.5


class Scene:
    key = ""
    accent = "phos"
    chapter_en = ""
    chapter_zh = ""

    def __init__(self, t0, t1):
        self.t0 = float(t0)
        self.t1 = float(t1)
        self.dur = self.t1 - self.t0
        # offset applied by Scene.cue(): lyric time -> this scene's clock
        self.cue_off = 0.0

    def local(self, t):
        v = t - self.t0
        if v < 0:
            return 0.0
        if v > self.dur:
            return self.dur
        return v

    def cue(self, en, i=0):
        """Lyric cue time expressed in this scene's own clock."""
        return cue(en, i) + self.cue_off

    def draw(self, cv, ctx):
        raise NotImplementedError


# --------------------------------------------------------------------------
# alpha helpers
# --------------------------------------------------------------------------

def stamp(cv, draw_fn, alpha, seed=0, clip=None):
    """Draw draw_fn into a scratch canvas, then composite with alpha."""
    if alpha <= 0.01:
        return
    tmp = Canvas(cv.w, cv.h)
    draw_fn(tmp)
    cv.composite(tmp, alpha=min(1.0, alpha), seed=seed, clip=clip)


def fade_window(t, t_in, t_out, fin=0.55, fout=0.55):
    """1 inside [t_in+fin, t_out-fout], ramp at edges."""
    if t < t_in or t > t_out:
        return 0.0
    a = 1.0
    if fin > 0 and t < t_in + fin:
        a = min(a, (t - t_in) / fin)
    if fout > 0 and t > t_out - fout:
        a = min(a, (t_out - t) / fout)
    return max(0.0, min(1.0, a))


def ramp(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return max(0.0, min(1.0, (t - t0) / (t1 - t0)))


def glow_text(cv, x, y, s, fg, accent=None, bg=None):
    shadow = shade(accent or fg, 0.35)
    cv.text(x + 1, y, s, shadow, bg)
    cv.text(x, y, s, fg, bg)
