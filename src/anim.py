"""Animation kit: the shared grammar every beat of the MV is built from.

The film never "jumps" from one tableau to the next.  Each beat is built out
of four moves, and this module gives one primitive per move:

    build   assemble()  type_lines()  sweep()  meter()
    morph   dissolve()  -- the thing just built turns into the next thing
    track   ladder()  counter()  meter()  -- an instrument counts it happening

Everything is a pure function of `t`, so seeking stays frame-exact: no state
is ever carried between calls, and every "random" choice comes from h01().

Style rules that the primitives already respect (keep them when you use them):

  * nothing is drawn in rows 0..3 (top telemetry) or the last 2 rows;
  * any text drawn on top of a panel must pass bg=, because composite()
    skips blank cells and the panel would leak through;
  * a dissolve never shows both states at full alpha: it is cell-wise, so
    the eye reads it as "this becomes that".
"""

import math

from renderer import Canvas, P, h01, mix, shade, sw, cw, CONT
from base import ramp

__all__ = ["dissolve", "dissolve_canvases", "assemble", "type_lines", "sweep",
           "ladder", "meter", "counter", "orbit", "slice_glitch", "rise",
           "ticker", "hand_off", "pulse_bars", "flow", "brackets",
           "dial", "hexrow", "type_loop", "echo_row"]


# --------------------------------------------------------------------------
# morph
# --------------------------------------------------------------------------

def dissolve(cv, t, t0, t1, fn_a, fn_b, seed=7, band=0.14,
             scram_fg=None, bg=None):
    """Morph state A (fn_a) into state B (fn_b) cell by cell.

    `fn_a` / `fn_b` take a Canvas and draw one whole state.  The crossover is
    a per-cell threshold, so cells flip in a speckled wave instead of the two
    states being blended into mud.  `band` is the width of the crackling
    front, which is drawn as `▒` / `░` so the seam is visible.
    """
    k = ramp(t, t0, t1)
    if k <= 0.0:
        fn_a(cv)
        return
    if k >= 1.0:
        fn_b(cv)
        return
    ca = Canvas(cv.w, cv.h)
    cb = Canvas(cv.w, cv.h)
    fn_a(ca)
    fn_b(cb)
    if scram_fg is None:
        scram_fg = P["white"]
    half = max(0.02, band * 0.5)
    for y in range(cv.h):
        ra, rb = ca.ch[y], cb.ch[y]
        fa, fb = ca.fg[y], cb.fg[y]
        ba, bb = ca.bg[y], cb.bg[y]
        for x in range(cv.w):
            if ra[x] in (" ", CONT) and rb[x] in (" ", CONT):
                continue          # empty in both states: leave the canvas alone
            v = h01(x * 7 + 13, y * 11 + 5, seed)
            if abs(v - k) < half and h01(x, y, seed + 3) < 0.55:
                cv.put(x, y, "▒" if v < k else "░", scram_fg, bg)
                continue
            if v < k:
                cv.put(x, y, rb[x], fb[x], bb[x] if bb[x] is not None else bg)
            else:
                cv.put(x, y, ra[x], fa[x], ba[x] if ba[x] is not None else bg)


def dissolve_canvases(dst, ca, cb, k, seed=7, band=0.18, scram_fg=None):
    """Morph a whole rendered frame A into frame B, cell by cell.

    This is the scene-to-scene hand-off: the outgoing picture does not fade,
    it is *eaten away* by a speckled front while the incoming picture fills
    the holes it leaves.  Cell-wise flipping instead of alpha blending is what
    keeps two different scenes from ever being visible on top of each other.
    """
    if k <= 0.0:
        dst.copy_from(ca)
        return
    if k >= 1.0:
        dst.copy_from(cb)
        return
    if scram_fg is None:
        scram_fg = P["white"]
    half = max(0.02, band * 0.5)
    for y in range(dst.h):
        ra, rb = ca.ch[y], cb.ch[y]
        for x in range(dst.w):
            if ra[x] in (" ", CONT) and rb[x] in (" ", CONT):
                continue
            v = h01(x * 7 + 13, y * 11 + 5, seed)
            if abs(v - k) < half and h01(x, y, seed + 3) < 0.5:
                dst._place(y, x, "▒" if v < k else "░", scram_fg, None)
            elif v < k:
                dst._place(y, x, rb[x], cb.fg[y][x], cb.bg[y][x])
            else:
                dst._place(y, x, ra[x], ca.fg[y][x], ca.bg[y][x])


