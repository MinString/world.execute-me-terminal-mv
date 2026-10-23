"""CRT signal path — the layer that makes the picture look *transmitted*.

Every scene is drawn as clean data; this module is the broadcast + tube chain
on top of it: phosphor stipple and dust in the empty space, a rolling beam,
grain, chroma bleed, vertical-hold slips, dropouts, tube corner mask and a
beat-synced bloom.  Everything is a pure function of `t` (seeded through
h01), so pausing or seeking never changes the frame.
"""

import math

from renderer import Canvas, P, h01, mix, shade

# 4x4 ordered dither, used for stipple and for half-tone bands
B4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
JUNK = "·.:'`\"~^*+x%&?!/\\|<>[]{}=-_"
DUST = "·˙'`"


def _b(x, y):
    return B4[y & 3][x & 3] / 16.0


# --------------------------------------------------------------------------
# phosphor stipple: the static half of the empty screen
# --------------------------------------------------------------------------

_TPL = {}


def stipple(w, h, ac):
    """Cached faint dot-grid / dust / dither wash that sits under every scene."""
    key = (w, h, ac)
    tpl = _TPL.get(key)
    if tpl is not None:
        return tpl
    tpl = Canvas(w, h)
    dim = mix(ac, P["black"], 0.86)
    dim2 = mix(ac, P["black"], 0.91)
    dim3 = mix(P["cyan"], P["black"], 0.88)
    for y in range(h):
        v = y / max(1, h - 1)
        for x in range(w):
            n = h01(x, y, 5)
            b = _b(x, y)
            ch = c = None
            if x % 10 == 0 and y % 5 == 0 and b < 0.7:
                ch, c = "·", dim
            elif n < 0.016 + 0.030 * (1.0 - v) and b < 0.62:
                ch, c = "·", dim2
            elif n > 0.994:
                ch = JUNK[int(h01(x, y, 7) * len(JUNK))]
                c = dim3
            if ch:
                tpl.put(x, y, ch, c)
    _TPL[key] = tpl
    return tpl


