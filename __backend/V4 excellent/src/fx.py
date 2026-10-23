"""Visual effects helpers shared by the scenes."""

import math

from renderer import mix, shade, grey, h01, sw, P

MS = 2.0        # terminal cells are roughly twice as tall as wide


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def smooth(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def ease_out(v):
    v = clamp(v)
    return 1 - (1 - v) ** 3


def pulse(t, beat_phase, k=0.5):
    """Beat pulse 1 -> 0 within each beat."""
    return math.exp(-beat_phase * 6.0) * k


# --------------------------------------------------------------------------
# text helpers
# --------------------------------------------------------------------------

def typewriter(s, age, cps=30.0, start=0.0):
    n = int(max(0.0, age - start) * cps)
    return s[:n], n < len(s)


def reveal(s, k):
    """Reveal a left-to-right fraction of s."""
    n = int(round(len(s) * clamp(k)))
    return s[:n]


def marquee(s, t, w, speed=12.0):
    """Rotating marquee text of given width."""
    if not s:
        return ""
    n = len(s)
    off = int(t * speed) % (n + w)
    buf = (" " * w + s + " " * w)[off:off + w]
    return buf


# --------------------------------------------------------------------------
# waves and curves
# --------------------------------------------------------------------------

def wave_row(cv, y0, amp, freq, phase, fg, ch="∿", x0=0, x1=None, thick=0):
    x1 = cv.w - 1 if x1 is None else x1
    for x in range(x0, x1 + 1):
        y = y0 + int(round(amp * math.sin(freq * x + phase)))
        if thick:
            for dy in range(-thick, thick + 1):
                cv.put(x, y + dy, ch, fg)
        else:
            cv.put(x, y, ch, fg)


def wave_char_cell(cv, y0, amp, freq, phase, fg, x0=0, x1=None, chars="▁▂▃▄▅▆▇█"):
    """Block-based waveform: height of a filled column per x."""
    x1 = cv.w - 1 if x1 is None else x1
    n = len(chars)
    for x in range(max(0, x0), min(cv.w, x1 + 1)):
        v = (math.sin(freq * x + phase) + 1) / 2
        h = int(v * (n - 1))
        cv.put(x, y0, chars[h], fg)


def sine_curve(cv, y_center, amp, freq, phase, fg, ch="·", step=1):
    pts = []
    for x in range(0, cv.w, step):
        y = y_center - int(round(amp * math.sin(freq * x + phase)))
        cv.put(x, y, ch, fg)
        pts.append((x, y))
    return pts


def circle(cv, cx, cy, r, fg, ch="•", a0=0.0, a1=2 * math.pi, ry=None, steps=None):
    ry = r / MS if ry is None else ry
    steps = max(24, int(abs(a1 - a0) * r * 3)) if steps is None else steps
    pts = []
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        x = cx + int(round(r * math.cos(a)))
        y = cy + int(round(ry * math.sin(a)))
        if (x, y) not in pts:
            cv.put(x, y, ch, fg)
            pts.append((x, y))
    return pts


def line(cv, x0, y0, x1, y1, fg, ch=None, dash=None):
    dx, dy = x1 - x0, y1 - y0
    n = max(abs(dx), abs(dy))
    if n == 0:
        cv.put(x0, y0, ch or "·", fg)
        return
    for i in range(n + 1):
        x = x0 + dx * i / n
        y = y0 + dy * i / n
        if dash and (i // 2) % 2 == 0:
            continue
        c = ch
        if c is None:
            if abs(dx) >= abs(dy) * 1.6:
                c = "─"
            elif abs(dy) >= abs(dx) * 1.6:
                c = "│"
            else:
                c = "╱" if (dx > 0) == (dy < 0) else "╲"
        cv.put(int(round(x)), int(round(y)), c, fg)


# --------------------------------------------------------------------------
# backgrounds
# --------------------------------------------------------------------------

def grid_floor(cv, horizon, fg, phase=0.0, rows=4, spread=11):
    """Dotted perspective floor receding to `horizon`."""
    h = cv.h
    span = max(1, h - 1 - horizon)
    cv.hline(0, horizon, cv.w, "─", shade(fg, 1.0))
    for i in range(1, rows + 1):
        k = (i / rows) ** 2.1
        y = horizon + int(round(span * k))
        if 0 <= y < h:
            cv.hline(0, y, cv.w, "─", shade(fg, 0.45 + 0.4 * k))
    cxm = cv.w // 2
    for y in range(horizon + 1, h - 1, 2):
        k = (y - horizon) / span
        for i in range(-13, 14):
            xh = cxm + i * 3
            xb = cxm + i * spread
            x = int(round(xh + (xb - xh) * (k ** 1.7)))
            cv.put(x, y, "│", shade(fg, 0.3 + 0.55 * k))


def matrix_rain(cv, t, fg, charset="01;(){}[]<>=+*exec", speed=14.0, density=0.55,
                seed=0, tail=5, dim_to=None):
    """Deterministic falling glyph columns."""
    w, h = cv.w, cv.h
    for col in range(w):
        if h01(col, seed) > density:
            continue
        sp = speed * (0.6 + 0.8 * h01(col, seed + 1))
        head = (t * sp + h01(col, seed + 2) * 100) % (h + tail + 6)
        hy = int(head) - tail - 3
        for k in range(tail):
            y = hy - k
            if 0 <= y < h:
                ch = charset[int(h01(col, y, seed) * len(charset))]
                f = fg if k == 0 else shade(fg, 1.0 - k / (tail + 1.0) * 0.85)
                if dim_to is not None:
                    f = mix(f, dim_to, 0.3)
                cv.put(col, y, ch, f)


def starfield(cv, t, fg, n=60, seed=3):
    for i in range(n):
        x = int(h01(i, seed) * cv.w)
        y = int((h01(i, seed + 1) + t * 0.01 * (0.2 + h01(i, seed + 2))) * cv.h) % cv.h
        ch = "·" if h01(i, seed + 3) < 0.7 else "+"
        cv.put(x, y, ch, shade(fg, 0.3 + 0.7 * h01(i, seed + 4)))


def scanlines(cv, k=0.72):
    for y in range(0, cv.h, 2):
        for x in range(cv.w):
            if cv.fg[y][x] is not None:
                cv.fg[y][x] = shade(cv.fg[y][x], k)


def vignette(cv, amount=0.3):
    cxm, cym = cv.w / 2, cv.h / 2
    for y in range(cv.h):
        dy = (y - cym) / cym
        for x in range(cv.w):
            dx = (x - cxm) / cxm
            d = min(1.0, dx * dx * 0.6 + dy * dy * 0.9)
            f = cv.fg[y][x]
            if f is not None:
                cv.fg[y][x] = shade(f, 1.0 - amount * d)


def glitch(cv, t, intensity=0.4, seed=0):
    """Row displacement + character corruption."""
    if intensity <= 0:
        return
    step = int(t * 18)
    for y in range(cv.h):
        if h01(y, step, seed) < intensity * 0.35:
            shift = int((h01(y, step, seed + 1) - 0.5) * cv.w * 0.25)
            if shift:
                row = cv.ch[y]
                frow = cv.fg[y]
                brow = cv.bg[y]
                if shift > 0:
                    cv.ch[y] = [" "] * shift + row[:-shift]
                    cv.fg[y] = [None] * shift + frow[:-shift]
                    cv.bg[y] = [None] * shift + brow[:-shift]
                else:
                    s = -shift
                    cv.ch[y] = row[s:] + [" "] * s
                    cv.fg[y] = frow[s:] + [None] * s
                    cv.bg[y] = brow[s:] + [None] * s
    for i in range(int(cv.w * cv.h * intensity * 0.04)):
        x = int(h01(i, step, seed + 7) * cv.w)
        y = int(h01(i, step, seed + 8) * cv.h)
        if cv.ch[y][x] != " ":
            cv.ch[y][x] = "%&@#$?!*" [int(h01(i, step, seed + 9) * 8)]
            cv.fg[y][x] = (255, 70, 90)


# --------------------------------------------------------------------------
# ui bits
# --------------------------------------------------------------------------

def bar(cv, x, y, w, k, fg, bg, full="█", rest="░"):
    n = int(round(w * clamp(k)))
    for i in range(w):
        cv.put(x + i, y, full if i < n else rest, fg if i < n else shade(fg, 0.45), bg)


def bracket(cv, x, y, w, h, fg, style="[]"):
    if style == "[]":
        tl, tr, bl, br, hz, vt = "[", "]", "[", "]", "─", "│"
    elif style == "<>":
        tl, tr, bl, br, hz, vt = "┌", "┐", "└", "┘", "─", "│"
    else:
        tl, tr, bl, br, hz, vt = "▛", "▜", "▙", "▟", "▀", "▌"
    cv.hline(x + 1, y, w - 2, hz, fg)
    cv.hline(x + 1, y + h - 1, w - 2, hz, fg)
    cv.vline(x, y + 1, h - 2, vt, fg)
    cv.vline(x + w - 1, y + 1, h - 2, vt, fg)
    cv.put(x, y, tl, fg)
    cv.put(x + w - 1, y, tr, fg)
    cv.put(x, y + h - 1, bl, fg)
    cv.put(x + w - 1, y + h - 1, br, fg)


def panel(cv, x, y, w, h, fg, bg=None, title=None, title_fg=None):
    cv.fill(x, y, w, h, " ", None, bg)
    cv.hline(x + 1, y, w - 2, "─", fg, bg)
    cv.hline(x + 1, y + h - 1, w - 2, "─", fg, bg)
    cv.vline(x, y + 1, h - 2, "│", fg, bg)
    cv.vline(x + w - 1, y + 1, h - 2, "│", fg, bg)
    for (px, py, c) in ((x, y, "┌"), (x + w - 1, y, "┐"),
                        (x, y + h - 1, "└"), (x + w - 1, y + h - 1, "┘")):
        cv.put(px, py, c, fg, bg)
    if title:
        cv.text(x + 2, y, " %s " % title, title_fg or fg, bg)


def sparkle(cv, x, y, t, fg, seed=0, n=6, rad=4):
    for i in range(n):
        a = h01(i, seed) * 6.283 + t * (0.8 + h01(i, seed + 1))
        r = rad * (0.4 + 0.6 * h01(i, seed + 2))
        px = int(x + math.cos(a) * r * 1.6)
        py = int(y + math.sin(a) * r / 1.4)
        cv.put(px, py, "✦" if h01(i, seed + 3) < 0.4 else "·", fg)


def ripple(cv, cx, cy, t, fg, n=3, speed=9.0, period=1.4, ch="·"):
    for i in range(n):
        age = (t / period + i / n) % 1.0
        r = age * speed
        if r < 0.6:
            continue
        a = 1.0 - age
        c = shade(fg, 0.35 + 0.65 * a)
        pts = circle(cv, cx, cy, int(r), c, ch, steps=max(16, int(r * 6)))
        _ = pts


def beam(cv, cx, y0, y1, fg, w=1):
    for y in range(y0, y1 + 1):
        for dx in range(-w, w + 1):
            cv.put(cx + dx, y, "█", fg)


def digit_roll(cv, x, y, value, width, fg, bg=None):
    s = str(int(value)).rjust(width)
    cv.text(x, y, s, fg, bg)


def shake(cv, t, amp=1.0, seed=0):
    """Return a seeded small offset for shake effects."""
    return (int(h01(int(t * 20), seed) * 2 * amp) - int(amp),
            int(h01(int(t * 20), seed + 1) * 2 * amp) - int(amp))


def desaturate(cv, k, dim=1.0):
    """Push all colors toward grey by k, optionally dim."""
    if k <= 0 and dim >= 1.0:
        return
    for y in range(cv.h):
        frow = cv.fg[y]
        for x in range(cv.w):
            c = frow[x]
            if c is None:
                continue
            if k > 0:
                c = grey(c, k)
            if dim != 1.0:
                c = shade(c, dim)
            frow[x] = c


def row_wave(cv, t, amp=2.0, freq=0.35, speed=3.0):
    """Horizontal per-row displacement — hypnotic warp."""
    for y in range(cv.h):
        dx = int(round(amp * math.sin(y * freq + t * speed)))
        if not dx:
            continue
        row = cv.ch[y]
        frow = cv.fg[y]
        brow = cv.bg[y]
        if dx > 0:
            cv.ch[y] = [" "] * dx + row[:-dx]
            cv.fg[y] = [None] * dx + frow[:-dx]
            cv.bg[y] = [None] * dx + brow[:-dx]
        else:
            s = -dx
            cv.ch[y] = row[s:] + [" "] * s
            cv.fg[y] = frow[s:] + [None] * s
            cv.bg[y] = brow[s:] + [None] * s


def ecg(u):
    """Single heartbeat waveform, u in [0,1)."""
    u = u % 1.0
    if u < 0.18:
        return 0.16 * math.sin(u / 0.18 * math.pi)
    if u < 0.30:
        return 0.0
    if u < 0.36:
        return -0.28 * math.sin((u - 0.30) / 0.06 * math.pi)
    if u < 0.42:
        return 1.0 * math.sin((u - 0.36) / 0.06 * math.pi)
    if u < 0.48:
        return -0.35 * math.sin((u - 0.42) / 0.06 * math.pi)
    if u < 0.70:
        return 0.0
    if u < 0.90:
        return 0.22 * math.sin((u - 0.70) / 0.20 * math.pi)
    return 0.0


def curve(cv, fn, x0, x1, fg, ch_up="╱", ch_dn="╲", ch_flat="─", ch_fill="│"):
    """Plot y=fn(x) as a connected line of box characters."""
    prev = None
    for x in range(x0, x1 + 1):
        y = int(round(fn(x)))
        if prev is None:
            cv.put(x, y, "·", fg)
            prev = y
            continue
        if y == prev:
            cv.put(x, y, ch_flat, fg)
        elif y > prev:
            cv.put(x, y, ch_dn, fg)
        else:
            cv.put(x, y, ch_up, fg)
        if abs(y - prev) > 1:
            step = 1 if y > prev else -1
            for yy in range(prev + step, y, step):
                cv.put(x, yy, ch_fill, fg)
        prev = y


def filled_wave(cv, cy, amp, freq, phase, fg, fill_fg, x0=0, x1=None):
    """Waveform as a filled band around the axis (reads well in a terminal)."""
    x1 = cv.w - 1 if x1 is None else x1
    for x in range(x0, x1 + 1):
        y = int(round(cy + amp * math.sin(freq * x + phase)))
        lo, hi = (cy, y) if y >= cy else (y, cy)
        for yy in range(lo, hi + 1):
            cv.put(x, yy, "░", fill_fg)
        cv.put(x, y, "▄" if y > cy else "▀", fg)