def hand_off(cv, t, t0, t1, draw_fn, seed=11):
    """Fade a finished beat away by breaking it into speckle.

    Draw it normally until t0, then progressively punch cells out of it, so
    the next beat can build *through* the holes instead of after a fade.
    """
    if t < t0:
        draw_fn(cv)
        return
    if t >= t1:
        return
    k = ramp(t, t0, t1)
    tmp = Canvas(cv.w, cv.h)
    draw_fn(tmp)
    for y in range(cv.h):
        for x in range(cv.w):
            c = tmp.ch[y][x]
            if c == " " or c == CONT:
                continue
            v = h01(x * 5 + 7, y * 3 + 1, seed)
            if v < k * 1.08:
                continue
            cv.put(x, y, c, tmp.fg[y][x], tmp.bg[y][x])


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def assemble(cv, x, y, art_rows, k, fg, seed=3, spread=7, snap=0.45,
             bg=None, map_fg=None, y_min=None):
    """A sprite assembling itself: cells fly in from scattered positions.

    k=0 nothing, k=1 fully formed.  Each cell travels from a hash-scattered
    start point to its final cell, and the last stretch snaps, so it reads as
    "pulled together and locked" rather than a fade.
    """
    if k <= 0.0:
        return
    last = max(1, len(art_rows))
    for j, line in enumerate(art_rows):
        yy = y + j
        if yy < 0 or yy >= cv.h:
            continue
        cx = x
        for c in line:
            wd = cw(c)
            if wd == 0:
                continue
            if c != " ":
                cell = int(h01(cx, yy, seed) * 61)
                d = 1.0 - k
                sx = int(cx + (h01(cell, 1, seed) * 2 - 1) * spread * d)
                sy = int(yy + (h01(cell, 2, seed) * 2 - 1) * spread * d * 0.5)
                if y_min is not None and sy < y_min:
                    sy = y_min
                if d < snap * 0.2:
                    sx, sy = cx, yy
                cf = map_fg(c, cx - x, j) if map_fg else fg
                al = shade(cf, min(1.0, 0.35 + 0.65 * k)) if cf is not None else None
                cv.put(sx, sy, c, al, bg)
            cx += wd


def type_lines(cv, x, y, rows, t, t0, cps=40.0, stagger=0.34,
               fg=None, bg=None, cursor=True, dim_after=None):
    """Type a block of lines in order, one cursor.

    y is the first row; each line i starts at t0 + i*stagger.  A line that is
    still being typed gets a blinking `▮` cursor.  `dim_after` may be a
    callback(line_index) -> color used once the line is complete.
    """
    from fx import typewriter
    shown_all = 0
    for i, s in enumerate(rows):
        at = t0 + i * stagger
        if t < at:
            break
        shown, typing = typewriter(s, t - at, cps)
        col = fg
        if not typing and dim_after is not None:
            col = dim_after(i)
        end = cv.text(x, y + i, shown, col, bg)
        shown_all += 1
        if cursor and typing and int(t * 12) % 2 == 0:
            cv.put(end, y + i, "▮", col, bg)
    return shown_all


def sweep(cv, x0, y0, x1, y1, k, ch, fg, bg=None, trail=None):
    """Draw a line progressively (a needle tracing it), k in 0..1."""
    n = max(1, int(abs(x1 - x0)) + 1 if abs(x1 - x0) >= abs(y1 - y0)
            else int(abs(y1 - y0)) + 1)
    last = int(n * max(0.0, min(1.0, k)))
    for i in range(last):
        f = i / float(n)
        xx = int(x0 + (x1 - x0) * f)
        yy = int(y0 + (y1 - y0) * f)
        cv.put(xx, yy, ch, fg, bg)
    if trail and 0 < last <= n:
        f = (last - 1) / float(n)
        cv.put(int(x0 + (x1 - x0) * f), int(y0 + (y1 - y0) * f), trail, fg, bg)