def streams(cv, t, ac):
    """Dim hex streams falling through the empty parts of the frame."""
    w, h = cv.w, cv.h
    n = max(5, w // 8)
    dim = mix(ac, P["black"], 0.80)
    dim2 = mix(ac, P["black"], 0.90)
    hexd = "0123456789ABCDEF"
    for i in range(n):
        x = int(h01(i, 41) * w)
        off = h01(i, 43) * h
        spd = 1.3 + 3.2 * h01(i, 45)
        ln = 2 + int(h01(i, 47) * 5)
        for j in range(ln):
            y = int((off + t * spd + j) % h)
            if 0 <= y < h and cv.ch[y][x] == " ":
                cv.put(x, y, hexd[int(h01(x, y, 49) * 16)], dim if j else dim2)


def ambient(cv, t, ac):
    """Lay the stipple down (drifting a cell sideways) + dust + data streams."""
    tpl = stipple(cv.w, cv.h, ac)
    cv.copy_from(tpl)
    cv.roll(int(round(math.sin(t * 0.5) * 1.2)), 0)
    n = max(4, cv.w // 22)
    for i in range(n):
        sp = 3.0 + 5.0 * h01(i, 21)
        x = int((h01(i, 5) * cv.w + t * sp) % cv.w)
        y = int((h01(i, 9) * cv.h + t * (0.5 + 1.1 * h01(i, 11))) % cv.h)
        cv.put(x, y, DUST[int(h01(i, 13) * 4)],
               mix(ac, P["white"], 0.2) if h01(i, 17) > 0.7 else mix(ac, P["black"], 0.6))
    streams(cv, t, ac)


# --------------------------------------------------------------------------
# tube artefacts
# --------------------------------------------------------------------------

def beam(cv, t, ac):
    """A slow bright bar rolling down the tube + a half-tone band behind it."""
    h = cv.h
    y = int((t * 9.0) % (h + 10)) - 5
    for dy, k in ((0, 0.13), (1, 0.10), (2, 0.055)):
        yy = y + dy
        if not (0 <= yy < h):
            continue
        row = cv.fg[yy]
        for x in range(cv.w):
            c = row[x]
            if c is not None and _b(x, yy) < 0.82:
                row[x] = mix(c, P["white"], k)
    # the retrace line runs the other way, much fainter
    y2 = int((h - (t * 5.5) % (h + 6)) + 3)
    if 0 <= y2 < h:
        row = cv.fg[y2]
        for x in range(cv.w):
            c = row[x]
            if c is not None:
                row[x] = mix(c, ac, 0.07)
    # interference ripple down the edges — the flyback's dirty secret
    for i in range(4):
        x = int(h01(i, int(t * 11), 31) * 3)
        if i % 2:
            x = cv.w - 1 - x
        yy = int((t * 21 + i * 7) % h)
        if 0 <= yy < h and cv.ch[yy][x] == " ":
            cv.put(x, yy, "▏" if i % 2 else "▎", mix(ac, P["black"], 0.62))


def grain(cv, t, ac, k=1.0):
    """Sparse snow in the empty cells."""
    step = int(t * 20)
    n = int(cv.w * cv.h * 0.012 * k)
    for i in range(n):
        x = int(h01(i, step, 61) * cv.w)
        y = int(h01(i, step, 62) * cv.h)
        if cv.ch[y][x] == " ":
            c = mix(ac, P["black"], 0.55 + 0.3 * h01(i, step, 63))
            cv.put(x, y, DUST[int(h01(i, step, 64) * 4)], c)


def chroma(cv, t, k=0.18):
    """R/B fringing on glyph edges — colour only, never the characters."""
    if k <= 0.01:
        return
    red = (255, 48, 74)
    cyan = (74, 214, 255)
    for y in range(cv.h):
        ch = cv.ch[y]
        fg = cv.fg[y]
        for x in range(cv.w):
            c = fg[x]
            if c is None or ch[x] == " " or ch[x] == "\x00":
                continue
            left = x > 0 and ch[x - 1] == " "
            right = x + 1 < cv.w and ch[x + 1] == " "
            if left and not right:
                fg[x] = mix(c, red, 0.45 * k)
            elif right and not left:
                fg[x] = mix(c, cyan, 0.40 * k)
            elif left and right:
                fg[x] = mix(c, red if h01(x, y, 33) < 0.5 else cyan, 0.30 * k)


def dropout(cv, t, k=0.3):
    """Signal dropouts: a couple of torn seams with noise bleeding through."""
    step = int(t * 8)
    n = 1 + int(k * 2)
    for i in range(n):
        y = int(h01(i, step, 71) * cv.h)
        x0 = int(h01(i, step, 72) * cv.w * 0.65)
        ln = int(6 + h01(i, step, 73) * cv.w * 0.45)
        for x in range(x0, min(cv.w, x0 + ln)):
            cv.ch[y][x] = " "
            cv.fg[y][x] = None
            cv.bg[y][x] = None
        for x in range(x0, min(cv.w, x0 + ln)):
            if h01(x, y, step, 74) < 0.18:
                cv.ch[y][x] = "▒"
                cv.fg[y][x] = mix(P["white"], P["phos"], 0.4)


def vhold(cv, t, k=0.35):
    """Vertical hold losing it: one-row slip plus a black flyback band."""
    if k <= 0.01:
        return
    dy = 1 if h01(int(t * 10), 81) < 0.6 else -1
    cv.roll(0, dy)
    y = 0 if dy > 0 else cv.h - 1
    cv.fill(0, y, cv.w, 1, " ", None, None)
    if k > 0.5:
        y2 = cv.h - 1 if dy > 0 else 0
        cv.fill(0, y2, cv.w, 1, " ", None, None)


def flag(cv, t):
    """Tape warp: the two rows just above the beam slip sideways."""
    h = cv.h
    y0 = int((t * 9.0) % (h + 10)) - 5
    for j in (-2, -1):
        y = y0 + j
        if not (0 <= y < h):
            continue
        dx = int(round(math.sin(t * 6.3 + y * 0.7) * 1.5))
        if dx:
            cv.ch[y] = cv.ch[y][-dx:] + cv.ch[y][:-dx]
            cv.fg[y] = cv.fg[y][-dx:] + cv.fg[y][:-dx]
            cv.bg[y] = cv.bg[y][-dx:] + cv.bg[y][:-dx]


def interlace(cv, t, k=0.045):
    """Half-line flicker: odd rows drift in brightness, like a real tube."""
    if int(t * 20) % 2:
        return
    for y in range(1, cv.h, 2):
        row = cv.fg[y]
        for x in range(cv.w):
            c = row[x]
            if c is not None:
                row[x] = shade(c, 1.0 - k)


def flash(cv, t, k=0.06):
    """Beat bloom: the tube blooms a little when the kick lands."""
    for y in range(cv.h):
        row = cv.fg[y]
        for x in range(cv.w):
            c = row[x]
            if c is not None:
                row[x] = mix(c, P["white"], k)


def corners(cv):
    """Masked tube corners (radius-2 arc), so the frame is not a hard rectangle."""
    w, h = cv.w, cv.h
    for (x, y, ch) in ((0, 1, "╭"), (w - 1, 1, "╮"), (0, h - 2, "╰"), (w - 1, h - 2, "╯")):
        if 0 <= x < w and 0 <= y < h:
            cv.put(x, y, ch, mix(P["grey_dim"], P["black"], 0.5))


def scan_gap(cv, t, heavy=0.0):
    """A dropped scanline: one row's cells replaced by half-tone blocks."""
    step = int(t * 0.8)
    if heavy < 0.05 and step % 4:
        return
    for i in range(1 + int(h01(step, 51) * 1.6)):
        y = int(h01(i, step, 53) * cv.h)
        if not (0 < y < cv.h - 1):
            continue
        row = cv.ch[y]
        fg = cv.fg[y]
        for x in range(cv.w):
            c = row[x]
            if c != " " and c != "\x00" and (x + y) % 2:
                row[x] = "░" if h01(x, y, 55) < 0.6 else "▒"
                fg[x] = mix(fg[x] or P["phos"], P["black"], 0.30)


def _free(cv, x, y, w, h):
    """True when that rectangle is mostly empty (so labels can go there)."""
    if x < 0 or y < 0 or x + w > cv.w or y + h > cv.h:
        return False
    n = 0
    for yy in range(y, y + h):
        row = cv.ch[yy]
        for xx in range(x, x + w):
            if row[xx] != " " and row[xx] != "\x00":
                n += 1
    return n <= int(w * h * 0.18)


def osd(cv, t, ac):
    """Instrument telemetry in the corners — only where nothing is drawn."""
    w, h = cv.w, cv.h
    if w < 56 or h < 12:
        return
    dim = mix(ac, P["black"], 0.58)
    dim2 = mix(ac, P["black"], 0.72)
    if _free(cv, w - 24, 1, 22, 2):
        cv.rtext(1, "⌁ SYNC %5.1f%% ●" % (95.4 + 4.4 * h01(int(t * 3), 41)),
                 dim2, right=w - 2)
        cv.rtext(2, "F%05d · %dx%d · 60Hz" % (int(t * 20) % 100000, w, h + 3),
                 dim2, right=w - 2)
    if _free(cv, 1, 2, 20, 2):
        cv.text(2, 2, "VID P1 · CH03", dim2)
        cv.text(2, 3, "Δ %3d ms" % (12 + int(9 * h01(int(t * 5), 43))), dim2)
    if _free(cv, 1, h - 2, 22, 1):
        cv.text(2, h - 2, "SIG 0x%03X · AGC %2d%%" % (
            (int(t * 61) & 0xFFF), 70 + int(28 * h01(int(t * 4), 45))), dim2)


def overdrive(cv, t):
    """A hard 2% white-out on the loudest beats (very short)."""
    for y in range(0, cv.h, 2):
        row = cv.fg[y]
        for x in range(cv.w):
            c = row[x]
            if c is not None:
                row[x] = mix(c, P["white"], 0.16)


# --------------------------------------------------------------------------
# the full pass
# --------------------------------------------------------------------------

def apply(cv, t, ac, heavy=0.0, beat_phase=1.0):
    """Run the tube chain over a finished scene canvas.

    heavy: 0..1, how badly the signal is broken right now (0 = clean).
    """
    beam(cv, t, ac)
    flag(cv, t)
    interlace(cv, t, 0.035 + 0.035 * heavy)
    if heavy > 0.02:
        chroma(cv, t, 0.12 + 0.5 * heavy)
        vhold(cv, t, heavy)
        dropout(cv, t, heavy)
        if heavy > 0.35:
            overdrive(cv, t)
    scan_gap(cv, t, heavy)
    osd(cv, t, ac)
    grain(cv, t, ac, 1.0 + heavy)
    if beat_phase < 0.10:
        flash(cv, t, 0.05 + 0.12 * (1.0 - beat_phase / 0.10) * (0.4 + heavy))
    corners(cv)