def rise(cv, x, ybase, k, peak, ch, fg, bg=None, w=1):
    """A column growing up from ybase by k*peak."""
    n = int(peak * max(0.0, min(1.0, k)))
    for j in range(n):
        for i in range(w):
            cv.put(x + i, ybase - j, ch, fg, bg)


# --------------------------------------------------------------------------
# track
# --------------------------------------------------------------------------

def ladder(cv, x, y, rows, active, fg_on, fg_off, bg=None, marker="▸",
           width=None, gap=0):
    """The instrument ladder: one line per state, the current one lit.

    rows is a list of already-formatted strings; `active` is the index that
    is "true right now".  Rows above the active one are lit a little more
    than rows below it, because they have already happened.
    """
    for i, s in enumerate(rows):
        on = (i == active)
        col = fg_on if on else fg_off
        if not on and i < active:
            col = mix(fg_off, fg_on, 0.35)
        if marker and on:
            cv.text(x, y + i * (1 + gap), marker, col, bg)
        txt = s if width is None else s[:width]
        cv.text(x + (2 if marker else 0), y + i * (1 + gap), txt, col, bg)


def meter(cv, x, y, label, val, vmax, width, fg, bg=None, dim_fg=None,
          full="█", empty="░", suffix=""):
    """`label ▕██████░░░░▏ 62%` -- a labelled horizontal gauge."""
    if dim_fg is None:
        dim_fg = mix(fg, P["black"], 0.55)
    cv.text(x, y, label, dim_fg, bg)
    bx = x + sw(label) + 1
    k = 0.0 if vmax <= 0 else max(0.0, min(1.0, val / float(vmax)))
    n = int(round(width * k))
    cv.put(bx, y, "▕", dim_fg, bg)
    for i in range(width):
        cv.put(bx + 1 + i, y, full if i < n else empty,
               fg if i < n else mix(dim_fg, P["black"], 0.5), bg)
    cv.put(bx + 1 + width, y, "▏", dim_fg, bg)
    cv.text(bx + width + 3, y, "%3d%%%s" % (int(k * 100), suffix), fg, bg)
    return bx + width + 3 + 4


def counter(cv, x, y, label, val, fmt, fg, bg=None, dim_fg=None):
    """`label 0x0F3A` -- a number that can be watched changing."""
    if dim_fg is None:
        dim_fg = mix(fg, P["black"], 0.5)
    cv.text(x, y, label, dim_fg, bg)
    cv.text(x + sw(label) + 1, y, fmt % val, fg, bg)


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def orbit(cx, cy, rx, ry, ang):
    """Point on an ellipse (terminal cells, so ry is usually rx/2)."""
    return (int(cx + rx * math.cos(ang)), int(cy + ry * math.sin(ang)))


def slice_glitch(cv, y0, y1, t, seed=5, n=2, amt=3):
    """Shift a few horizontal slices sideways -- a signal tear."""
    if y1 - y0 < 3:
        return
    for i in range(n):
        band = h01(i, seed, int(t * 3))
        yy = y0 + int(band * (y1 - y0))
        dx = int((h01(i, seed + 1, int(t * 3)) * 2 - 1) * amt)
        if dx == 0:
            continue
        row_ch = cv.ch[yy][:]
        row_fg = cv.fg[yy][:]
        row_bg = cv.bg[yy][:]
        for x in range(cv.w):
            s = x - dx
            if 0 <= s < cv.w:
                cv.ch[yy][x] = row_ch[s]
                cv.fg[yy][x] = row_fg[s]
                cv.bg[yy][x] = row_bg[s]


def ticker(cv, y, s, t, speed=14.0, fg=None, bg=None, x0=1, x1=None):
    """A one-line marquee scrolling right-to-left, wrapping."""
    if x1 is None:
        x1 = cv.w - 2
    span = max(1, x1 - x0)
    width = sw(s)
    if width <= 0:
        return
    txt = s * (span // width + 2)
    off = int(t * speed) % width
    cv.text(x0, y, txt[off:off + span], fg, bg)


def scanline(cv, t, y0, y1, fg=None, speed=18.0, band=3, seed=5, k=1.0):
    """A read head crosses the frame from top to bottom.

    Where it passes, the ink saturates (text blooms into half-tone, rules
    thicken) and the row is re-lit, so a page of text keeps being *read*
    instead of sitting there.  Never touches the rows outside `[y0, y1)`.
    """
    if y1 <= y0 or k <= 0.02:
        return
    w = cv.w
    span = (y1 - y0) + band * 2
    head = y0 - band + int((t * speed) % span)
    for dy in range(band):
        y = head + dy
        if not (y0 <= y < y1):
            continue
        row, rfg = cv.ch[y], cv.fg[y]
        edge = 1.0 - abs(dy - (band - 1) / 2.0) / (band / 2.0 + 0.6)
        for x in range(1, w - 1):
            c = row[x]
            if c == " " or c == "\x00":
                continue
            if edge > 0.6 and h01(x, y, seed) < edge * 0.92 * k:
                row[x] = "▓" if h01(x, y, seed + 2) < 0.5 else "▒"
            elif c in "─┄┅":
                row[x] = "━"
            elif c in "│┊":
                row[x] = "┃"
            rfg[x] = shade(fg or P["white"], 0.92)

# --------------------------------------------------------------------------
# live-motion kit (round 3): bars that breathe, streams that carry gifts,
# frames that lock on, gauges that read, buses that flicker
# --------------------------------------------------------------------------

def pulse_bars(cv, x, y, n, t, fg, hmax=6, seed=0, gap=1, hz=3.1):
    """An EQ-style bar array breathing at staggered harmonics: live spectrum
    energy rather than a still meter.  Bars grow up from row `y`."""
    for i in range(n):
        v = (abs(math.sin(i * 0.9 + seed + t * hz)) * 0.6
             + abs(math.cos(t * hz * 0.62 + i * 1.7 + seed)) * 0.4)
        hgt = max(1, int(hmax * v))
        for j in range(hgt):
            cv.put(x + i * (1 + gap), y - j,
                   "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"[min(7, (j * 8) // hgt)],
                   fg)


def flow(cv, x0, y0, x1, y1, t, n=8, fg=None, ch="\u00b7", arc=2.0, speed=0.7,
         tail=True, seed=0):
    """A stream of packets travelling A->B on a slight arc, each dragging a
    comet tail: the workhorse for "me gives something to you"."""
    if fg is None:
        fg = P["ice"]
    dx, dy = x1 - x0, y1 - y0
    for i in range(n):
        u = (t * speed + (i + h01(i, seed)) / float(n)) % 1.0
        for k, chh, al in ((0, ch, 1.0), (1, "\u00b7", 0.55), (2, "\u00b7", 0.28)):
            uu = u - 0.045 * k
            if not tail and k:
                continue
            if uu <= 0.0 or uu >= 1.0:
                continue
            cv.put(int(round(x0 + dx * uu)),
                   int(round(y0 + dy * uu - math.sin(uu * math.pi) * arc)),
                   chh, shade(fg, al))


def brackets(cv, x, y, w_, h_, fg, k=1.0):
    """Pulsing corner brackets framing the object currently in play; k in
    [0, 1] grows the arms so the frame reads as "locking on"."""
    if w_ < 2 or h_ < 2:
        return
    for px, py, cc in ((x, y, "\u250c"), (x + w_ - 1, y, "\u2510"),
                       (x, y + h_ - 1, "\u2514"), (x + w_ - 1, y + h_ - 1, "\u2518")):
        cv.put(px, py, cc, fg)
    arm = max(1, min(3, int(round(2 * k))))
    for i in range(1, arm + 1):
        if i < w_ - 1:
            cv.put(x + i, y, "\u2500", fg)
            cv.put(x + w_ - 1 - i, y, "\u2500", fg)
            if h_ > 2:
                cv.put(x + i, y + h_ - 1, "\u2500", fg)
                cv.put(x + w_ - 1 - i, y + h_ - 1, "\u2500", fg)
    if h_ > 2:
        cv.put(x, y + 1, "\u2502", fg)
        cv.put(x + w_ - 1, y + 1, "\u2502", fg)


def dial(cv, cx, cy, r, val, fg, label=None, bg=None):
    """A round gauge: twelve ticks, a needle at val in [0, 1), an optional
    caption row under the dial."""
    val = max(0.0, min(0.999, val))
    for i in range(12):
        a = -math.pi / 2 + 2 * math.pi * i / 12.0
        cv.put(int(round(cx + math.cos(a) * r)),
               int(round(cy + math.sin(a) * r * 0.6)), "\u00b7", shade(fg, 0.4))
    a = -math.pi / 2 + 2 * math.pi * val
    for k in range(1, r):
        cv.put(int(round(cx + math.cos(a) * k)),
               int(round(cy + math.sin(a) * k * 0.6)),
               "\u2022" if k == r - 1 else "\u00b7", fg)
    cv.put(cx, cy, "\u25c9", fg)
    if label and 0 < cy + int(r * 0.6) + 1 < cv.h:
        cv.text(cx - sw(label) // 2, cy + int(r * 0.6) + 1, label, fg, bg=bg)


def hexrow(cv, x, y, n, t, fg, seed=0, hz=10):
    """n flickering hex bytes: a live data bus that never stops moving."""
    for i in range(n):
        cv.text(x + i * 3, y,
                "%02X" % int(h01(i, int(t * hz), seed) * 256), fg)

# --------------------------------------------------------------------------
# obsessive text (round 4): the machine cannot stop saying certain words
# --------------------------------------------------------------------------

def type_loop(t, t0, word, cycles, cps=16.0, hold=0.35, wipe=0.20, gap=0.10,
              accel=1.0, del_last=False):
    """Type `word`, hold, delete it backward, pause, repeat -- `cycles` times.

    By default the LAST cycle never deletes (the word that finally lands);
    pass del_last=True when something else follows immediately.  accel < 1
    makes later cycles shorter (desperation); 1.0 keeps a steady ritual.
    Pure function of t.  Returns (visible, k, phase) with phase in
    {"type", "hold", "wipe", "gap", "stay"} -- draw a blinking cursor while
    phase is "type" or "wipe" and flash the word on the "hold" entry frame.
    """
    w = float(len(word))
    d_type = w / cps
    if t < t0:
        return "", 0, "gap"
    tt = t - t0
    base = d_type + hold + wipe + gap
    k = 0
    while k < cycles - 1:
        d = base * (accel ** k)
        if tt < d:
            break
        tt -= d
        k += 1
    last = (k == cycles - 1)
    if tt < d_type:
        return word[:max(0, int(tt * cps))], k, "type"
    tt -= d_type
    if tt < hold:
        return word, k, "hold"
    if last and not del_last:
        return word, k, "stay"
    tt -= hold
    if tt < wipe:
        n = int(w - tt * (w / wipe))
        return word[:max(0, min(int(w), n))], k, "wipe"
    return "", k, "gap"


def echo_row(cv, x, y, word, t, t0, n=2, fg=None, sep="  ", decay=0.55,
             cps=14.0, cx=None):
    """The word and its typed echoes side by side, older copies dimmer --
    for doubled lyrics ("so dizzy so dizzy", "the trance the trance",
    "strange strange simulation").  Copy i starts typing at
    t0 + i * (len(word)/cps + 0.30).  If cx is given the whole row is
    centred there instead of left-aligned at x."""
    fg = fg or P["white"]
    if cx is not None:
        x = cx - (n * len(word) + (n - 1) * len(sep)) // 2
    for i in range(n):
        age = t - t0 - i * (len(word) / float(cps) + 0.30)
        if age <= 0:
            continue
        vis = word[:max(0, int(age * cps))]
        if vis:
            cv.text(x + i * (len(word) + len(sep)), y, vis,
                    shade(fg, decay ** i))
