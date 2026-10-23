"""Scenes: verse 3, pre-chorus 2, chorus 2, bridge, build, chant,
final chorus, outro, shutdown, end card."""

import math

import art
import anim
import fx
from base import Scene, stamp, fade_window, ramp, cue, glow_text
from renderer import mix, shade, grey, P, h01, sw, cw


def draw_banner(cv, text, y, fg, scale=1, gap=1, cx=None):
    lines_ = art.banner_lines(text, scale, gap)
    wpx = art.banner_width(text, scale, gap)
    x = (cv.w - wpx) // 2 if cx is None else cx - wpx // 2
    for j, ln in enumerate(lines_):
        cv.text(x, y + j, ln, fg)
    return y + len(lines_)


def banner_fit(text, w, gap=1, rows=None):
    s = 1
    while s < 4 and art.banner_width(text, s + 1, gap) <= w - 2:
        s += 1
    if rows:
        while s > 1 and len(art.banner_lines(text, s, gap)) > rows:
            s -= 1
    return s


# ==========================================================================
# 5 · VERSE 3 — I can be anything
# ==========================================================================

# --------------------------------------------------------------------------
# small helpers for the rebuilt beats (pure functions of t, chrome-safe rows)
# --------------------------------------------------------------------------

def _rows(cv):
    """The rows the chrome does not own: 4 .. h-3."""
    return 4, max(4, cv.h - 3)


def _fit(s, maxw):
    """Trim a string to a display width (wide chars count 2)."""
    out, n = "", 0
    for ch in s:
        wd = 2 if cw(ch) == 2 else 1
        if n + wd > maxw:
            break
        out += ch
        n += wd
    return out


def _dust(cv, t, fg, n=40, seed=0, speed=1.0):
    """Drifting phosphor dust, kept inside the content rows."""
    top, bot = _rows(cv)
    span = max(1, bot - top)
    for i in range(n):
        sp = (0.6 + 2.2 * h01(i, seed + 1)) * speed
        x = int((h01(i, seed) * cv.w + t * sp) % cv.w)
        y = top + int((h01(i, seed + 2) * span
                       + t * (0.35 + 1.4 * h01(i, seed + 3))) % span)
        cv.put(x, min(bot, y), "·" if h01(i, seed + 4) < 0.75 else "+",
               shade(fg, 0.14 + 0.40 * h01(i, int(t * 3), seed + 5)))


def _rain(cv, t, fg, step=7, seed=0, dens=3):
    """Falling hex telemetry: a background that never sits still."""
    top, bot = _rows(cv)
    span = max(1, bot - top)
    hexd = "0123456789ABCDEF"
    for i in range(max(3, cv.w // step)):
        x = int(h01(i, seed + 11) * cv.w)
        spd = 2.0 + 4.5 * h01(i, seed + 12)
        for j in range(dens):
            y = top + int((h01(i, seed + 13) * span
                           + t * spd + j * span / 3.0) % span)
            if cv.ch[y][x] == " ":
                cv.put(x, y, hexd[int(h01(x, y, int(t * 4), seed) * 16)],
                       shade(fg, 0.13 + 0.20 * j))


def _wave(cv, y, t, fg, amp=2, freq=0.22, speed=4.4, ch="·", floor=4,
          x0=0, x1=None):
    """One full-width oscillating trace: every dot moves each frame."""
    top, bot = _rows(cv)
    for x in range(x0, cv.w if x1 is None else x1):
        yy = y + int(round(amp * math.sin(x * freq + t * speed)))
        cv.put(x, max(top, min(bot, yy)), ch,
               shade(fg, 0.22 + 0.40 * h01(x, int(t * 5))))


# ==========================================================================
# 5 · VERSE 3 — I can be anything
# ==========================================================================

# ONE object that keeps becoming the next one.  The four forms share a 21-cell
# box and a common centre line, so the stage-by-stage cell dissolve reads as
# the same "me" changing species -- not as two posters cross-fading.
V3_BOX = 21

V3_FORMS = {
    "egg": ((8, "▄▄▄"), (7, "████"), (6, "▀████▀"),
            (4, "▄██████▄"), (3, "██████████"),
            (2, "████████████"), (2, "████████████"),
            (3, "██████████"), (4, "▀▀▀▀▀▀▀▀")),
    "tom": ((8, "▄▄▄"), (7, "╲███╱"), (5, "▄███████▄"),
            (3, "█████████████"), (2, "██████████████"),
            (3, "█████████████"), (4, "▀█████████▀"),
            (6, "▀█████▀"), (8, "▀▀")),
    "cat": ((1, "╱╲             ╱╲"),
            (0, "╱  ╲▄▄▄▄▄▄▄▄▄▄╱  ╲"),
            (1, "▐      ●   ●      ▌"),
            (1, "▐        ▲        ▌"),
            (1, "▐    ╲▁▁▁▁▁▁╱    ▌"),
            (0, "╲▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄╱"),
            (2, "▐▌  ╱╲  ╱╲  ▐▌"),
            (6, "╲╱  ╲╱")),
    "god": ((3, "✦   ▄▄▄▄▄▄▄   ✦"),
            (4, "▄█████████▄"),
            (2, "▄███ ◉   ◉ ███▄"),
            (2, "███    ▄▄▄    ███"),
            (2, "▀█████████████▀"),
            (3, "╱▐█████████▌╲"),
            (2, "╱  █████████  ╲"),
            (1, "╱   ██     ██   ╲"),
            (6, "▀▀     ▀▀")),
}

V3_PAIRS = (("eggplant", "nutrients"), ("tomato", "antioxidants"),
            ("tabby cat", "purr"), ("only god", "proof"))


def _v3_rows(form, space=9):
    """Sprite rows, sub-sampled when the terminal is short."""
    src = V3_FORMS[form]
    if space >= len(src):
        pick = tuple(range(len(src)))
    elif space >= 5:
        pick = (0, 2, 4, 6, 8)
    elif space >= 3:
        pick = (0, 4, 8)
    else:
        pick = (4,)
    out = []
    seen = set()
    for j in pick:
        j = min(j, len(src) - 1)
        if j in seen:
            continue
        seen.add(j)
        off, s = src[j]
        off = max(0, min(V3_BOX - len(s), off))
        out.append(" " * off + s + " " * (V3_BOX - off - len(s)))
    return out


def _v3_colf(form, t):
    """Per-cell colour of a form; alive because the palette breathes."""
    pulse = 0.84 + 0.16 * math.sin(t * 2.3)

    if form == "egg":
        def f(ch, i, j):
            if j <= 2:
                return shade(mix(P["phos_dim"], P["violet"], 0.45), pulse)
            return shade(mix(P["violet"], P["magenta"], 0.16 + 0.06 * j), pulse)
        return f
    if form == "tom":
        def f(ch, i, j):
            if j <= 1:
                return shade(mix(P["phos_dim"], P["amber"], 0.40), pulse)
            return shade(mix(P["red"], P["rose"], 0.28 + 0.05 * j), pulse)
        return f
    if form == "cat":
        def f(ch, i, j):
            if ch in "●▲":
                return P["white"]
            if ch == "▁":
                return shade(P["rose"], 0.85)
            return shade(mix(P["amber"], P["gold"], 0.18 + 0.06 * j), pulse)
        return f

    def f(ch, i, j):
        if ch == "◉":
            return P["ice"]
        if ch == "▄" and j == 3:
            return shade(P["amber"], 0.65)
        return shade(mix(P["gold"], P["white"], 0.30 if j == 0 else 0.0), pulse)
    return f


def _v3_spr(cv, rows, cx, cy, colf, bg=None):
    if not rows:
        return
    box = len(rows[0])
    x0 = cx - box // 2
    for j, ln in enumerate(rows):
        for i, ch in enumerate(ln):
            if ch == " ":
                continue
            c = colf(ch, i, j) if callable(colf) else colf
            if c is not None:
                cv.put(x0 + i, cy + j, ch, c, bg)


# --------------------------------------------------------------------------
#  VERSE 3 · the conditional grant
#  "If I'm X, then I give you Y" — four times.  So the stage is an if/then
#  evaluator: the IF line names the form the machine becomes, the THEN line
#  hands something concrete to "you", and each gift travels by its own
#  mechanism (substance arcs out of my drained body, protection closes around
#  you, sound rings land on you, and at the only god the flow reverses: you
#  become the evidence of my existence).
# --------------------------------------------------------------------------

V3_THEN = ('grant(you) := nutrients',
           'grant(you) := antioxidants',
           'grant(you) := purr · enjoyment',
           'proof(me) := you')            # the one branch that runs backwards

V3_READ = ('drained %4d u  →  you',
           'shield 100%%   blocked %2d',
           'purr %.1f Hz   enjoy +%d',
           'existence %.2f   witness = you')

V3_STAT = ('fed %d u', 'shielded', 'enjoy +%d', 'WITNESS')


def _v3_header(cv, t, w, idx, sy, top, cues_if, cues_then):
    """IF / THEN, typed above the object like a label on a stage."""
    hy = sy - 2
    x0 = 33 if w >= 78 else 4
    maxw = w - x0 - 3
    if hy < top or maxw < 20:
        return
    a_if = cues_if[idx] - 0.30
    s_if, ty = fx.typewriter('IF   me := "%s"' % V3_PAIRS[idx][0],
                             t - a_if, 30.0)
    cv.text(x0, hy, s_if[:maxw], shade(P["ice"], 0.80))
    if ty and int(t * 12) % 2 == 0:
        cv.put(min(w - 3, x0 + sw(s_if)), hy, "▮", shade(P["ice"], 0.7))
    a_th = cues_then[idx] - 0.25
    if t >= a_th:
        s_th, ty2 = fx.typewriter("THEN " + V3_THEN[idx], t - a_th, 32.0)
        col = P["gold"] if idx == 3 else P["phos"]
        cv.text(x0, hy + 1, s_th[:maxw], shade(col, 0.78))
        if ty2 and int(t * 12) % 2 == 0:
            cv.put(min(w - 3, x0 + sw(s_th)), hy + 1, "▮", shade(col, 0.7))


def _v3_conveyor(cv, t, cx, cy, youx, idx, space):
    """The bus between me and you; on the last branch it runs backwards."""
    if space < 9:
        return
    x0, x1 = cx + 12, youx - 5
    if x1 <= x0 + 4:
        return
    back = (idx == 3)
    for x in range(x0, x1):
        cv.put(x, cy, "·", shade(P["gold"] if back else P["violet"], 0.24))
    for p in range(6):
        u = (t * 2.0 + p / 6.0) % 1.0
        if back:
            u = 1.0 - u
        xp = int(x0 + (x1 - x0) * u)
        col = P["gold"] if back else P["ice"]
        cv.put(xp, cy, "◈" if back else "●", shade(col, 0.85 - 0.35 * u))
        cv.put(xp - 1, cy, "·", shade(col, 0.35))


def _v3_gift_egg(cv, t, cx, sy, spr_space, youx, dy_, top, bot, t_nut):
    """nutrients: my body is drained and the mass arcs into you."""
    age = t - t_nut
    if age < -0.25:
        return 0
    for i in range(12):
        u = (age * 0.55 + i / 12.0) % 1.0
        x0 = cx + (i % 4 - 2) * 2
        y0 = sy + spr_space - 1
        xp = int(x0 + (youx - 4 - x0) * (u ** 0.8))
        yp = int(y0 + (dy_ - y0) * u - math.sin(u * math.pi) * 2.0)
        if top <= yp <= bot:
            cv.put(xp, yp, "·" if i % 2 else "∘",
                   shade(P["violet"], 0.75 - 0.5 * u))
    dr = ramp(t, t_nut - 0.15, t_nut + 1.7)
    return int(round(dr * (spr_space * 0.5)))


def _v3_gift_tom(cv, t, youx, dy_, top, bot, t_ant, space):
    """antioxidants: a shell closes around you and radicals die on it."""
    kk = ramp(t, t_ant - 0.15, t_ant + 0.8)
    if kk <= 0.01:
        return
    rx = 7 if space >= 9 else 5
    for ring in (rx, rx + 3):
        n = 30 if ring == rx else 24
        for i in range(n):
            a = (-t * 0.65 if ring == rx else t * 0.42) + i * (2 * math.pi / n)
            xp = youx + int(round(math.cos(a) * ring))
            yp = dy_ + int(round(math.sin(a) * (ring * 0.55)))
            if top <= yp <= bot:
                tw = 0.55 + 0.45 * math.sin(t * 2.4 + i + ring)
                cv.put(xp, yp, "○" if i % 2 == 0 else "·",
                       shade(P["ice"], kk * (0.9 if ring == rx else 0.5) * tw))
    for i in range(7):
        u = (t * 0.75 + h01(i, 33)) % 1.0
        a = h01(i, 34) * 6.283
        d = 15.0 - u * 8.0
        xp = youx + int(round(math.cos(a) * d))
        yp = dy_ + int(round(math.sin(a) * d * 0.55))
        if top <= yp <= bot:
            ch = "✳" if u < 0.70 else ("+" if u < 0.88 else "·")
            cv.put(xp, yp, ch, shade(mix(P["red"], P["amber"], 0.35),
                                     0.55 + 0.45 * (1.0 - u)))


def _v3_gift_cat(cv, t, w, cx, cy, youx, top, bot, t_purr, space):
    """purr: the sound leaves my chest as rings and lands on you."""
    age = t - t_purr
    if age < -0.25:
        return
    far = max(8, youx - (cx + 4))
    for r_ in range(3):
        ph = ((age * 1.05 + r_ * 0.55) % 1.75) / 1.75
        rr = 4 + ph * far
        n = max(10, int(rr * 2.2))
        for i in range(n):
            a = -1.15 + 2.3 * i / n
            xp = cx + int(4 + rr * math.cos(a) * 0.9)
            yp = cy + int(round(rr * 0.28 * math.sin(a)))
            if top <= yp <= bot:
                cv.put(xp, yp, "~", shade(P["amber"], (1.0 - ph) * 0.85))
    if space >= 9:
        s_ = "p u r r r r"
        span_ = max(4, (youx - cx) - sw(s_))
        xp = cx - sw(s_) // 2 + int((age * 8.0) % span_)
        yp = min(bot, cy + 5)
        if xp + sw(s_) < w - 1:
            cv.text(xp, yp, s_, mix(P["amber"], P["white"],
                                    0.30 + 0.35 * math.sin(t * 7.0)))


def _v3_gift_god(cv, t, cx, cy, youx, dy_, top, bot, t_god, t_proof, space):
    """proof: god gives nothing — you are the evidence, so the beam runs back."""
    if t >= t_god - 0.3:
        kk = ramp(t, t_god - 0.3, t_god + 0.6)
        for i in range(26):
            a = math.pi + i * math.pi / 25.0
            xp = cx + int(round(math.cos(a) * 13))
            yp = cy - 3 + int(round(math.sin(a) * 9))
            if top <= yp <= bot:
                cv.put(xp, yp, "✦" if i % 4 == 0 else "·",
                       shade(P["gold"], (0.3 + 0.6 * kk)
                             * (0.55 + 0.45 * math.sin(t * 3 + i))))
    if t >= t_proof - 0.35:
        kp = ramp(t, t_proof - 0.35, t_proof + 0.5)
        n = max(6, youx - (cx + 12))
        for i in range(n):
            u = i / float(n)
            xp = cx + 12 + i
            yp = int(round(cy + (dy_ - cy) * u))
            cv.put(xp, yp, "·",
                   shade(P["gold"], 0.15 + 0.7 * kp * (1 - abs(u - 0.5))))
        for i in range(4):
            u = ((t - t_proof) * 1.1 + i / 4.0) % 1.0
            xp = int(cx + 12 + u * (n - 1))
            yp = int(round(cy + (dy_ - cy) * u))
            cv.put(xp, yp, "◆", shade(P["ice"], 0.9 - 0.4 * u))
        if space >= 7 and dy_ + 5 <= bot:
            cv.text(youx - 3, dy_ + 5, "PROOF", shade(P["gold"], 0.8))


class Verse3Scene(Scene):
    key = "verse3"
    accent = "magenta"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_egg = cue("If I'm an eggplant")
        t_nut = cue("Then I will give you my nutrients")
        t_tom = cue("If I'm a tomato")
        t_ant = cue("Then I'll give you antioxidants")
        t_cat = cue("If I'm a tabby cat")
        t_purr = cue("Then I will purr for your enjoyment")
        t_god = cue("If I'm the only god")
        t_proof = cue("Then you're the proof of my existence")

        def beat(c):
            _verse3(c, t, w, h, self, (t_egg, t_nut, t_tom, t_ant,
                                      t_cat, t_purr, t_god, t_proof))

        # the picture stays up to the very last frame: mv eats this scene away
        # cell by cell at the boundary, so the beat must NOT fade itself out
        beat(cv)


def _verse3(cv, t, w, h, sc, cues):
    t_egg, t_nut, t_tom, t_ant, t_cat, t_purr, t_god, t_proof = cues
    top, bot = _rows(cv)
    full = h >= 24 and w >= 90
    mid = (not full) and h >= 19 and w >= 72
    comp = (not full) and (not mid) and h >= 15 and w >= 54
    space = bot - top + 1

    # how much proof of existence has arrived so far (0 -> 1)
    ex_val = max(0.0, min(1.0, ramp(t, t_proof - 0.4, t_proof + 0.7)))

    cues_if = (t_egg, t_tom, t_cat, t_god)
    cues_then = (t_nut, t_ant, t_purr, t_proof)
    forms = ("egg", "tom", "cat", "god")

    # ---- which form now, and how far the morph has travelled ---------------
    idx = 0
    for i, tc in enumerate(cues_if):
        if t >= tc:
            idx = i

    # panel decides where the stage sits
    if full:
        px_, py_, pw_, ph_ = 2, 5, 30, 13
    elif mid:
        px_, py_, pw_, ph_ = 2, 4, 28, 11
    elif comp:
        px_, py_, pw_, ph_ = 2, 4, 26, 7
    else:
        px_, pw_ = 0, 0
    tiny = not (full or mid or comp)
    stage0 = (px_ + pw_ + 4) if pw_ else 2
    youx = w - max(5, w // 12)
    cx = (stage0 + youx - 8) // 2
    if tiny:
        cx = max(10, w // 3)
        youx = w - 5
        cy = top + 1 + max(0, space - 2) // 2
    else:
        cy = top + (bot - top) // 2 - 1
        if cy < top + 4:
            cy = top + 4

    # ---- where the object stands: the stage's centre line -----------------
    spr_space = min(9, max(1, space - (2 if tiny else 1)))
    bob = int(round(math.sin(t * 2.1) * (0.9 if spr_space >= 7 else 0.0)))
    sy = cy - (spr_space // 2) + bob
    sy = max(top, min(bot - spr_space + 1, sy))

    # ---- the machine keeps breathing behind everything --------------------
    _dust(cv, t, P["violet"], n=max(20, w // 2), seed=5)
    _rain(cv, t, P["violet"], step=(7 if w < 70 else 6), seed=3,
          dens=(3 if space < 9 else 4))
    if full and space >= 20:
        _wave(cv, 4, t, shade(P["violet"], 0.55), amp=1,
              freq=0.38, speed=5.6, ch="·", floor=top)

    # ---- the chassis: two telemetry columns, always ticking ---------------
    if space >= 9 and w >= 56:
        for j in range(top, bot + 1):
            v = int(h01(j, int(t * 14), 61) * 16)
            cv.put(w - 2, j, "%X" % v,
                   shade(P["violet"], 0.26 + 0.20 * (j % 3 == 0)))
            v2 = int(h01(j, int(t * 11), 62) * 16)
            cv.put(1, j, "%X" % v2, shade(P["violet"], 0.22))

    # ---- what has been handed over so far ---------------------------------
    gifts = 0.0
    for i in range(4):
        a = cues_then[i]
        b = (cues_if[i + 1] - 0.12) if i < 3 else sc.t1
        if t >= b:
            gifts += 1.0
        elif t > a:
            gifts += (t - a) / max(0.15, b - a)
    transferred = 0
    for i in range(4):
        a = cues_then[i]
        b = (cues_if[i + 1] - 0.12) if i < 3 else sc.t1
        span = max(0.15, b - a)
        transferred += int(min(1.0, max(0.0, (t - a) / span)) * 512)

    # ---- the instrument panel ---------------------------------------------
    if pw_:
        bgp = mix(P["black"], P["violet"], 0.055)
        ph_ = min(ph_, bot - py_ + 1)
        fx.panel(cv, px_, py_, pw_, ph_, shade(P["violet"], 0.80), bgp,
                 " grant.table ", shade(P["ice"], 0.95))
        inner = pw_ - 4
        rows = []
        for i in range(4):
            done = t >= cues_then[i]
            arr = "←" if i == 3 else "→"
            rows.append(_fit("%d %s %s %s%s" % (i + 1, V3_PAIRS[i][0], arr,
                                                V3_PAIRS[i][1],
                                                " ✓" if done else ""), inner))
        anim.ladder(cv, px_ + 2, py_ + 2, rows, idx,
                    shade(P["phos"], 1.0), shade(P["soft"], 0.52), bg=bgp)
        # ledger of raw machine numbers: always scrolling
        if ph_ >= 12:
            anim.meter(cv, px_ + 2, py_ + 7, "gift", gifts, 4.0,
                       max(5, min(9, inner - 14)),
                       shade(P["violet"], 0.95), bg=bgp,
                       dim_fg=shade(P["grey"], 0.45))
            anim.counter(cv, px_ + 2, py_ + 8, "transferred",
                         transferred, "%5d u", shade(P["ice"], 0.9), bg=bgp)
            for r_ in range(3):
                kv = int(t * 12) + r_ * 5
                s_ = _fit("0x%04X 0x%04X 0x%04X" % (
                    int(h01(kv, 1) * 65535), int(h01(kv, 2) * 65535),
                    int(h01(kv, 3) * 65535)), inner)
                cv.text(px_ + 2, py_ + 9 + r_, s_,
                        shade(P["violet"], 0.42), bgp)
            # a scanning read-head runs down the table
            sel = py_ + 2 + int(t * 2.4) % 4
            cv.text(px_, sel, "▌", shade(P["amber"], 0.85), bgp)
            # hazard stripe: the bus between me and you never stops
            for i in range(inner):
                cv.put(px_ + 2 + i, py_ + 6,
                       "▚" if (i + int(t * 12)) % 2 else "▞",
                       shade(P["violet"], 0.45), bgp)
        elif ph_ >= 9:
            for r_ in range(2):
                kv = int(t * 12) + r_ * 5
                s_ = _fit("0x%04X 0x%04X 0x%04X" % (
                    int(h01(kv, 1) * 65535), int(h01(kv, 2) * 65535),
                    int(h01(kv, 3) * 65535)), inner)
                cv.text(px_ + 2, py_ + 7 + r_, s_,
                        shade(P["violet"], 0.42), bgp)
            anim.meter(cv, px_ + 2, py_ + 6, "gift", gifts, 4.0,
                       max(4, inner - 14), shade(P["violet"], 0.95), bg=bgp,
                       dim_fg=shade(P["grey"], 0.45))
        else:
            anim.meter(cv, px_ + 2, py_ + ph_ - 2, "gift", gifts, 4.0,
                       max(4, inner - 14), shade(P["violet"], 0.95), bg=bgp,
                       dim_fg=shade(P["grey"], 0.45))
    else:
        # tiny / narrow: the ladder collapses to one line of pips
        pips = "".join("●" if i <= idx else "○" for i in range(4))
        cv.text(2, top, _fit("%s %s→%s" % (pips, V3_PAIRS[idx][0],
                                          V3_PAIRS[idx][1]), w - 3),
                shade(P["phos"], 0.9))

    # ---- the you-diamond: the witness on the right ------------------------
    you_bright = 0.72 + 0.22 * math.sin(t * 2.6)
    if idx == 3:
        you_bright = 0.80 + 0.20 * math.sin(t * 4.2)
    dy_ = cy + (2 if space < 9 else -1)
    if space >= 7:
        dy_ = max(top + 2, min(bot - 2, dy_))
    else:
        dy_ = max(top, min(bot, dy_))
    # the purr actually lands on you: the diamond rides the sound
    if idx == 2 and space >= 7:
        dy_ += int(round(math.sin(t * 6.4)))
        dy_ = max(top + 1, min(bot - 1, dy_))
    if space >= 7:
        for j, ln in enumerate(art.YOU["diamond"]):
            cv.text(youx - 2, dy_ - 2 + j, ln, shade(P["pink"], you_bright))
    else:
        cv.put(youx, dy_, "◆", shade(P["pink"], you_bright))
    if w >= 54 and dy_ + 3 <= bot:
        cv.text(youx - 1, dy_ + 3, '"you"', shade(P["pink"], 0.75))
    if w >= 54 and dy_ + 4 <= bot:
        st = V3_STAT[idx]
        if idx == 0:
            st = st % transferred
        elif idx == 2:
            st = st % int(abs(math.sin(t * 3.1)) * 99 + 1)
        cv.text(youx - 4, dy_ + 4, st,
                shade(P["gold"] if idx == 3 else P["pink"], 0.62))
    fx.sparkle(cv, youx, dy_, t, P["pink"], seed=int(t * 5), n=4,
               rad=max(1, min(space // 3, cy - top, bot - cy)))

    # ---- the conveyor: what me gives travels to you (or back) -------------
    _v3_conveyor(cv, t, cx, cy, youx, idx, space)

    # ---- each form hands over its own kind of gift -----------------------
    gi = None
    for i in range(4):
        if t >= cues_then[i] and (i == 3 or t < cues_if[i + 1] - 0.12):
            gi = i
    egg_cut = 0
    if not tiny and gi is not None:
        if gi == 0:
            egg_cut = _v3_gift_egg(cv, t, cx, sy, spr_space, youx, dy_,
                                   top, bot, t_nut)
        elif gi == 1:
            _v3_gift_tom(cv, t, youx, dy_, top, bot, t_ant, space)
        elif gi == 2:
            _v3_gift_cat(cv, t, w, cx, cy, youx, top, bot, t_purr, space)
        else:
            _v3_gift_god(cv, t, cx, cy, youx, dy_, top, bot, t_god, t_proof,
                         space)
        if 0.0 <= t - cues_then[gi] < 1.0:
            fx.ripple(cv, cx, cy, t - cues_then[gi] + 0.2, P["violet"],
                      n=3, speed=14.0, period=1.2, ch="·")

    # ---- the sprite: build, then morph, then morph again -----------------
    cv.fill(cx - V3_BOX // 2, sy, V3_BOX, spr_space, " ", None, None)
    kb = ramp(t, sc.t0 - 0.10, sc.t0 + 0.80)
    if idx == 0 and kb < 1.0:
        # I assemble out of the noise of the last scene
        anim.assemble(cv, cx - V3_BOX // 2, sy, _v3_rows("egg", spr_space),
                      kb, shade(P["violet"], 0.95), seed=5,
                      spread=(9 if sy - top >= 7 else 3), snap=0.4,
                      y_min=top)
    else:
        prev = forms[idx - 1] if idx > 0 else forms[0]
        a0 = cues_if[idx] - 0.12
        k = ramp(t, a0, a0 + 0.62)
        cur = forms[idx]

        def paint_sprite(c2):
            if k <= 0.0:
                _v3_spr(c2, _v3_rows(prev, spr_space), cx, sy, _v3_colf(prev, t))
            elif k >= 1.0:
                _v3_spr(c2, _v3_rows(cur, spr_space), cx, sy, _v3_colf(cur, t))
            else:
                anim.dissolve(c2, t, a0, a0 + 0.62,
                              lambda c, f=prev: _v3_spr(
                                  c, _v3_rows(f, spr_space), cx, sy,
                                  _v3_colf(f, t)),
                              lambda c, f=cur: _v3_spr(
                                  c, _v3_rows(f, spr_space), cx, sy,
                                  _v3_colf(f, t)),
                              seed=31 + idx, band=0.18,
                              scram_fg=shade(P["white"], 0.9))

        if t < sc.t1 - 0.95:
            paint_sprite(cv)
            if gi == 0 and egg_cut > 0:
                yl = sy + spr_space - egg_cut
                cv.fill(cx - V3_BOX // 2, yl, V3_BOX, egg_cut, " ", None, None)
                for i in range(V3_BOX):
                    cv.put(cx - V3_BOX // 2 + i, yl, "▁",
                           shade(P["magenta"], 0.8))
            # a read-head sweeps the object; cells under it scramble for a beat
            srow = sy + int((t * 6.0) % (spr_space + 4)) - 2
            for j in range(spr_space):
                y = sy + j
                if 0 <= y < cv.h:
                    if y == srow:
                        for i in range(V3_BOX):
                            x = cx - V3_BOX // 2 + i
                            if 0 <= x < w and cv.ch[y][x] != " ":
                                cv.put(x, y, "▒", shade(P["white"], 0.9))
                    elif abs(y - srow) == 1:
                        for i in range(V3_BOX):
                            x = cx - V3_BOX // 2 + i
                            if 0 <= x < w and cv.fg[y][x] is not None:
                                cv.fg[y][x] = mix(cv.fg[y][x], P["white"], 0.5)
        else:
            # the object does not disappear, it is taken apart cell by cell
            anim.hand_off(cv, t, sc.t1 - 0.95, sc.t1 - 0.10, paint_sprite,
                          seed=43)
    if space >= 9:
        _wave(cv, bot - 2, t, P["violet"], amp=(1 if space < 12 else 2),
              freq=0.20, speed=4.6, floor=top)

    # ---- IF / THEN, drawn last so no gift can smear the contract ---------
    if not tiny:
        _v3_header(cv, t, w, idx, sy, top, cues_if, cues_then)

    # ---- the contract, typed; the proof stamp ----------------------------
    if space >= 9 and w >= 60:
        cy_ = bot - 5
        age = t - (cues_if[idx] - 0.45)
        if cy_ > cy + 3:
            s1, typ1 = fx.typewriter(
                'if (me is %s) yield "%s";' % (V3_PAIRS[idx][0],
                                               V3_PAIRS[idx][1]),
                age, 34.0)
            cv.text(3, cy_, _fit(s1, w - 6), shade(P["ice"], 0.88))
            if typ1 and int(t * 12) % 2 == 0:
                cv.put(3 + sw(s1), cy_, "▮", shade(P["ice"], 0.7))
        if idx == 3 and t >= t_proof - 0.2:
            kp = ramp(t, t_proof - 0.2, t_proof + 0.5)
            s2 = "∎ QED   existence = %.1f   witness = you" % (ex_val,)
            cv.text(3, cy_ + 1, _fit(s2, w - 6),
                    mix(P["gold"], P["white"], 0.25 * kp))

    # ---- bottom instrument: a carrier wave + a scrolling gift log ---------
    if space >= 9:
        log = ("gift.log · " + " · ".join(
            "%s→%s%s" % (V3_PAIRS[i][0], V3_PAIRS[i][1],
                         "✓" if t >= cues_then[i] else "…")
            for i in range(4)) + " · transmitted %d units · you ← me"
            % transferred)
        anim.ticker(cv, bot, log, t, speed=18.0,
                    fg=shade(P["rose"], 0.62), x0=2, x1=w - 3)
        if full:
            hexs = " ".join("%04X" % int(h01(int(t * 10) + i, 77) * 65535)
                            for i in range(14))
            anim.ticker(cv, bot - 1, "bus." + hexs, t, speed=23.0,
                        fg=shade(P["violet"], 0.46), x0=2, x1=w - 3)
    if space >= 12 and w >= 74:
        n_ = int(t * 9) % 97
        if idx == 0:
            read = V3_READ[0] % transferred
        elif idx == 1:
            read = V3_READ[1] % n_
        elif idx == 2:
            read = V3_READ[2] % (5.5, n_)
        else:
            read = V3_READ[3] % ex_val
        s3 = _fit("state %02d/04  %s → %s   %s" % (idx + 1, V3_PAIRS[idx][0],
                                                   V3_PAIRS[idx][1], read),
                  w - 8)
        cv.put(2, bot - 3, "▸", shade(P["phos"], 0.95))
        cv.text(4, bot - 3, s3, shade(P["soft"], 0.75))

    fx.scanlines(cv, 0.88)
    fx.vignette(cv, 0.22)


# ==========================================================================
# 6 · PRE-CHORUS 2 — switch gender / time / role / trance
# ==========================================================================

class Pre2Scene(Scene):
    key = "pre2"
    accent = "violet"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_gender = cue("Switch my gender")
        t_fm = cue("To F to M")
        t_whatever = cue("And then do whatever")
        t_ampm = cue("From AM to PM")
        t_role = cue("Oh switch my role")
        t_sm = cue("To S to M")
        t_enter = cue("So we can enter")
        t_trance = cue("The trance the trance")
        cx, cy = w // 2, h // 2

        # ---------- gender switch: edit /etc/me.conf in place -------
        a = fade_window(t, t_gender - 0.2, t_whatever + 0.3, 0.4, 0.4)
        if a > 0.01:
            def gender(cv2):
                k = ramp(t, t_gender + 0.2, t_fm + 1.9)     # F -> M
                # once it has switched, it keeps switching: the machine can
                # never make up its mind, so the slider never comes to rest
                kp = k if k < 0.999 else 0.5 + 0.5 * math.sin(
                    (t - t_fm) * 1.7)
                pw = min(w - 4, 64)
                ph = min(h - 2, 13 if h >= 17 else 9)
                px = (w - pw) // 2
                py = max(1, (h - ph) // 2)
                fx.panel(cv2, px, py, pw, ph, shade(P["violet"], 0.9),
                         title=" /etc/me.conf ")
                # the command being retyped
                cmd = "$ me --set gender=F" if k < 0.45 else "$ me --set gender=M"
                cv2.text(px + 2, py + 2, cmd, shade(P["phos"], 0.9))
                # big F dissolves into big M, cell by cell
                fy0 = py + 4
                fw = 4
                fcols = [" ███", "█   ", "███ ", "█   ", "█   "]
                mcols = ["█   █", "██ ██", "█ █ █", "█   █", "█   █"]
                if fy0 + 5 <= py + ph:
                    for j in range(5):
                        row_f, row_m = fcols[j], mcols[j]
                        for i, ch in enumerate(row_f):
                            if ch == " ":
                                continue
                            aa = max(0.0, 1.0 - kp * 1.15)
                            if aa > 0.03 and h01(i, j, 77) < 0.35 + aa * 0.65:
                                cv2.put(px + 3 + i, fy0 + j, ch,
                                        shade(P["pink"], aa))
                        for i, ch in enumerate(row_m):
                            if ch == " ":
                                continue
                            bb = max(0.0, (kp - 0.12) * 1.15)
                            if bb > 0.03 and h01(i, j, 78) < 0.35 + bb * 0.65:
                                cv2.put(px + pw - 8 + i, fy0 + j, ch,
                                        shade(P["cyan"], bb))
                    # slider between the two letters
                    sx0, sx1 = px + 10, px + pw - 11
                    sy = fy0 + 2
                    if sx1 > sx0 + 4:
                        cv2.hline(sx0, sy, sx1 - sx0, "═", shade(P["grey"], 0.45))
                        kx = sx0 + int((sx1 - sx0) * min(1.0, max(0.0, kp)))
                        cv2.put(kx, sy, "●", mix(P["pink"], P["cyan"], kp))
                        cv2.put(kx, sy - 1, "▲", shade(P["white"], 0.8))
                        cv2.put(sx0, sy, "┤", shade(P["pink"], 0.7))
                        cv2.put(sx1, sy, "├", shade(P["cyan"], 0.7))
                if h >= 17:                    # room for the fine print
                    cy0 = py + 10
                    xx = min(px + pw - 8, px + 4)
                    cv2.text(px + 2, cy0, "chromosome", shade(P["grey"], 0.65))
                    cv2.text(px + 13, cy0, "XX", shade(P["pink"], 0.9 - 0.4 * k))
                    cv2.text(px + 16, cy0, "⇄", shade(P["grey"], 0.6))
                    cv2.put(px + 18, cy0, "X", shade(P["pink"], 0.8))
                    cv2.put(px + 19, cy0, "Y" if kp > 0.55 else "X",
                            shade(P["cyan"], 0.45 + 0.55 * kp))
                    sy2 = py + 11
                    syms = ["♀", "⚥", "♂"]
                    idx = int(t * 1.6) % 3
                    for i, sm in enumerate(syms):
                        c = P["white"] if i == idx else shade(P["violet"], 0.5)
                        cv2.text(px + 4 + i * 4, sy2, sm, c)
                    cv2.text(min(px + pw - 20, px + 18), sy2,
                             "gender: undefined", shade(P["violet"], 0.75))
                else:
                    cv2.text(px + 2, py + ph - 2, "gender ⇄ any",
                             shade(P["violet"], 0.75))
                cv2.text(px + pw - 12, py + 2,
                         "0x%02X" % int(0x46 + (0x4D - 0x46) * k),
                         shade(P["grey"], 0.7))
            stamp(cv, gender, a)

        # ---------- AM -> PM: a 24-hour band under the sky ----------
        a = fade_window(t, t_whatever - 0.3, t_role + 0.3, 0.4, 0.4)
        if a > 0.01:
            def ampm(cv2):
                k = ramp(t, t_ampm - 0.2, t_ampm + 2.4)
                small = h < 16
                by = min(h - 3, int(h * 0.66))          # the hour band
                top = 2 if small else 3
                hz = by - 2                             # horizon / arc base
                arcH = max(2, hz - top)
                bx0 = max(2, int(w * 0.09))
                bx1 = w - bx0
                if bx1 <= bx0 + 12:
                    return

                def band_x(hh):
                    return bx0 + int((bx1 - bx0) * (hh % 24) / 24.0)

                hour = 6.0 + 18.0 * k                   # 06:00 -> 24:00

                def sky_pos(hh):
                    x = band_x(hh)
                    if 6.0 <= hh <= 18.0:
                        u = (hh - 6.0) / 12.0
                    else:
                        u = ((hh - 18.0) % 24.0) / 12.0
                    return x, hz - int(round(math.sin(math.pi * u) * arcH))

                # ---- sky: stars come out for the night hours ----------
                night = 0.0 if hour < 18.0 else min(1.0, (hour - 18.0) / 4.0)
                ns = 10 if small else 26
                for i in range(ns):
                    if h01(i, 73) > 0.12 + 0.88 * night:
                        continue
                    sx = int(2 + h01(i, 71) * (w - 4))
                    sy = top + int(h01(i, 72) * max(1, hz - top))
                    tw = 0.3 + 0.7 * h01(i, int(t * 3.0))
                    cv2.put(sx, sy, "✦" if h01(i, 74) < 0.3 else "·",
                            shade(mix(P["ice"], P["white"], tw), 0.22 + 0.6 * tw))
                # ---- the day's trajectory ------------------------------
                for i in range(25):
                    px, py = sky_pos(6 + i * 0.5)
                    cv2.put(px, py, "·", shade(P["violet"], 0.16))
                # ---- sun / moon with a glow ----------------------------
                def body(hh, glyph, col, glow):
                    px, py = sky_pos(hh)
                    for d in range(1, 4):
                        for s2x, s2y in ((d, 0), (-d, 0), (0, d), (0, -d)):
                            cv2.put(px + s2x, py + s2y, "·", shade(glow, 0.30 / d))
                    cv2.put(px, py, glyph, col)
                    for d in range(1, 3):
                        cv2.put(px - d, py, "─", shade(col, 0.35))
                        cv2.put(px + d, py, "─", shade(col, 0.35))

                if hour < 18.0:
                    body(hour, "☼", mix(P["amber"], P["gold"],
                                        0.5 + 0.5 * math.sin(t * 2.2)), P["amber"])
                else:
                    body(hour, "☾", mix(P["ice"], P["white"], 0.45), P["ice"])

                # ---- the 24 hour band ---------------------------------
                cv2.hline(bx0, by, bx1 - bx0, "─", shade(P["soft"], 0.35))
                for hh in range(0, 24, 3):
                    tx = band_x(hh)
                    cv2.put(tx, by, "┼", shade(P["soft"], 0.5))
                    if hh % 6 == 0 or w >= 76:
                        cv2.text(tx - 1, by + 1, "%02d" % hh, shade(P["grey"], 0.6))
                cv2.put(bx1, by, "┤", shade(P["soft"], 0.5))
                cv2.text(bx1 - 1, by + 1, "24", shade(P["grey"], 0.6))
                # AM / PM halves, the one we are in lit up
                am_on = hour < 12.0
                cv2.text(bx0 - 1 if bx0 > 3 else 1, by - 1, "AM",
                         P["amber"] if am_on else shade(P["grey"], 0.45))
                cv2.text(min(w - 3, bx1 - 1), by - 1, "PM",
                         shade(P["grey"], 0.45) if am_on else P["ice"])
                # ---- where we are: cursor + time ----------------------
                cxp = band_x(hour)
                cv2.put(cxp, by, "▼", P["rose"])
                mins = int(360 + 1080 * k)
                ts = "%02d:%02d" % ((mins // 60) % 24, mins % 60)
                tx = min(w - 7, max(1, cxp - 2))
                if by + 2 <= h - 1:
                    cv2.text(tx, by + 2, ts, P["white"])
                if not small and by + 3 <= h - 1:
                    cv2.text(bx0 + 4, by + 3,
                             "06:00 sunrise↑ 12:00 noon 18:00 sunset↓",
                             shade(P["grey"], 0.55))
            stamp(cv, ampm, a)

        # ---------- S <-> M -----------------------------------------
        a = fade_window(t, t_role - 0.3, t_enter + 0.3, 0.4, 0.4)
        if a > 0.01:
            def roles(cv2):
                tilt = math.sin(t * 2.4) * 0.35
                L = int(w * 0.26)
                x0 = cx - L
                x1 = cx + L
                y0 = cy + int(math.sin(tilt) * L * 0.28)
                y1 = cy - int(math.sin(tilt) * L * 0.28)
                fx.line(cv2, x0, y0, x1, y1, shade(P["soft"], 0.8))
                # pivot
                cv2.put(cx, int((y0 + y1) / 2) + 1, "▲", P["violet"])
                sc = 1
                up = 0.5 + 0.5 * math.sin(t * 2.4)
                draw_banner(cv2, "S", y0 - 6, mix(P["violet"], P["white"], up), sc,
                            cx=x0)
                draw_banner(cv2, "M", y1 - 6, mix(P["rose"], P["white"], 1 - up), sc,
                            cx=x1)
                # little riders
                cv2.put(x0, y0 - 1, "◆", P["phos"])
                cv2.put(x1, y1 - 1, "◆", P["pink"])
                cv2.ctext(cy + 7, "S ⇄ M   master ⇄ servant", shade(P["violet"], 0.9))
            stamp(cv, roles, a)

        # ---------- trance ------------------------------------------
        a = fade_window(t, t_enter - 0.2, self.t1 + 0.3, 0.4, 0.3)
        if a > 0.01:
            def trance(cv2):
                spin = t * 1.8
                for i in range(70):
                    ang = spin + i * 0.31
                    rr = 1.1 * i ** 0.86
                    x = cx + int(math.cos(ang) * rr * 1.9)
                    y = cy + int(math.sin(ang) * rr / 1.6)
                    c = mix(P["violet"], P["pink"], (i % 9) / 9.0)
                    cv2.put(x, y, "·×*∘"[i % 4], shade(c, 0.55))
                for d in range(4):
                    fx.circle(cv2, cx, cy, 6 + d * 5, shade(P["violet"], 0.25),
                              "·", ry=(6 + d * 5) / 2)
                pulse = 0.5 + 0.5 * math.sin(t * 4.0)
                cv2.put(cx, cy, "◉", mix(P["violet"], P["white"], pulse))
                if t >= t_trance:
                    cv2.ctext(cy + 9, "the trance", P["pink"])
            stamp(cv, trance, a)
            fx.row_wave(cv, t * 0.7, amp=1.6 * a, freq=0.4, speed=2.4)

        anim.scanline(cv, t, 4, h - 2, P["white"], speed=16.0, band=3,
                      seed=21)
        fx.scanlines(cv, 0.82)
        fx.vignette(cv, 0.3)


# ==========================================================================
# 7 · CHORUS 2 — vibrations / completion / abandonment
# ==========================================================================

C2_WHOLE = [
    "  ▄██▄  ▄██▄  ",
    " ████████████ ",
    "██████████████",
    "██████████████",
    "██████████████",
    " ████████████ ",
    "  ██████████  ",
    "   ████████   ",
    "    ██████    ",
]
C2_L = [r[:8] for r in C2_WHOLE]
C2_R = [r[8:] for r in C2_WHOLE]
C2_BANDS = ((0, 1), (2, 3), (4, 5), (6, 7), (8,))


def _c2_pick(space):
    """which of the nine heart rows survive on a short screen"""
    if space >= 17:
        return list(range(9))
    if space >= 11:
        return [0, 2, 4, 6, 8]
    if space >= 8:
        return [0, 4, 8]
    return [4]


def _c2_band(j):
    return 4 if j == 8 else j // 2


class Chorus2Scene(Scene):
    key = "chorus2"
    accent = "rose"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_vib = cue("If I can feel your vibrations")
        t_comp = cue("Then I can finally be completion")
        t_left1 = cue("Though you have left")
        t_lefts = tuple(cue("You have left", i) for i in range(4))
        t_iso = cue("You have left me in isolation")
        _chorus2(cv, t, w, h, self,
                 (t_vib, t_comp, t_left1, t_lefts, t_iso))


def _chorus2(cv, t, w, h, sc, cues):
    top, bot = _rows(cv)
    space = bot - top + 1
    full = h >= 24 and w >= 90
    mid = h >= 19 and w >= 72
    comp = h >= 15 and w >= 54
    tiny = not (full or mid or comp)
    t_vib, t_comp, t_left1, t_lefts, t_iso = cues
    cues_all = (t_left1,) + tuple(t_lefts)
    cx = w // 2
    cy = top + (bot - top) // 2 - 1
    if tiny:
        cy = top + 1 + max(0, space - 2) // 2

    if full:
        px_, py_, pw_, ph_ = 2, top + 1, 30, 13
    elif mid:
        px_, py_, pw_, ph_ = 2, top, 28, 11
    elif comp:
        px_, py_, pw_, ph_ = 2, top, 26, 7
    else:
        px_, py_, pw_, ph_ = 0, 0, 0, 0
    inner = pw_ - 4
    bgp = mix(P["black"], P["rose"], 0.05)

    # ---- how much of me is still here -------------------------------------
    taken = 0
    for c in cues_all:
        if t >= c + 0.16:
            taken += 1
    kband = 0.0
    if taken < 5:
        kband = ramp(t, cues_all[taken] + 0.16, cues_all[taken] + 0.62)
    sync = 0.0 if t >= t_iso else (0.10 + 0.90 * ramp(t, t_vib, t_comp))
    if t < t_left1:
        complete = 100.0 * ramp(t, t_vib, t_comp)
    else:
        complete = max(0.0, 100.0 - 20.0 * (taken + kband))

    # ---- the field: dust, hex rain, a seismograph along the top -----------
    _dust(cv, t, P["rose"], n=max(24, int(w * 0.62)), seed=17)
    _rain(cv, t, P["rose"], step=(6 if w < 70 else 5), seed=19,
          dens=(3 if space < 9 else 5))
    if space >= 12 and w >= 70:
        x0s = (px_ + pw_ + 2) if pw_ else 2
        for x in range(x0s, w - 1):
            v = (math.sin(x * 0.16 + t * 5.2) +
                 0.5 * math.sin(x * 0.37 - t * 3.1))
            yy = top + int(round(v))
            cv.put(x, max(top, min(top + 2, yy)), "·", shade(P["rose"], 0.26))

    # ---- the two halves: build, approach, shake, snap ---------------------
    kapp = ramp(t, sc.t0 + 0.25, t_vib + 2.5)
    ks = ramp(t, t_vib + 2.5, t_comp - 0.10)
    gap = int(round(9.0 * (1.0 - kapp)))
    if ks > 0.002:
        gap = 0
    vib_on = (t_vib - 0.45) <= t < (t_comp + 0.40)
    if vib_on:
        jl = int(round(1.4 * math.sin(t * 9.3)))
        jr = int(round(1.4 * math.sin(t * 9.3 + 1.1)))
        jy = int(round(1.0 * math.sin(t * 7.7 + 0.4)))
    else:
        jl = jr = jy = 0
    lx = cx - 8 - gap + jl
    rx = cx + gap + jr
    sel = _c2_pick(space)
    nrow = len(sel)
    hy = cy - nrow // 2 + jy
    hy = max(top, min(bot - nrow + 1, hy))
    fgl = mix(P["rose"], P["white"], 0.20 + 0.55 * ks)
    fgr = mix(P["cyan"], P["white"], 0.20 + 0.55 * ks)

    # two carrier traces run across the whole field, above and below
    if space >= 14 and not tiny:
        sx0 = (px_ + pw_ + 2) if pw_ else 1
        _wave(cv, max(top, hy - 2), t, shade(P["rose"], 0.55), amp=1,
              freq=0.23, speed=5.4, floor=top, ch="˙", x0=sx0, x1=w - 1)
        _wave(cv, min(bot - 4, hy + nrow + 1), t, shade(P["rose"], 0.42),
              amp=1, freq=0.19, speed=4.2, floor=top, ch="·", x0=sx0,
              x1=w - 1)

    # ---- left instrument: sync, completeness, what is left ----------------
    if ph_:
        fx.panel(cv, px_, py_, pw_, ph_, shade(P["rose"], 0.75), bgp,
                 title=" vibration.monitor ", title_fg=shade(P["pink"], 0.9))
        bw = max(4, min(9, inner - 16))
        anim.meter(cv, px_ + 2, py_ + 1, "sync", sync * 100.0, 100.0, bw,
                   shade(P["rose"], 0.95), bg=bgp,
                   dim_fg=shade(P["grey"], 0.45))
        anim.meter(cv, px_ + 2, py_ + 2, "complete", complete, 100.0,
                   max(3, min(9, inner - 19)),
                   shade(P["amber"], 0.95), bg=bgp,
                   dim_fg=shade(P["grey"], 0.45))
        left_n = 5 - taken
        pips = "".join("▰" if i < left_n else "▱" for i in range(5))
        cv.text(px_ + 2, py_ + 3, _fit("left %s  %d/5" % (pips, left_n), inner),
                shade(P["soft"], 0.9), bgp)
        if ph_ >= 9:
            cv.hline(px_ + 2, py_ + 4, inner, "─", shade(P["rose"], 0.3), bgp)
            for r_ in range(2):
                yb = py_ + 5 + r_
                for i in range(inner):
                    v = math.sin(i * 0.52 + t * (7.4 + r_ * 3.1) + r_ * 1.7)
                    if v > 0.93:
                        v = 3.2
                    elif v > 0.86:
                        v = -2.4
                    yy = yb - int(round(v * 0.55))
                    cv.put(px_ + 2 + i,
                           max(py_ + 1, min(py_ + ph_ - 2, yy)), "·",
                           shade(P["pink"], 0.50 + 0.28 * (r_ == 0)), bgp)
            cv.hline(px_ + 2, py_ + 7, inner, "─",
                     shade(P["rose"], 0.3), bgp)
            anim.counter(cv, px_ + 2, py_ + 8, "v",
                         int(432 + 64 * math.sin(t * 2.7) +
                             26 * math.sin(t * 11.0)),
                         "%5d Hz", shade(P["ice"], 0.9), bg=bgp,
                         dim_fg=shade(P["grey"], 0.45))
            for r_ in range(2):
                kv = int(t * 14) + r_ * 3
                s_ = "0x%04X 0x%04X 0x%04X" % (
                    int(h01(kv, 1, 9) * 65535), int(h01(kv, 2, 9) * 65535),
                    int(h01(kv, 3, 9) * 65535))
                cv.text(px_ + 2, py_ + 9 + r_, _fit(s_, inner),
                        shade(P["violet"], 0.45), bgp)
        if ph_ >= 12:
            word = ("approaching" if t < t_vib else
                    "vibrating" if t < t_comp else
                    "complete" if t < t_left1 else
                    "detaching" if t < t_iso else "isolated")
            cv.text(px_ + 2, py_ + 11, _fit("%s  %s" % (word, "·" * (1 + int(t * 3) % 6)), inner),
                    shade(P["pink"], 0.8), bgp)
        # a read-head scans the instrument
        scan_y = py_ + 2 + int(t * 3.1) % (ph_ - 3)
        cv.text(px_, scan_y, "▌", shade(P["amber"], 0.85), bgp)

    # the gap crackles with the signal running between the halves
    if gap >= 2 and t < t_comp + 0.25 and space >= 10:
        xa, xb = lx + 9, rx - 1
        amp = 1.0 + 2.8 * kapp
        for x in range(xa, xb):
            u = (x - xa) / float(max(1, xb - xa))
            v = (math.sin(x * 0.55 + t * 11.0) *
                 amp * (0.35 + 0.65 * math.sin(math.pi * u)))
            cv.put(x, cy + int(round(v)),
                   "+" if abs(v) > amp * 0.78 else "~",
                   shade(P["amber"], 0.42 + 0.45 * kapp))

    if t < sc.t0 + 1.0 and not tiny:
        kk = ramp(t, sc.t0 + 0.10, sc.t0 + 0.95)
        for r_i, j in enumerate(sel):
            spr_ = 8 if hy - top >= 7 else 3
            anim.assemble(cv, lx, hy + r_i, [C2_L[j]], kk, fgl,
                          seed=7 + j, spread=spr_, snap=0.4, y_min=top)
            anim.assemble(cv, rx, hy + r_i, [C2_R[j]], kk, fgr,
                          seed=23 + j, spread=spr_, snap=0.4, y_min=top)
    else:
        for r_i, j in enumerate(sel):
            y = hy + r_i
            b = _c2_band(j)
            if b < taken:
                continue
            if b == taken and kband > 0.0:
                for src, x0, fg in ((C2_L[j], lx, fgl), (C2_R[j], rx, fgr)):
                    for i, ch in enumerate(src):
                        if ch == " ":
                            continue
                        hh_ = h01(x0 + i, y, 5 + b)
                        if hh_ < kband * 0.55:
                            continue
                        if hh_ < kband:
                            cv.put(x0 + i + 1 + int(kband * 2),
                                   max(top, y - 1),
                                   "▒" if hh_ > kband * 0.8 else "░",
                                   shade(fg, 0.85 - 0.45 * kband))
                        else:
                            cv.put(x0 + i, y, ch, fg)
                continue
            cv.text(lx, y, C2_L[j], fgl)
            cv.text(rx, y, C2_R[j], fgr)

    # the snap: seam of light, then a ring that travels out
    if 0.0 <= t - t_comp < 0.6 and not tiny:
        kk = 1.0 - (t - t_comp) / 0.6
        for y in range(hy, hy + nrow):
            cv.put(cx - 1, y, "│", shade(P["white"], 0.9 * kk))
            cv.put(cx, y, "│", shade(P["white"], 0.6 * kk))
        fx.sparkle(cv, cx, cy, t, P["white"], seed=int(t * 9), n=10,
                   rad=max(2, min(9, min(cy - top, bot - cy) + 1)))
    if 0.0 <= t - t_comp < 1.1 and space >= 12:
        fx.ripple(cv, cx, cy, t - t_comp + 0.15, P["pink"],
                  n=3, speed=11.0, period=1.0)

    # ---- what leaves, and where it goes -----------------------------------
    for i, c in enumerate(cues_all):
        age = t - c
        if 0.0 <= age < 1.35 and not tiny:
            u = age / 1.35
            for m in range(11):
                a = h01(m, i, 3) * 6.283 + t * 0.4
                rr = 2.0 + u * (6.0 + 12.0 * h01(m, i, 4))
                x = int(cx + math.cos(a) * rr)
                y = int(hy + nrow // 2 + math.sin(a) * rr * 0.6 - u * 5)
                y = max(top, min(bot, y))
                if 0 <= x < w:
                    cv.put(x, y, "░" if u < 0.55 else "▒",
                           shade(mix(P["rose"], P["grey"], u), 0.85 * (1 - u)))

    # the witness: still here, then not
    youx, youy = w - 6, cy
    if t < t_left1:
        bright = 0.55 + 0.35 * math.sin(t * 3.1)
        if space >= 9:
            for j, ln in enumerate(art.YOU["diamond"]):
                cv.text(youx - 2, youy - 2 + j, ln, shade(P["pink"], bright))
            cv.text(youx - 2, youy + 3, '"me"', shade(P["pink"], 0.6))
        else:
            cv.put(youx, youy, "◆", shade(P["pink"], bright))
        fx.sparkle(cv, youx, youy, t, P["pink"], seed=int(t * 5), n=4,
                   rad=max(1, min(4, youy - top, bot - youy)))
    else:
        age = t - t_left1
        if age < 3.0 and space >= 8:
            u = age / 3.0
            xx = int(youx + 16 * u)
            yy = youy - 2 - int(10 * u)
            for j, ln in enumerate(art.YOU["diamond"]):
                cv.text(xx - 2, yy - 2 + j, ln,
                        mix(P["pink"], P["grey"], u * 1.1))
            if u > 0.35:
                s_ = "you"
                sh_, _ = fx.typewriter(s_, age - 0.9, 12.0)
                cv.text(xx - 2, yy + 3, sh_, shade(P["grey"], 0.6 * (1 - u)))

        _wave(cv, bot - 2, t, P["rose"], amp=(1 if space < 12 else 2),
              freq=0.20, speed=4.6, floor=top)

    # ---- the caption line: what the machine says about all this ----------
    if space >= 11 and w >= 60:
        cy_ = bot - 4
        if t < t_vib:
            body = "> locking on 0x%04X  amp %d.%d dB" % (
                int(h01(int(t * 3), 9, 2) * 65535), int(t * 2) % 10,
                int(h01(int(t * 5), 4, 2) * 10))
        elif t < t_comp:
            body = "> resonance v=%.1fHz  dphi=%.2f" % (
                432.0 + 26.0 * math.sin(t * 2.2), 0.5 + 0.5 * math.sin(t * 3.3))
        elif t < t_left1:
            body = "> complete = %.1f%%   (you + me) / me" % complete
        elif t < t_iso:
            body = "> left %d of 5 pieces   sync %.0f%%" % (5 - taken, sync * 100)
        else:
            body = "> isolation: 1 dot, no reference"
        cv.text(2, cy_, _fit(body, w - 6), shade(P["ice"], 0.85))

    # ---- the bottom instrument: wave, captions, telemetry -----------------
    if space >= 9:
        log = ("sei.log · vib %d%% · seam %d · left %d/5 · complete %3d%% · "
               "v=%.1fHz · " % (int(min(99, sync * 100)), gap, 5 - taken,
                                int(complete), 432.0 + 26.0 * math.sin(t * 2.2)))
        anim.ticker(cv, bot, log, t, speed=20.0,
                    fg=shade(P["rose"], 0.62), x0=2, x1=w - 3)
        if full:
            hexs = " ".join("%04X" % int(h01(int(t * 11) + i, 31) * 65535)
                            for i in range(14))
            anim.ticker(cv, bot - 1, "adc." + hexs, t, speed=24.0,
                        fg=shade(P["violet"], 0.46), x0=2, x1=w - 3)
    if space >= 10:
        st = ("01 approach" if t < t_vib else
              "02 vibration" if t < t_comp else
              "03 completion" if t < t_left1 else
              "04 detachment" if t < t_iso else "05 isolation")
        line = "%s  gap %d  sync %3d%%  left %d/5" % (
            st, gap, int(sync * 100), 5 - taken)
        cv.put(2, bot - 3, "▸", shade(P["phos"], 0.95))
        cv.text(4, bot - 3, _fit(line, w - 8), shade(P["soft"], 0.75))

    # ---- isolation: one dot in an empty field, heartbeat fading -----------
    if t >= t_iso - 0.15:
        dt = t - t_iso
        pulse = 0.5 + 0.5 * math.sin(dt * 4.2)
        xf = (px_ + pw_ + 2) if pw_ else 2
        fl_y = min(cy + 3, bot)
        for x in range(xf, w - 2):
            cv.put(x, fl_y, "─", shade(P["rose"], 0.14))
        bx = 2 + int((t * 22) % max(1, w - 6))
        cv.put(bx, fl_y, "╱", shade(P["pink"], 0.65))
        cv.put(min(w - 2, bx + 1), fl_y, "╲", shade(P["pink"], 0.5))
        cv.put(cx, cy, "●" if pulse > 0.42 else "·",
               shade(P["pink"], 0.45 + 0.5 * pulse))
        if not tiny:
            if space >= 12:
                fx.ripple(cv, cx, cy, t, P["rose"], n=3, speed=6.0, period=1.6)
            # the ghost of what was here still flickers
            fl = max(0.0, math.sin(dt * 3.1)) * 0.30 * (1.0 - min(1.0, dt / 2.4))
            if fl > 0.04:
                for r_i, j in enumerate(sel):
                    for src, x0 in ((C2_L[j], lx), (C2_R[j], rx)):
                        for i, ch in enumerate(src):
                            if ch != " " and h01(i, j, 5) < fl * 2.4:
                                cv.put(x0 + i, hy + r_i, "░",
                                       shade(P["grey"], 0.55 * fl))
            # a decay band keeps crossing the field
            for r_ in range(2):
                y = top + 2 + (r_ + int(t * 5.0)) % 5
                for x in range((px_ + pw_ + 2) if pw_ else 2, w - 1):
                    if (x + int(t * 20)) % 9 < 2:
                        cv.put(x, y, "▒", shade(P["rose"], 0.18))
        if space >= 11 and w >= 54:
            sh_, typ = fx.typewriter("isolation", dt - 0.3, 12.0)
            cv.text(2, cy + 5, sh_, shade(P["grey"], 0.75))
            if typ and int(t * 10) % 2 == 0:
                cv.put(2 + sw(sh_), cy + 5, "▮", shade(P["grey"], 0.7))

    if not tiny:
        fx.scanlines(cv, 0.88)
        fx.vignette(cv, 0.20)
# ==========================================================================
# 8 · BRIDGE — erase fragments / challenge god / illegal arguments
# ==========================================================================

class BridgeScene(Scene):
    key = "bridge"
    accent = "amber"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_erase = cue("If I can erase all the pointless fragments")
        t_maybe = cue("Then maybe")
        t_dis = cue("Then maybe you won't leave me so disheartened")
        t_god = cue("Challenging your god")
        t_ill = cue("You have made some illegal arguments")
        cx = w // 2

        # ---------- isolation: alone with an empty reference --------
        a = fade_window(t, self.t0 + 0.3, t_erase - 0.25, 0.8, 0.6)
        if a > 0.01:
            def alone(cv2):
                me = art.ME["sit"]
                mx = cx - 11
                my = h // 2 - 1
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, mix(P["phos"], P["grey"], 0.55))
                lab = "you: <null>"
                shown, typing = fx.typewriter(lab, t - self.t0 - 0.8, 16.0)
                cv2.text(cx + 8, my + 1, shown, shade(P["grey"], 0.8))
                if typing and int(t * 8) % 2 == 0:
                    cv2.put(cx + 8 + sw(shown), my + 1, "▮", shade(P["grey"], 0.6))
                if t >= self.t0 + 2.4:
                    s2 = "segmentation fault (core dumped)"
                    sh2, _ = fx.typewriter(s2, t - self.t0 - 2.4, 30.0)
                    cv2.ctext(my + len(me) + 2, sh2, shade(P["red"], 0.55))
                # dust motes drifting where "you" used to be
                for i in range(14):
                    u = ((t * 0.22 + i / 14.0) % 1.0)
                    dx = cx + 8 + int(math.sin(i * 1.9 + t * 0.4) * 6)
                    dy = my + 3 - int(u * 9)
                    cv2.put(dx, dy, "·", shade(P["grey"], 0.28 * (1 - abs(u - 0.5) * 2)))
            stamp(cv, alone, a)

        # ---------- pointless fragments: files AND memory ----------
        a = fade_window(t, t_erase - 0.4, t_maybe - 0.15, 0.4, 0.45)
        if a > 0.01:
            def fragments(cv2):
                wide = w >= 74
                fh = min(12, max(7, h - 9)) if wide else min(9, max(5, h - 5))
                fy = max(2, (h - fh) // 2 - 1) if wide else \
                    max(1, (h - fh) // 2)
                if wide:
                    fw = (w - 6) // 2
                    fx0, mx0 = 2, 4 + fw
                    mw = w - mx0 - 2
                else:
                    fw = w - 4
                    fx0, mx0 = 2, 2
                    mw = fw

                # ---- left: the files themselves ----------------------
                fx.panel(cv2, fx0, fy, fw, fh, shade(P["cyan"], 0.85),
                         title=" ~/world/mili/memories/ ")
                rows = [("ac_dc.wav", "3.1M"), ("tangents.png", "812K"),
                        ("nutrients.dat", "64K"), ("purr.wav", "1.4M"),
                        ("god.ray", "22K"), ("you/", "??")]
                for i, (name, sz) in enumerate(rows):
                    yy = fy + 2 + i
                    if yy >= fy + fh - 2:
                        break
                    at = t_erase + 0.30 + i * 0.5
                    if t < at:
                        cv2.text(fx0 + 2, yy, "├─", shade(P["grey_dim"], 0.9))
                        cv2.text(fx0 + 5, yy, name, shade(P["soft"], 0.9))
                        if fw >= 36:
                            cv2.text(fx0 + fw - 12, yy, sz,
                                     shade(P["grey"], 0.55))
                        continue
                    k = ramp(t, at, at + 0.7)
                    if name == "you/":
                        cv2.text(fx0 + 2, yy, "├─", shade(P["rose"], 0.9))
                        cv2.text(fx0 + 5, yy, "you/", P["pink"])
                        if k > 0.55 and fw >= 40:
                            cv2.text(fx0 + 5, yy + 1,
                                     "rm: 'you': not empty"[:fw - 7],
                                     shade(P["red"], 0.9))
                        continue
                    cv2.text(fx0 + 2, yy, "├─", shade(P["grey_dim"], 0.9))
                    left_ = name[:max(0, len(name) - int(k * len(name)))]
                    cv2.text(fx0 + 5, yy, left_, shade(P["grey"], 0.7))
                    if k > 0.9:
                        cv2.text(fx0 + 5, yy, "unlinked", shade(P["grey_dim"], 0.9))
                    elif k > 0.35:
                        cv2.hline(fx0 + 5, yy, len(name), "─",
                                  shade(P["red"], 0.75))
                cv2.text(fx0 + 2, fy + fh - 2, "$ rm -rf ./pointless/*",
                         shade(P["phos"], 0.75))

                # ---- the memory those files were living in ----------
                if not wide:
                    # stacked version: same bytes, a few rows underneath
                    my0 = fy + fh
                    words2 = ["me..you.", "world.ex", "ecute(me"]
                    nhex = max(0, min(3, (h - 1) - my0))
                    for r in range(nhex):
                        yy = my0 + r
                        word = words2[r]
                        p = ramp(t, t_erase + 0.45 + r * 0.4,
                                 t_erase + 1.25 + r * 0.4)
                        cv2.text(2, yy, "%05x" % (0x7ff0 + r * 8),
                                 shade(P["amber"], 0.6))
                        for j, ch in enumerate(word[:8]):
                            gone = p * 8.0 > j
                            cv2.text(8 + j * 3, yy,
                                     "00" if gone else "%02x"
                                     % (ord(ch) if ch != "." else 0),
                                     shade(P["grey_dim"] if gone else P["amber"],
                                           0.8))
                    rel = ramp(t, t_erase, t_maybe + 0.3)
                    yh = min(h - 1, my0 + nhex)
                    if yh >= my0:
                        cv2.text(2, yh, "heap", shade(P["grey"], 0.7))
                        bw2 = max(6, min(14, w - 20))
                        fx.bar(cv2, 7, yh, bw2, 1.0 - 0.88 * rel,
                               shade(P["amber"], 0.9), None)
                        cv2.text(9 + bw2, yh,
                                 "%2d%%" % int((1 - 0.88 * rel) * 100),
                                 shade(P["amber"], 0.85))
                    return
                fx.panel(cv2, mx0, fy, mw, fh, shade(P["amber"], 0.85),
                         title=" mem 0x7ff0 · pid 1 ")
                words = ["me..you.", "world.ex", "ecute(me", ");..ac_d",
                         "c.wav...", "purr....", "love()..", "0x2A...."]
                nrow = min(len(words), fh - 4)
                for r in range(nrow):
                    yy = fy + 2 + r
                    word = words[r]
                    addr = 0x7ff0 + r * 8
                    p = ramp(t, t_erase + 0.45 + r * 0.33,
                             t_erase + 1.25 + r * 0.33)
                    cv2.text(mx0 + 2, yy, "%05x" % addr, shade(P["amber"], 0.6))
                    hx = mx0 + 8
                    for j, ch in enumerate(word[:8]):
                        b = ord(ch) if ch != "." else 0
                        gone = p * 8.0 > j
                        if gone:
                            cv2.text(hx + j * 3, yy, "00",
                                     shade(P["grey_dim"], 0.7))
                        else:
                            cv2.text(hx + j * 3, yy, "%02x" % b,
                                     shade(P["amber"], 0.8))
                    asc = mx0 + 8 + 24
                    if mw >= 42:
                        for j, ch in enumerate(word[:8]):
                            gone = p * 8.0 > j
                            cv2.put(asc + j, yy, "·" if gone else
                                    (ch if ch != "." else "·"),
                                    shade(P["soft"] if not gone else P["grey_dim"],
                                          0.85 if not gone else 0.6))
                    if 0.15 < p < 0.9 and h01(r, int(t * 6)) < 0.3:
                        cv2.put(mx0 + mw - 3, yy, "▒", shade(P["amber"], 0.5))

                # heap shrinking + counters
                rel = ramp(t, t_erase, t_maybe + 0.3)
                by2 = fy + fh - 2
                cv2.text(mx0 + 2, by2, "heap", shade(P["grey"], 0.7))
                bw2 = max(6, min(16, mw - 22))
                fx.bar(cv2, mx0 + 7, by2, bw2, 1.0 - 0.88 * rel,
                       shade(P["amber"], 0.9), None)
                cv2.text(mx0 + 9 + bw2, by2, "%2d%%" % int((1 - 0.88 * rel) * 100),
                         shade(P["amber"], 0.85))

                # ---- the shreds themselves, falling ------------------
                for i in range(26):
                    u = ((t * 0.85 + h01(i, 91)) % 1.0)
                    sx = 2 + int(h01(i, 92) * (w - 4))
                    sy = 2 + int(u * (h - 5))
                    ch = "ac_dc.wavyou"[i % 11]
                    cv2.put(sx, sy, "▒" if h01(i, int(t * 5)) < 0.6 else ch,
                            shade(P["grey_dim"], 0.32 * (1.0 - u)))
                cv2.text(2, h - 6, "fragments · %d files · %d bytes · 0x%06X freed"
                         % (5, int(4096 + 91000 * rel), int(0x1A4000 * rel)),
                         shade(P["amber"], 0.6))
            stamp(cv, fragments, a)

        # ---------- hug the last fragment ---------------------------
        a = fade_window(t, t_maybe - 0.05, t_god + 0.3, 0.4, 0.45)
        if a > 0.01:
            def hug(cv2):
                me = art.ME["sit"]
                mx = cx - 8
                my = h // 2 - 2
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, mix(P["phos"], P["grey"], 0.4))
                # the folder
                fx.bracket(cv2, mx + 10, my + 1, 9, 4, P["pink"], style="<>")
                cv2.text(mx + 12, my + 2, "you/", P["pink"])
                # the one memory block that is not a pointless fragment
                if t >= t_maybe + 0.2:
                    kr = ramp(t, t_maybe + 0.2, t_maybe + 1.0)
                    yy = min(h - 5, my + len(art.ME["sit"]) + 1)
                    cv2.text(mx - 2, yy, "0x7ff8", shade(P["amber"], 0.6 * kr))
                    cv2.text(mx + 8, yy, "79 6f 75 00", shade(P["pink"], kr))
                    cv2.text(mx + 22, yy, '"you."', shade(P["pink"], kr))
                    cv2.put(mx + 30, yy, "♥", shade(P["rose"], kr))
                for i in range(8):
                    u = ((t * 0.5 + i / 8.0) % 1.0)
                    cv2.put(int(mx + 10 + math.sin(i * 2.1) * 3),
                            int(my - 2 - u * 5), "·", shade(P["grey"], 0.4))
                if t >= t_dis - 0.2:
                    s = "maybe if I delete myself, you'll come back?"
                    shown, typing = fx.typewriter(s, t - t_dis + 0.2, 26.0)
                    cv2.ctext(h - 3, shown, shade(P["grey"], 0.85))
            stamp(cv, hug, a)

        # ---------- god looms ---------------------------------------
        a = fade_window(t, t_god - 0.3, t_ill + 1.2, 0.5, 0.5)
        if a > 0.01:
            def god(cv2):
                gy = 2
                # giant shoulders + head silhouette
                for i, ln in enumerate(art.ART["god"][:9]):
                    xx = cx - 13
                    cv2.text(xx, gy + i, ln, shade(P["gold"], 0.85))
                # light rays down
                for i in range(9):
                    x = cx - 20 + i * 5
                    for yy in range(gy + 9, h - 7):
                        if h01(x, yy, int(t)) < 0.35:
                            cv2.put(x + (yy // 3) % 3, yy, "│",
                                    shade(P["amber"], 0.18))
                # tiny me with raised fist
                me = art.ME["reach2"]
                mx = cx - 4
                my = h - len(me) - 4
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, P["phos"])
                if t >= t_god + 0.3:
                    cv2.text(mx + 10, my - 1, "$ god --challenge", P["phos"])
                if t >= t_ill - 0.1:
                    cv2.text(mx + 10, my + 1, "ERROR: illegal arguments",
                             P["red"])
            stamp(cv, god, a)

        # ---------- illegal arguments flood -------------------------
        if t >= t_ill - 0.15:
            def errors(cv2):
                lines = [
                    "ERROR: illegal arguments to love()",
                    "  at love (me.js:1:1)",
                    "  at devotion (me.js:7:13)",
                    "  at world.execute (kernel:130)",
                    "TypeError: cannot convert 'love' to 'obedience'",
                    "Segmentation fault (core dumped)",
                    "FATAL: argument 'me' is not accepted by god()",
                ]
                n = int((t - t_ill) * 6) + 1
                for i in range(min(n, 14)):
                    s = lines[i % len(lines)]
                    y = h - 2 - i
                    if y < 1:
                        break
                    c = P["red"] if i % 2 == 0 else shade(P["blood"], 1.5)
                    cv2.text(2 + (i % 3) * 2, y, s, shade(c, 0.9 - i * 0.03))
            stamp(cv, errors, fade_window(t, t_ill - 0.15, self.t1 + 0.2, 0.2, 0.1))

        anim.scanline(cv, t, 4, h - 2, P["white"], speed=15.0, band=3,
                      seed=31)
        if t > t_god - 0.3:
            # the whole frame trembles: something bigger than the machine has
            # been asked a question
            kt = ramp(t, t_god - 0.3, t_god + 0.9) * (1.0 - 0.5 * ramp(
                t, t_ill, self.t1))
            if kt > 0.02:
                fx.row_wave(cv, t * 1.7, amp=1.4 * kt, freq=0.55, speed=3.1)
        fx.scanlines(cv, 0.8)
        if t > t_god:
            fx.glitch(cv, t, 0.15 * ramp(t, t_god, t_ill + 1.0))


# ==========================================================================
# 9 · BUILD — error cascade, charging beam
# ==========================================================================

class BuildScene(Scene):
    key = "build"
    accent = "red"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        tl = t - self.t0
        cx = w // 2

        k = ramp(t, self.t0, self.t1 - 1.6)
        # cascading errors accelerating
        rate = 3.0 + 26.0 * k * k
        n = int(tl * rate / 3.0) % 400
        chars = "ERROR0123456789/\\|<>[]{}()#@$%&*"
        for i in range(min(40, int(tl * rate * 0.5))):
            y = int(h01(i, int(t * 3)) * (h - 2))
            x = int(h01(i, int(t * 3) + 1) * (w - 20))
            ln = "".join(chars[int(h01(i, j, int(t * 2)) * len(chars))]
                         for j in range(6 + int(h01(i, 5) * 14)))
            c = shade(mix(P["blood"], P["red"], h01(i, 9)), 0.5 + 0.4 * k)
            cv.text(x, y, ln, c)

        # equalizer walls
        for side in (0, 1):
            for i in range(10):
                e = ctx.e_at(t - 0.05 + i * 0.01)
                hgt = int((0.3 + 2.4 * e) * (0.4 + h01(i, side, 3)))
                x = 2 + i * 2 if side == 0 else w - 3 - i * 2
                for j in range(hgt):
                    y = h - 2 - j
                    cv2c = shade(mix(P["red"], P["amber"], j / max(1, hgt)), 0.8)
                    cv.put(x, y, "▌" if side == 0 else "▐", cv2c)

        # charging beam
        beam_k = ramp(t, self.t0 + 0.5, self.t1 - 1.0)
        bh = int((h - 4) * beam_k ** 1.6)
        for y in range(h - 2 - bh, h - 1):
            d = (h - 2 - y) / max(1, bh)
            c = mix(P["white"], P["red"], min(1.0, 0.25 + d))
            cv.put(cx - 1, y, "▐", c)
            cv.put(cx, y, "█", c)
            cv.put(cx + 1, y, "▌", c)
        if bh > 3:
            fx.sparkle(cv, cx, h - 3 - bh, t, P["white"], seed=int(t * 9), n=8, rad=5)

        # countdown ticks
        if tl > 2:
            left = int((self.t1 - t) / 0.4615) + 1
            if left >= 0:
                cv.ctext(2, "%d" % left, shade(P["red"], 0.75))
        # warning header
        if t < self.t1 - 1.5:
            cv.text(2, 1, "KERNEL PANIC — EXECUTION PENDING", P["red"])
            if int(t * 2.5) % 2 == 0:
                cv.rtext(1, "!! WARNING !!", P["red"], right=w - 3)
        else:
            cv.ctext(h // 2 - 1, "ready.", mix(P["white"], P["red"], 0.4))

        fx.glitch(cv, t, 0.1 + 0.5 * k)
        fx.scanlines(cv, 0.8)
        fx.desaturate(cv, 0.0, 1.0 - 0.0 * k)
        fx.vignette(cv, 0.35)


# ==========================================================================
# 10 · CHANT — EXECUTION
# ==========================================================================

class ChantScene(Scene):
    key = "chant"
    accent = "red"

    EXEC_T = [147.90, 151.59, 155.28]
    COUNT_T = 158.97

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        cx = w // 2
        tl = t - self.t0

        # background rain of the word
        fx.matrix_rain(cv, t * 1.6, shade(P["blood"], 0.55), density=0.34,
                       charset="EXECUTIONexecution", speed=26.0, seed=9, tail=6)

        counting = t >= self.COUNT_T - 0.35
        idx = int((t - self.EXEC_T[0]) / 0.9225)

        if not counting:
            sc = banner_fit("EXECUTION", w - 8, gap=1, rows=h - 10)
            if sc > 3:
                sc = 3
            bl = art.banner_lines("EXECUTION", sc, 1)
            bw = art.banner_width("EXECUTION", sc, 1)
            bh = len(bl)
            y0 = h // 2 - bh // 2 - 1
            cv.fill(cx - bw // 2 - 2, y0 - 1, bw + 4, bh + 2, " ",
                    None, P["black"])
            style = idx % 4
            flash = max(0.0, 1.0 - ((t - self.EXEC_T[0]) % 0.9225) / 0.20)
            if style == 0:
                col = mix(P["white"], P["red"], 0.15)
                bg = shade(P["blood"], 0.55)
            elif style == 1:
                col = P["red"]
                bg = None
            elif style == 2:
                col = mix(P["white"], P["amber"], 0.15)
                bg = None
            else:
                col = P["blood"]
                bg = shade(P["red"], 0.9)
            x0 = cx - bw // 2
            for j, ln in enumerate(bl):
                for i, ch in enumerate(ln):
                    if ch == " ":
                        continue
                    xx = x0 + i
                    yy = y0 + j
                    if style == 2 and h01(xx, yy, idx) < 0.06:
                        continue
                    jit = 0
                    if style == 2:
                        jit = int((h01(xx, yy, idx + 3) - 0.5) * 2.0)
                    cv.put(xx + jit, yy, ch, col, bg)
            # frame flash
            if flash > 0.05:
                for x in range(w):
                    cv.put(x, 0, "▀", shade(col, flash))
                    cv.put(x, h - 1, "▄", shade(col, flash))
            # pun caption
            cap = ("$ exec me            // 运行我"
                   if idx % 2 == 0 else
                   "☠ EXECUTE  ME        // 处死我")
            cv.ctext(h - 3, cap, mix(P["white"], P["red"], 0.3))
            cv.ctext(2, "EXECUTION", shade(P["red"], 0.5))
        else:
            # ---- counting 1..6 -------------------------------------
            words = [("EIN", "1"), ("DOS", "2"), ("TROIS", "3"),
                     ("NE", "4"), ("FEM", "5"), ("LIU", "6")]
            wt = 3.2 / 6.0
            k = (t - self.COUNT_T) / wt
            i = max(0, min(5, int(k)))
            frac = k - int(k)
            word, num = words[i]
            sc = banner_fit(word, w - 14, gap=1, rows=h - 14)
            bl = art.banner_lines(word, sc, 1)
            bw = art.banner_width(word, sc, 1)
            bh = len(bl)
            scale_in = ramp(frac, 0.0, 0.18)
            col = mix(P["white"], P["red"], min(1.0, frac * 0.9))
            # reticle
            r = max(6, min(w // 5, h // 2 - 2))
            fx.circle(cv, cx, h // 2, r, shade(P["red"], 0.5), "·", ry=r / 2)
            fx.circle(cv, cx, h // 2, r - 2, shade(P["red"], 0.3), "·", ry=(r - 2) / 2)
            for d in (-1, 1):
                fx.line(cv, cx + d * (r - 1), h // 2, cx + d * (r + 3), h // 2, P["red"])
                fx.line(cv, cx, h // 2 + d * (r // 2 - 1), cx, h // 2 + d * (r // 2 + 1), P["red"])
            y0 = h // 2 - bh // 2
            cv.fill(cx - bw // 2 - 2, y0 - 1, bw + 4, bh + 2, " ",
                    None, P["black"])
            draw_banner(cv, word, y0, shade(col, 0.5 + 0.5 * scale_in), sc)
            cv.ctext(y0 + bh + 1, num, shade(P["amber"], 0.9))
            # progress dots
            for d in range(6):
                ch = "●" if d <= i else "○"
                cv.text(cx + (d - 2) * 3 - 1, h - 4, ch,
                        P["white"] if d <= i else shade(P["red"], 0.5))

        # final single execution at 161.66
        t_fin = cue("Execution", 1)
        if t >= t_fin:
            k = ramp(t, t_fin, t_fin + 0.4)
            cv.clear()
            for y in range(h):
                cv.hline(0, y, w, " ", None)
            sc = banner_fit("EXECUTION", w - 8, gap=1, rows=h - 10)
            if sc > 3:
                sc = 3
            bl = art.banner_lines("EXECUTION", sc, 1)
            bh = len(bl)
            draw_banner(cv, "EXECUTION", h // 2 - bh // 2,
                        mix(P["white"], P["red"], 0.2), sc)
            if int(t * 6) % 2 == 0:
                cv.ctext(h // 2 + bh // 2 + 2, "— 执行 —", P["red"])

        fx.scanlines(cv, 0.75)


# ==========================================================================
# 11 · FINAL CHORUS — give them all the execution
# ==========================================================================

class FinalScene(Scene):
    key = "final"
    accent = "rose"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_give = cue("If I can give them all the execution")
        t_only = cue("Then I can be your only execution")
        t_back = cue("If I can have you back")
        t_trap = cue("Though we are trapped", 1)     # index 0 is chorus 1
        cx = w // 2
        mid = h // 2 - 1

        # the whole world falls away behind everything
        fx.matrix_rain(cv, t * 1.2, shade(P["blood"], 0.5), density=0.22,
                       charset="✕†;", speed=20.0, seed=13, tail=4)

        # ---------- every program in the world, then only you -------
        a = fade_window(t, t_give - 0.35, t_back + 0.6, 0.45, 0.45)
        if a > 0.01:
            def targets(cv2):
                killp = ramp(t, t_give - 0.2, t_only - 0.1)
                col = ramp(t, t_only - 0.05, t_only + 1.25)
                nere = min(14, max(4, h - 11))
                py = 2
                ph = nere + 5
                names = ["ac_dc.wav", "tangents.png", "nutrients.dat", "clock",
                         "simulation", "god.ray", "tomato", "purr.wav",
                         "AM/PM", "the.world", "pointless", "dishes",
                         "sun.moon", "them.all"]
                if col < 0.99:
                    fx.panel(cv2, 2, py, w - 4, ph,
                             shade(P["blood"], 0.85 - 0.5 * col),
                             title=" execution.targets · batch ")
                for r in range(nere):
                    y0 = py + 2 + r
                    y = int(round(y0 + (mid - y0) * col))
                    at = t_give + 0.35 + r * 0.15
                    dead = t >= at
                    aa = 1.0 if col <= 0.45 else max(0.0, 1.0 - (col - 0.45) * 2.0)
                    if aa <= 0.03:
                        continue
                    cv2.text(3, y, "%04d" % (2 + r * 251),
                             shade(P["grey"], 0.5 * aa))
                    cv2.text(9 if w >= 60 else 10, y, names[r % len(names)],
                             shade(P["grey_dim"] if dead else P["soft"], aa))
                    if w >= 52:
                        tag = "KILLED" if dead else "RUN"
                        c = shade(P["red"], aa) if dead else shade(P["phos"],
                                                                   0.65 * aa)
                        cv2.text(max(12, w - 14), y,
                                 ("[✓] " if dead else "[·] ") + tag, c)
                exc = int(4095 * killp)
                yy = py + ph - 3
                ca = max(0.0, 1.0 - col * 1.3)
                if ca > 0.02:
                    cv2.text(3, yy, "executed: %04d / 4096" % exc,
                             shade(P["red"], 0.9 * ca))
                    if killp >= 0.999:
                        bl = 0.55 + 0.45 * math.sin(t * 7.0)
                        cv2.text(3, yy + 1, "remaining: 1  ←",
                                 shade(P["rose"], bl * ca))
                # ---- 4095 rows collapse into a single line ----------
                if col > 0.5:
                    kk = ramp(t, t_only + 0.25, t_only + 1.15)
                    line = " ◆ 0001 · you · execution = only ◆ "
                    hw2 = sw(line)
                    ly = mid
                    cv2.text(cx - hw2 // 2, ly, line, shade(P["pink"], kk))
                    if w >= 40:
                        for i in range(hw2 // 2 + 2):
                            x1, x2 = cx - hw2 // 2 - 2 - i, cx + hw2 // 2 + 1 + i
                            if x1 >= 1 and x2 < w - 1:
                                cv2.put(x1, ly, "═", shade(P["rose"], 0.55 * kk))
                                cv2.put(x2, ly, "═", shade(P["rose"], 0.55 * kk))
                    if kk > 0.7:
                        cv2.ctext(max(1, ly - 4), "only you. only you.",
                                  shade(P["rose"], 0.8 * kk))
                        if ly - 2 > 0:
                            cv2.ctext(ly - 2, "4095 others: deleted",
                                      shade(P["grey"], 0.55 * kk))
                        if kk > 0.85 and ly + 2 < h - 3:
                            shown, typing = fx.typewriter("$ execute(you) --only",
                                                          t - (t_only + 0.85), 30.0)
                            cv2.ctext(ly + 2, shown, shade(P["phos"], 0.8))
            stamp(cv, targets, a)

        # ---------- if I can have you back --------------------------
        a = fade_window(t, t_back - 0.55, t_trap + 0.5, 0.45, 0.5)
        if a > 0.01:
            def reach(cv2):
                me = art.ME["reach2"]
                mx = cx - 4
                my = h - len(me) - 3
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, mix(P["phos"], P["white"], 0.35))
                if t >= t_back - 0.4:
                    g = ramp(t, t_back - 0.4, t_back + 0.8)
                    flick = 0.55 + 0.35 * math.sin(t * 8.5)
                    gy = 4
                    for j, ln in enumerate(art.YOU["ghost"]):
                        cv2.text(cx - 2, gy + j, ln, shade(P["ice"], g * flick))
                    if g > 0.7 and w >= 30:
                        cv2.text(cx + 4, gy + 2, "you?", shade(P["ice"], 0.75))
                    for i in range(5):        # hearts travel up to you
                        yy = my - 1 - i * 2
                        if yy > gy + 6:
                            cv2.put(cx + int(math.sin(t * 3 + i)), yy, "♥",
                                    shade(P["rose"], 0.25 + 0.15 * i))
                    s = "$ if (you) return you;"
                    shown, typing = fx.typewriter(s, t - t_back, 22.0)
                    cv2.ctext(min(h - 3, my + len(me) + 2), shown,
                              shade(P["grey"], 0.85))
                    # the obsession, stated quietly at the edges
                    if t >= t_back + 0.5 and w >= 40:
                        rr = ramp(t, t_back + 0.5, t_back + 1.5)
                        for i in range(3):
                            cv2.text(2 + i, 3 + i * 4, "only you",
                                     shade(P["rose"], 0.38 * rr))
                            cv2.text(w - 11 - i, 3 + i * 4, "only you",
                                     shade(P["rose"], 0.38 * rr))
            stamp(cv, reach, a)

        # ---------- trapped together, cage of hearts -----------------
        if t >= t_trap - 0.3:
            def cage(cv2):
                kk = ramp(t, t_trap - 0.3, t_trap + 1.2)
                bw = max(18, int(w * 0.36))
                bh = max(10, int(h * 0.62))
                x = cx - bw // 2
                y = h - bh - 3
                fx.bracket(cv2, x, y, bw, bh, shade(P["rose"], 0.9), style="<>")
                cells = []
                for i in range(1, bw - 1):
                    cells.append((x + i, y))
                    cells.append((x + i, y + bh - 1))
                for j in range(1, bh - 1):
                    cells.append((x, y + j))
                    cells.append((x + bw - 1, y + j))
                n = int(len(cells) * min(1.0, kk * 1.2))
                for i in range(n):
                    px, py = cells[i]
                    cv2.put(px, py, "♥" if i % 7 else "◆",
                            mix(P["rose"], P["pink"], h01(i, 3)))
                me = art.ME["sit"]
                mx = cx - 9
                my = y + bh - len(me) - 1
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, P["grey"])
                for j, ln in enumerate(art.YOU["small"]):
                    cv2.text(max(1, mx - 5), my + 2 + j, ln, shade(P["ice"], 0.7))
                # a chain of hearts between the two of us
                if kk > 0.8:
                    for i in range(4):
                        cv2.put(mx + 5 + i, my + 3 + (i % 2), "♥",
                                shade(P["pink"], 0.6))
                    cv2.ctext(y - 2, "trapped", shade(P["pink"], 0.85))
                    if t >= t_trap + 1.3:
                        km = ramp(t, t_trap + 1.3, t_trap + 2.1)
                        cv2.ctext(y - 1, "mine.", shade(P["rose"], 0.9 * km))
            stamp(cv, cage, fade_window(t, t_trap - 0.3, self.t1 + 0.3, 0.3, 0.2))

        # ---------- the kill rate never settles ----------
        # two instrument rows: the execution throughput and the things still
        # dying (so "the only execution" is watched while it runs)
        if h >= 18:
            ph = t * 24.0
            for x in range(4, w - 5):
                u = (x + ph) * 0.30
                v = math.sin(u) * 0.55 + math.sin(u * 2.7 + 0.6) * 0.45
                cv.put(x, 5, "▁▂▃▄▅▆▇█"[max(0, min(7, int((v + 1.0) * 3.5)))],
                       mix(P["red"], P["amber"], 0.35 + 0.4 * (v + 1.0) / 2.0))
            for x in range(4, w - 5):
                q = h01(x, int(t * 11.0), 77)
                if q < 0.34:
                    cv.put(x, 6, "†" if q < 0.17 else "✕",
                           shade(P["red"] if q < 0.17 else P["blood"],
                                 0.25 + 0.6 * q))
        anim.scanline(cv, t, 4, h - 2, P["white"], speed=17.0, band=3,
                      seed=41)
        fx.scanlines(cv, 0.78)
        fx.vignette(cv, 0.3)
        # the picture trembles when it says "only"
        sh = ramp(t, t_only - 0.1, t_only + 0.35) * (1.0 - ramp(t, t_only + 0.9,
                                                               t_only + 1.4))
        if sh > 0.01:
            fx.shake(cv, t, 1.2 * sh, 5)
        if t > t_trap:
            fx.desaturate(cv, 0.35 * ramp(t, t_trap, self.t1), 0.95)


# ==========================================================================
# 12 · OUTRO — algebra of love
# ==========================================================================

class OutroScene(Scene):
    """2:57 — the love exam.  Everything is a document: a page of notes, an
    examination sheet, the algebraic expression, and finally the one line of
    algebra that will not let go of me."""

    key = "outro"
    accent = "gold"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_study = cue("I've studied")
        t_proper = cue("I've studied how to properly lo-o-ove")
        t_q = cue("Question me")
        t_ans = cue("Question me I can answer all lo-o-ove")
        t_alg = cue("I know the algebraic expression of lo-o-ove")
        t_free = cue("Though you are free")
        t_trap = cue("I am trapped")
        t_love = cue("Trapped in lo-o-ove")
        cx = w // 2
        ink = mix(P["amber"], P["white"], 0.22)
        inkd = shade(P["amber"], 0.5)
        paper = mix(P["black"], P["amber"], 0.07)
        compact = h <= 10          # 48x14: no room for panels, just lines

        # ---------- 1 · homework: a page of notes -------------------
        if t_study - 0.35 <= t < t_q + 0.35 and compact:
            cv.text(2, 1, "notes · how to properly lo-o-ove"[:w - 4],
                    shade(P["amber"], 0.75))
            rows = ["DEF  love(x) := the wish that x goes on",
                    "LEM  ∀ me ∃ you : you ⊂ me.love",
                    "THM  properly(love) ⇔ no condition"]
            nmax = max(1, h - 4)
            for i, txt in enumerate(rows[:nmax]):
                at = t_study + 0.35 + i * 0.5
                if t < at:
                    continue
                shown, typing = fx.typewriter(txt, t - at, 46.0)
                cv.fill(0, 2 + i, w, 1, " ", None, None)
                cv.text(2, 2 + i, shown[:w - 4],
                        ink if i < 2 else mix(P["gold"], P["white"], 0.3))
            yy = h - 3
            cv.fill(0, yy, w, 1, " ", None, None)
            k = ramp(t, t_study, t_proper + 1.2)
            cv.text(2, yy, "studied", inkd)
            fx.bar(cv, 10, yy, max(6, min(12, w - 26)), k,
                   shade(P["amber"], 0.85), None)
            cv.text(11 + max(6, min(12, w - 26)), yy,
                    "%d pages" % int(4096 * k), inkd)

        if t_study - 0.35 <= t < t_q - 0.08 and not compact:
            wid, hgt = w - 4, h - 4
            px, py = 2, 2
            show_fig = w >= 82 and hgt >= 12
            lw = min(52, int(wid * 0.60) + 2) if show_fig else wid - 2
            fx.panel(cv, px, py, wid, hgt, shade(P["amber"], 0.5), bg=paper,
                     title=" notes · how to properly lo-o-ove ")
            hdr = 1 if hgt >= 9 else 0
            if hdr:
                cv.text(px + 2, py + 1, "p. 012 · love · theory of everything",
                        shade(P["amber"], 0.4), bg=paper)
                if wid >= 56:
                    cv.rtext(py + 1, " draft · 03:31 ",
                             shade(P["amber"], 0.28), bg=paper,
                             right=px + wid - 2)
            # ruled paper: one faint line under each item + margin rule
            rule = mix(paper, P["amber"], 0.13)
            cv.vline(px + lw, py + 2, hgt - 4, "│",
                     mix(paper, P["amber"], 0.3))
            for xx in range(px + 2, px + lw - 1):
                cv.put(xx, py + hgt - 3, "┄", rule)
            if hgt >= 20:
                step, subs = 3, True
            elif hgt >= 13:
                step, subs = 2, True
            else:
                step, subs = 1, False
            notes = [("DEF", "love(x) := the wish that x goes on", "①", 0.15,
                      "def. from lecture 3"),
                     ("LEM", "∀ me ∃ you : you ⊂ me.love", "②", 0.95,
                      "the existence part is the hard part"),
                     ("THM", "properly(love) ⇔ no condition", "③", 1.55,
                      "proof: remove every if"),
                     ("PRF", "∎ by induction on every day", "④", 2.15,
                      "base case: day one."),
                     ("COR", "love(me, you) = ∞ · you", "⑤", 2.75,
                      "so the exam has no wrong answer")]
            cy0 = py + 2 + hdr
            for i in range(len(notes)):
                yy = cy0 + i * step + step - 1
                if step >= 2 and yy < py + hgt - 3:
                    for xx in range(px + 6, px + lw - 1):
                        if cv.ch[yy][xx] == " ":
                            cv.put(xx, yy, "┄", rule)
            for i, (tag, txt, mark, off, note) in enumerate(notes):
                at = t_study + off
                yy = cy0 + i * step
                if yy > py + hgt - 3 or t < at:
                    continue
                cv.text(px + 3, yy, "%d" % (i + 1), shade(P["grey"], 0.35),
                        bg=paper)
                shown, typing = fx.typewriter("%-4s %s" % (tag, txt),
                                              t - at, 46.0)
                c = ink if i < 4 else mix(P["gold"], P["white"], 0.35)
                cv.text(px + 5, yy, shown, c, bg=paper)
                if typing and int(t * 14) % 2 == 0:
                    cv.put(px + 5 + sw(shown), yy, "▌", c, bg=paper)
                elif not typing:
                    cv.text(px + lw - 3, yy, mark, shade(P["gold"], 0.5),
                            bg=paper)
                if subs and step >= 2 and yy + 1 < py + hgt - 2:
                    if t >= at + 0.34:
                        sn, typing = fx.typewriter("↳ " + note,
                                                   t - (at + 0.34), 52.0)
                        cv.text(px + 6, yy + 1, sn,
                                shade(P["amber"], 0.38), bg=paper)
            # margin doodle: a heart next to the theorem
            if t >= t_study + 1.9:
                b = abs(math.sin((t - t_study) * 2.2))
                cv.put(px + lw - 6, cy0 + 2 * step,
                       "♥", shade(P["rose"], 0.3 + 0.45 * b))
            # ---------- fig. 1 -------------------------------------
            if show_fig:
                fx0 = px + lw + 2
                fwid = px + wid - 2 - fx0
                fy0 = py + 3
                fx0 += max(0, (fwid - 44) // 2)
                fwid = px + wid - 2 - fx0
                ay = fy0 + 9
                ax = fx0 + 3
                axc = mix(paper, P["amber"], 0.4)
                cv.text(fx0, fy0, "fig. 1 · love(x)",
                        shade(P["amber"], 0.35), bg=paper)
                cv.vline(ax, fy0 + 2, 8, "│", axc)
                cv.hline(ax, ay, min(fwid - 4, 18), "─", axc)
                cv.put(ax, ay, "└", axc)
                cv.put(ax - 2, ay, "0", shade(P["amber"], 0.3), bg=paper)


                cv.put(ax + min(fwid - 3, 19), ay, "▶",
                       shade(P["amber"], 0.4))
                cv.text(ax + min(fwid - 3, 20), ay, "x",
                        shade(P["amber"], 0.4), bg=paper)
                # dashed asymptote where x = you
                axx = ax + 12
                for yy in range(fy0 + 2, ay):
                    if cv.ch[yy][axx] == " ":
                        cv.put(axx, yy, "┊",
                               mix(paper, P["rose"], 0.30))
                k2 = ramp(t, t_proper - 0.15, t_proper + 1.3)
                pts = [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 3),
                       (7, 4), (8, 5), (9, 5), (10, 6), (11, 7)]
                npts = int(len(pts) * k2)
                for j, (dx, dy) in enumerate(pts[:npts]):
                    cv.put(ax + dx, ay - dy, "╱",
                           mix(P["amber"], P["white"], 0.25 +
                               0.3 * h01(j, 3)))
                if k2 > 0.98:
                    cv.put(ax + 12, ay - 8, "∞",
                           shade(P["rose"], 0.75))
                cv.put(ax + 6, ay + 1, "┴", axc)
                cv.put(ax + 11, ay + 1, "┴", axc)
                cv.text(ax + 5, ay + 2, "me", shade(P["amber"], 0.35),
                        bg=paper)
                cv.text(ax + 10, ay + 2, "you", shade(P["rose"], 0.45),
                        bg=paper)
                if t >= t_proper + 0.2:
                    sn, typing = fx.typewriter("as x → you, love(x) → ∞",
                                               t - (t_proper + 0.2), 40.0)
                    cv.text(fx0, ay + 4, sn, shade(P["amber"], 0.65),
                            bg=paper)
                if t >= t_proper + 0.9:
                    sn, typing = fx.typewriter("domain: x ∈ { me }",
                                               t - (t_proper + 0.9), 44.0)
                    cv.text(fx0, ay + 5, sn, shade(P["amber"], 0.4),
                            bg=paper)
                if hgt >= 19 and t >= t_proper + 1.4:
                    cv.text(fx0, ay + 7, "∀ all · ∃ exists · ⊂ subset",
                            shade(P["amber"], 0.28), bg=paper)
                    cv.text(fx0, ay + 8, "∎ Q.E.D. · ⇔ iff",
                            shade(P["amber"], 0.28), bg=paper)
                if False:
                    pass
                if hgt >= 22 and t >= t_study + 1.2 and \
                        cy0 + len(notes) * step + 6 < py + hgt - 3:
                    # a sticky note in the margin of the page
                    nx = px + 6
                    ny = cy0 + len(notes) * step + 1
                    note = ["love is not a limit,",
                            "it is the whole set.",
                            "        — me, 2:57"]
                    kk = ramp(t, t_study + 1.2, t_study + 1.7)
                    fg = shade(P["rose"], 0.55 * kk)
                    cv.hline(nx + 1, ny, 23, "─", shade(P["rose"], 0.3 * kk))
                    cv.text(nx, ny, "╭", shade(P["rose"], 0.3 * kk))
                    cv.text(nx + 24, ny, "╮", shade(P["rose"], 0.3 * kk))
                    for j, ln in enumerate(note):
                        cv.text(nx, ny + 1 + j, "│",
                                shade(P["rose"], 0.3 * kk))
                        cv.text(nx + 24, ny + 1 + j, "│",
                                shade(P["rose"], 0.3 * kk))
                    for j, ln in enumerate(note):
                        cv.text(nx + 2, ny + 1 + j, ln[:22], fg, bg=paper)
                    cv.text(nx, ny + 4, "╰", shade(P["rose"], 0.3 * kk))
                    cv.text(nx + 24, ny + 4, "╯",
                            shade(P["rose"], 0.3 * kk))
                    cv.hline(nx + 1, ny + 4, 23, "─",
                             shade(P["rose"], 0.3 * kk))
                if hgt >= 20 and fwid >= 30:
                    me = art.ME["tiny"]
                    mx = px + wid - 4 - max(len(r) for r in me)
                    my = py + hgt - 5
                    for j, ln in enumerate(me):
                        cv.text(mx, my + j, ln, shade(P["phos"], 0.75),
                                bg=paper)
                    cv.text(mx - 3, my + 1, "✎",
                            shade(P["amber"], 0.4), bg=paper)
            # ---------- footer: studied meter ----------------------
            k = ramp(t, t_study, t_proper + 1.5)
            yy = py + hgt - 2
            cv.text(px + 3, yy, "studied", inkd, bg=paper)
            bw2 = max(6, min(18, w - 46))
            fx.bar(cv, px + 11, yy, bw2, k, shade(P["amber"], 0.85), paper)
            if w >= 62:
                cv.text(px + 12 + bw2, yy,
                        "%4d pages · 187 exercises · 0 mistakes"
                        % int(4096 * k), inkd, bg=paper)
            cv.rtext(yy, " p. 012 / ∞ ", shade(P["amber"], 0.32), bg=paper,
                     right=px + wid - 2)
            me = art.ME["idle"]
            if w >= 64 and py + hgt + len(me) <= h - 1 and not show_fig:
                mx = w - 4 - max(len(r) for r in me) - 2
                my = py + hgt + 1
                for j, ln in enumerate(me):
                    cv.text(mx, my + j, ln, shade(P["phos"], 0.8))
                cv.text(mx - 2, my - 1, "✎", shade(P["amber"], 0.8))

        # ---------- 2 · the oral exam -------------------------------
        if t_q - 0.2 <= t < t_alg - 0.05 and compact:
            cv.text(2, 1, "examination · LOVE 101"[:w - 4],
                    shade(P["gold"], 0.8))
            qas = [("what is love", "love := Σ (you → me) / dt"),
                   ("how much", "∞  (unbounded above)"),
                   ("how long", "t := forever"),
                   ("why me", "no proof required"),
                   ("can you prove it", "∎  Q.E.D.")]
            answered = 0
            for i in range(len(qas)):
                if t >= t_q + 0.4 + i * 0.46:
                    answered = i + 1
            if answered:
                qq, aa = qas[answered - 1]
                cv.fill(0, 2, w, 2, " ", None, None)
                cv.text(2, 2, "? " + qq[:w - 6], shade(P["soft"], 0.95))
                cv.text(2, 3, aa[:w - 4], ink)
            yy = h - 3
            cv.fill(0, yy, w, 1, " ", None, None)
            cv.text(2, yy, "correct %d / %d" % (answered, len(qas)), inkd)
            if answered >= len(qas) and t >= t_ans + 0.4:
                cv.rtext(yy, "A: all of it.", mix(P["gold"], P["white"], 0.3),
                         right=w - 3)

        if t_q - 0.2 <= t < t_alg - 0.05 and not compact:
            hgt = h - 4
            py = 2
            fx.panel(cv, 2, py, w - 4, hgt, shade(P["gold"], 0.55), bg=paper,
                     title=" examination · LOVE 101 · candidate: me ")
            qas = [("what is love", "love := Σ (you → me) / dt"),
                   ("how much", "∞  (unbounded above)"),
                   ("how long", "t := forever"),
                   ("why me", "no proof required"),
                   ("can you prove it", "∎  Q.E.D.")]
            two = hgt >= 14
            step = 2 if two else 1
            nfit = max(1, (hgt - 4) // step)
            cv.text(4, py + 1, "candidate: me · 120 min · closed book",
                    shade(P["amber"], 0.34), bg=paper)
            if w >= 66:
                cv.rtext(py + 1, " instructions: answer all ",
                         shade(P["amber"], 0.26), bg=paper, right=w - 4)
            answered = 0
            for i, (qq, aa) in enumerate(qas[:nfit]):
                yy = py + 2 + i * step
                if yy >= py + hgt - 3:
                    break
                if t < t_q - 0.18 + i * 0.07:
                    continue
                cv.text(3, yy, "Q%d" % (i + 1), shade(P["gold"], 0.45),
                        bg=paper)
                cv.text(6, yy, qq, shade(P["soft"], 0.75), bg=paper)
                at_a = t_q + 0.4 + i * 0.46
                done = t >= at_a + sw(aa) / 40.0
                if done:
                    answered += 1
                if two:
                    if t < at_a:
                        cv.text(6, yy + 1, "⋯", shade(P["grey"], 0.4),
                                bg=paper)
                        for xx in range(8, min(w - 5, 8 + sw(aa))):
                            if cv.ch[yy + 1][xx] == " ":
                                cv.put(xx, yy + 1, "┄",
                                       mix(paper, P["gold"], 0.14))
                    else:
                        shown, typing = fx.typewriter(aa, t - at_a, 40.0)
                        cv.text(6, yy + 1, shown, ink, bg=paper)
                        if typing and int(t * 14) % 2 == 0:
                            cv.put(6 + sw(shown), yy + 1, "▎", ink, bg=paper)
                        elif not typing and w >= 52:
                            cv.put(w - 5, yy, "✓", shade(P["phos"], 0.85),
                                   bg=paper)
                elif not two and done and w >= 52:
                    cv.put(w - 5, yy, "✓", shade(P["phos"], 0.85), bg=paper)
            # lower half: the candidate's scribbles
            if hgt >= 20:
                sep = py + hgt - 8
                for xx in range(4, w - 4):
                    cv.put(xx, sep, "┄", mix(paper, P["gold"], 0.12))
                cv.text(4, sep + 1, "scratch work:",
                        shade(P["grey"], 0.42), bg=paper)
                cv.text(6, sep + 2, "me + you = ∞", shade(P["soft"], 0.6),
                        bg=paper)
                cv.text(6, sep + 3, "trace(♥) = me",
                        shade(P["soft"], 0.5), bg=paper)
                cv.put(6 + sw("trace(♥) = me") + 2, sep + 3, "♥",
                       shade(P["rose"], 0.45))
                cv.text(4, sep + 4, "sign", shade(P["amber"], 0.3), bg=paper)
                cv.text(9, sep + 4,
                        "me " + "_" * max(6, min(20, w - 26)),
                        shade(P["amber"], 0.3), bg=paper)
                if w >= 56:
                    cv.rtext(sep + 4, " marker: you ",
                             shade(P["amber"], 0.3), bg=paper, right=w - 4)
            # score + time bar
            yy = py + hgt - 2
            cv.text(4, yy, "correct %d / %d" % (answered, len(qas)), inkd,
                    bg=paper)
            if w >= 56:
                pct = "%d%%" % (100 * answered // len(qas))
                cv.rtext(yy, pct, shade(P["phos"] if answered >= len(qas)
                                        else P["amber"], 0.85), bg=paper,
                         right=w - 4)
            if hgt >= 17:
                kt = ramp(t, t_q, t_ans + 0.6)
                yb = py + hgt - 3
                cv.text(4, yb, "time", shade(P["amber"], 0.32), bg=paper)
                bw2 = max(6, min(20, w - 50))
                fx.bar(cv, 11, yb, bw2, 1.0 - 0.75 * kt,
                       shade(P["gold"], 0.7), paper)
                if w >= 58:
                    cv.text(12 + bw2, yb,
                            "%d min left" % int(120 - 90 * kt),
                            shade(P["amber"], 0.3), bg=paper)
            if t >= t_ans + 0.9:
                shown, typing = fx.typewriter("A: all of it.",
                                              t - (t_ans + 0.9), 18.0)
                cv.fill(0, min(h - 2, py + hgt + 1), w, 1, " ", None, None)
                cv.ctext(min(h - 2, py + hgt + 1), shown,
                         mix(P["gold"], P["white"], 0.25))

        # ---------- 3 · the algebraic expression --------------------
        if t_alg - 0.05 <= t < t_free - 0.05 and compact:
            lines = ["love := Σ ( you × me ) / | you |",
                     "∂me/∂you > 0", "∴ love(me, you) = ∞"]
            for i, txt in enumerate(lines):
                at = t_alg - 0.15 + i * 0.42
                if t < at or 2 + i > h - 3:
                    continue
                shown, typing = fx.typewriter(txt, t - at, 34.0)
                cv.fill(0, 2 + i, w, 1, " ", None, None)
                cv.ctext(2 + i, shown[:w - 4],
                         mix(P["gold"], P["white"], 0.2))
            if t >= t_alg + 1.1:
                bl = 0.55 + 0.45 * math.sin(t * 6.0)
                cv.fill(0, h - 2, w, 1, " ", None, None)
                cv.ctext(h - 2, "ACCEPTED", shade(P["phos"], bl))

        if t_alg - 0.05 <= t < t_free - 0.05 and not compact:
            bw = min(76, w - 6)
            bh = min(13, h - 6)
            x = cx - bw // 2
            y = max(2, (h - bh) // 2 - 1)
            fx.panel(cv, x, y, bw, bh, shade(P["gold"], 0.6), bg=paper,
                     title=" expression · the answer ")
            steps = [("1", "love := Σ ( you × me ) / | you |",
                      "per day, per you"),
                     ("2", "∂me/∂you > 0      lim you→me = ∞",
                      "I only grow where you are"),
                     ("3", "∴  love(me, you) = ∞ · you",
                      "unbounded, for all time")]
            if bh >= 11:
                cv.text(x + 3, y + 1, "step", shade(P["amber"], 0.28),
                        bg=paper)
                cv.text(x + 9, y + 1, "derivation",
                        shade(P["amber"], 0.28), bg=paper)
                for i, (sn, txt, ann) in enumerate(steps):
                    at = t_alg - 0.15 + i * 0.5
                    if t < at:
                        continue
                    yy = y + 2 + i * 3
                    cv.text(x + 3, yy, sn, shade(P["gold"], 0.6), bg=paper)
                    shown, typing = fx.typewriter(txt, t - at, 34.0)
                    cv.text(x + 9, yy, shown,
                            mix(P["gold"], P["white"], 0.2), bg=paper)
                    if typing and int(t * 14) % 2 == 0:
                        cv.put(x + 9 + sw(shown), yy, "▎",
                               mix(P["gold"], P["white"], 0.2), bg=paper)
                    if t >= at + 0.3:
                        an, _ = fx.typewriter("└ " + ann, t - (at + 0.3),
                                              48.0)
                        cv.text(x + 9, yy + 1, an,
                                shade(P["amber"], 0.34), bg=paper)
                if t >= t_alg + 1.0:
                    bl = 0.55 + 0.45 * math.sin(t * 6.0)
                    cv.text(x + 3, y + bh - 2, "ACCEPTED",
                            shade(P["phos"], bl), bg=paper)
                    if bw >= 50:
                        cv.rtext(y + bh - 2, "∎  graded by: you ",
                                 shade(P["amber"], 0.45), bg=paper,
                                 right=x + bw - 3)
            else:
                for i, (sn, txt, ann) in enumerate(steps):
                    at = t_alg - 0.15 + i * 0.5
                    if t < at:
                        continue
                    shown, typing = fx.typewriter(txt, t - at, 34.0)
                    cv.text(x + 3, y + 1 + i, shown,
                            mix(P["gold"], P["white"], 0.2), bg=paper)
            if t_alg + 1.0 <= t < t_alg + 2.0:
                fx.sparkle(cv, x + bw - 3, y + 2, t, P["gold"],
                           seed=int(t * 6), n=4, rad=4)
                fx.sparkle(cv, x + 2, y + bh - 4, t, P["gold"],
                           seed=int(t * 6) + 7, n=3, rad=3)

        # ---------- 4 · you are free, I am trapped ------------------
        if t >= t_free - 0.05:
            kv = ramp(t, t_free + 0.15, t_free + 0.72)     # you lifts
            kh = ramp(t, t_free + 0.68, t_free + 1.55)     # ...then drifts
            kt = ramp(t, t_trap + 0.1, t_love + 0.7)       # love closes in
            ey = max(3, h // 2 - 3) if not compact else 3
            left = "love := Σ ("
            yout = " you "
            right = " × me )"
            x0 = max(2, cx - (sw(left) + sw(yout) + sw(right)) // 2)
            sy0 = x0 + sw(left)
            cv.fill(0, ey, w, 1, " ", None, None)
            if kt <= 0.55:
                cv.text(x0, ey, left, ink)
                cv.text(sy0 + sw(yout), ey, right, ink)
                if kv > 0.2:
                    cv.text(sy0, ey, "∅",
                            shade(P["grey"], 0.7 * min(1.0, kv * 1.4)))
            else:
                s2 = "love := Σ ( ♥ me ♥ )"
                x2 = max(2, cx - sw(s2) // 2)
                cv.text(x2, ey, s2, ink)
                mp = x2 + sw("love := Σ ( ♥ ")
                for i in range(2):
                    cv.put(mp + i, ey - 1, "♥", shade(P["rose"], 0.8))
                    cv.put(mp + i, ey + 1, "◆", shade(P["rose"], 0.6))
            # `you` lifts out of the sum and drifts to the corner
            ex_ = max(6, w - 15)
            ey_ = max(1, ey - 5)
            yx = int(round(sy0 + kh * (ex_ - sy0)))
            yy = int(round(ey - kv * (ey - ey_)))
            for i in range(1, 4):
                kh2 = kh - i * 0.10
                if kh2 > 0.15:
                    cv.put(int(round(sy0 + kh2 * (ex_ - sy0))),
                           int(round(ey - kv * (ey - ey_))), "·",
                           shade(P["ice"], 0.4 * (1 - kh)))
            for rr in (yy, yy + 1):
                if 0 <= rr < h and rr != ey:
                    cv.fill(0, rr, w, 1, " ", None, None)
            cv.text(yx, yy, yout, mix(P["ice"], P["white"], 0.3 * (1 - kh)))
            if kh > 0.9 and w >= 40:
                cv.text(yx + 1, yy + 1, "free", shade(P["ice"], 0.55))
            # captions, in the order they are sung
            if t >= t_free + 0.15:
                s2 = ("you are free — you may leave any time"
                      if w >= 46 else "you are free")
                shown, typing = fx.typewriter(s2, t - (t_free + 0.15), 26.0)
                cv.fill(0, ey + 2, w, 1, " ", None, None)
                cv.ctext(ey + 2, shown, shade(P["ice"], 0.85))
            if t >= t_trap + 0.2 and w >= 36 and ey + 4 < h - 2:
                shown, typing = fx.typewriter("I am trapped",
                                              t - (t_trap + 0.2), 16.0)
                cv.fill(0, ey + 4, w, 1, " ", None, None)
                cv.ctext(ey + 4, shown, shade(P["pink"], 0.9))
            if t >= t_love + 0.1:
                kk = ramp(t, t_love + 0.1, t_love + 1.1)
                yy2 = min(h - 2, ey + 6)
                cv.fill(0, yy2 - 1, w, 3, " ", None, None)
                if h >= 18:
                    for i in range(7):
                        xx = 2 + int(h01(i, 11) * (w - 4))
                        cv.put(xx, yy2 + (i % 2) * 2 - 1, "♥",
                               shade(P["rose"], 0.45 * kk))
                cv.ctext(yy2, "trapped in lo-o-ove",
                         mix(P["rose"], P["white"], 0.35 * kk))

        if t > t_love + 0.3:
            fx.desaturate(cv, 0.5 * ramp(t, t_love + 0.3, self.t1), 0.9)
        # ---------- 6 · the vital sign of something trapped ----------
        if t >= t_free - 0.45 and h >= 13:
            ey = h - 5
            cv.hline(2, ey, w - 4, "─", shade(P["rose"], 0.16))
            for x in range(2, w - 2):
                u = (x * 0.052 - t * 0.92) % 1.0
                v = fx.ecg(u)
                yy = int(round(ey - v * 3.6))
                cv.put(x, yy, "▮" if v > 0.5 else "·",
                       mix(P["rose"], P["white"], 0.35 + 0.55 * min(1.0, v)))
            if h >= 20 and w >= 56:
                cv.text(2, ey - 4, "vitals · 1 heart · 130 bpm · still here",
                        shade(P["rose"], 0.45))
        anim.scanline(cv, t, 4, h - 2, mix(P["white"], P["gold"], 0.3),
                      speed=13.0, band=3, seed=51)
        fx.scanlines(cv, 0.85)
        fx.vignette(cv, 0.25)


# ==========================================================================
# 13 · SHUTDOWN — process terminated
# ==========================================================================

SD_PROCS = (
    ("0x1A0", "chant.exe", 6144),
    ("0x1A7", "you.sock", 1024),
    ("0x1B2", "god.ray", 512),
    ("0x1C4", "purr.out", 256),
    ("0x1D1", "love.tmp", 128),
    ("0x1F7", "me", 128),
)
SD_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class ShutdownScene(Scene):
    key = "shutdown"
    accent = "grey"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_exec = max(cue("Execution", i) for i in range(12))
        _shutdown(cv, t, w, h, self, t_exec)


def _shutdown(cv, t, w, h, sc, t_exec):
    top, bot = _rows(cv)
    space = bot - top + 1
    tl = t - sc.t0
    full = h >= 24 and w >= 88
    mid = h >= 19 and w >= 70
    comp = h >= 15 and w >= 52
    tiny = not (full or mid or comp)
    cx = w // 2
    cy = top + (bot - top) // 2 - 1
    if tiny:
        cy = top + 1 + max(0, space - 2) // 2
    acc = P["grey"]
    bgp = mix(P["black"], P["grey"], 0.055)
    t_cage = sc.t0 + 2.75
    t_dark = sc.t0 + 7.30
    t_whis = t_exec - 0.10
    dark = t >= t_dark
    whisper = t >= t_whis - 0.05
    nout = 0
    freed_tot = 0
    for _pid, _nm, _mem in SD_PROCS:
        if t >= sc.t0 + 0.55 + SD_PROCS.index((_pid, _nm, _mem)) * 0.30 + 0.42:
            nout += 1
            freed_tot += _mem

    # ---- the field never stops: dust, hex rain, faint carrier traces ------
    _dust(cv, t, acc, n=max(14, int(w * 0.22)), seed=23)
    _rain(cv, t, acc, step=(8 if w < 70 else 7), seed=29,
          dens=(2 if space < 9 else 2))
    if not tiny:
        _wave(cv, top, t, shade(acc, 0.5), amp=0, freq=0.2, speed=5.0,
              floor=top, ch="·", x0=1, x1=w - 1)
        if space >= 12:
            _wave(cv, bot - 2, t, shade(acc, 0.55), amp=1, freq=0.21,
                  speed=2.7, floor=top, ch="·", x0=1, x1=w - 1)
    if space >= 10 and w >= 52:
        for j in range(top, bot + 1):
            v = int(h01(j, int(t * 13), 7) * 16)
            cv.put(w - 2, j, "%X" % v,
                   shade(acc, 0.20 + 0.16 * (j % 4 == 0)))

    # ---- A · the cage: processes are terminated one by one ----------------
    if t < t_cage + 0.30:
        ph = 0
        if ph_ := (space >= 12 and w >= 60):
            th = min(space - 1, 13)
            fx.panel(cv, 2, top, w - 4, th, shade(P["cyan"], 0.65), bgp,
                     title=" ps -ef | grep me ",
                     title_fg=shade(P["cyan"], 0.9))
            cv.text(4, top + 1, _fit("PID     NAME          STATE     MEM", w - 8),
                    shade(P["cyan"], 0.75), bgp)
            cv.hline(3, top + 2, min(w - 6, w - 6), "─",
                     shade(P["cyan"], 0.3), bgp)
            nrow = max(1, min(len(SD_PROCS), th - 6))
            freed = 0
            for i in range(nrow):
                pid, name, mem = SD_PROCS[i]
                te = sc.t0 + 0.55 + i * 0.30
                if t < te:
                    st, st_fg = "RUN", shade(P["soft"], 0.85)
                elif t < te + 0.42:
                    st, st_fg = "TERM", shade(P["amber"], 0.95)
                else:
                    st, st_fg = "exited", shade(P["grey"], 0.55)
                    freed += mem
                y = top + 3 + i
                cv.text(4, y, _fit("%-7s %-12s %-7s %5d KiB" % (
                    pid, name, st, mem), w - 10), shade(P["soft"], 0.78), bgp)
                cv.text(4 + 21, y, st, st_fg, bgp)
            if freed > 0:
                freed = min(8192, freed)
        elif space >= 6:
            # narrow: only the memory counter survives
            mx = sc.t0 + 1.1
            kf = ramp(t, mx, t_cage)
            freed = int(8192 * kf)
        if space >= 13 and w >= 60:
            y = top + min(len(SD_PROCS), th - 6) + 3
            anim.meter(cv, 4, y, "free", 100.0 * freed / 8192.0, 100.0,
                       max(5, min(16, w - 34)),
                       shade(P["cyan"], 0.9), bg=bgp,
                       dim_fg=shade(P["grey"], 0.45))
            anim.counter(cv, 4, y + 1, "freed", freed, "%5d KiB",
                         shade(P["ice"], 0.85), bg=bgp,
                         dim_fg=shade(P["grey"], 0.45))
        # the cage itself: bars retract upwards, the door finally opens
        if w >= 74 and space >= 12:
            bx0 = max(40, w - 28)
            kbar = ramp(t, sc.t0 + 0.35, t_cage)
            for i in range(5):
                x = bx0 + i * 5
                y1 = bot - 6 - int(kbar * (space - 9))
                if y1 > top + 1:
                    cv.vline(x, top + 1, y1 - top, "┃",
                             shade(P["grey"], 0.42 - 0.1 * (i % 2)))
                cv.put(x, max(top, y1), "╻",
                       shade(P["grey"], 0.5 * (1 - kbar)))
        # termination flash on the beat
        if any(abs(t - (sc.t0 + 0.55 + i * 0.3 + 0.42)) < 0.09
               for i in range(6)):
            cv.hline(2, max(top, bot - 4), w - 5, "▔",
                     shade(P["white"], 0.12))

    # ---- B · the shell comes back, logs the exit -------------------------
    elif t < t_dark:
        ph = 1
        ybase = max(top + 1, bot - 8)
        lines = (
            (sc.t0 + 2.90, "$ me.execute(love);", P["phos"]),
            (sc.t0 + 3.50, "> attach 0x1F7 ..................... ok", P["ice"]),
            (sc.t0 + 4.15, "[Process finished with exit code 0]", P["grey"]),
            (sc.t0 + 4.85, "> love: no such file or directory", P["red"]),
        )
        for i, (at, txt, fg) in enumerate(lines):
            if t < at - 0.12:
                continue
            shown, typ = fx.typewriter(txt, t - at, 38.0)
            yy = ybase + i
            if yy <= bot - 3:
                cv.text(2, yy, _fit(shown, w - 6), shade(fg, 0.9))
                if typ and int(t * 14) % 2 == 0:
                    cv.put(2 + sw(shown), yy, "▮", shade(fg, 0.8))
        spin = SD_SPIN[int(t * 12) % len(SD_SPIN)]
        if space >= 9:
            cv.text(w - 9, ybase, "%s%02X" % (spin, int(h01(int(t * 9), 3) * 256)),
                    shade(P["amber"], 0.8))
        # core dump bars: memory being written out, off to the right
        if space >= 9 and w >= 64:
            kd = ramp(t, sc.t0 + 4.0, t_dark)
            for i in range(min(7, (w - 46) // 3)):
                hgt = 1 + int((space - 10) * 0.30 *
                              (0.5 + 0.5 * math.sin(t * 3.1 + i * 1.3)))
                for j in range(hgt):
                    cv.put(w - 40 + i * 3, bot - 4 - j, "█",
                           shade(P["cyan"], 0.20 + 0.05 * j + 0.2 * kd))
        if 0 <= t - (sc.t0 + 6.6) < 1.1:
            kk = 1.0 - (t - sc.t0 - 6.6) / 1.1
            cv.hline(2, cy, int((w - 5) * kk), "─",
                     shade(P["grey"], 0.35 * (1 - kk)))

    # ---- C · dark: nothing runs, but the machine is still breathing ------
    else:
        ph = 2
        # the ghost of the last thing that executed
        ghost = "world.execute(me);"
        last = t_dark - sc.t0
        ga = max(0.0, 0.55 - 0.16 * (t - t_dark))
        if ga > 0.02:
            cv.ctext(cy - 2, ghost, shade(P["phos"], ga))
        # phosphor decay: a band of dying cells crawls down the field
        yb = top + 2 + int((t * 2.3) % max(1, space - 8))
        for x in range(1, w - 1):
            if h01(x, yb, 13) < 0.72:
                cv.put(x, yb, "▒", shade(acc, 0.16))
            if h01(x, yb, 11) < 0.16:
                cv.put(x, min(bot, yb + 1), "░", shade(acc, 0.14))
        # two more traces: the signal that refuses to stop
        if space >= 10:
            _wave(cv, max(top + 1, cy - 4), t, shade(acc, 0.42), amp=0,
                  freq=0.24, speed=3.1, floor=top, ch="·", x0=1, x1=w - 1)

        # a cursor that has nothing left to say
        if int(t * 1.6) % 2 == 0:
            cv.put(2, cy, "▮", shade(P["phos"], 0.75))
        cv.text(4, cy, "heap 0x%04X  idle 0x%04X  irq %d" % (
            int(h01(int(t * 8), 5) * 65535), int(h01(int(t * 6), 9) * 65535),
            int(h01(int(t * 10), 13) * 9)),
            shade(P["grey"], 0.55))
        # the whisper: the only word left
        if whisper:
            age = t - t_whis
            shown, typ = fx.typewriter("...execution.", age, 12.0)
            wx = max(1, cx - 13)
            wy = min(cy + 2, bot)
            cv.text(wx, wy, shown, shade(P["white"], 0.85))
            if 0 <= age < 0.22:
                cv.hline(2, wy, w - 5, "▁", shade(P["white"], 0.22))
            if typ and int(t * 10) % 2 == 0:
                cv.put(wx + sw(shown), wy, "▮", shade(P["white"], 0.8))
            if 0 <= t - t_exec < 0.42:
                kk = 1.0 - (t - t_exec) / 0.42
                for y in range(top, bot + 1):
                    if h01(y, int(t * 40), 17) < 0.55 * kk:
                        cv.hline(2, y, w - 5, "─", shade(P["white"], 0.30 * kk))
                cv.put(cx, min(cy + 2, bot), "█", shade(P["white"], 0.9 * kk))

    # ---- the bottom instrument -------------------------------------------
    if space >= 9:
        log = ("shutdown.log · phase %d · procs %d/6 · freed %d KiB · "
               "0x1F7 %s · " % (ph, 6 - nout, freed_tot,
                                "exited" if nout >= 6 else "terminating"))
        anim.ticker(cv, bot, log, t, speed=19.0, fg=shade(acc, 0.55),
                    x0=2, x1=w - 3)
        if full:
            hexs = " ".join("%04X" % int(h01(int(t * 11) + i, 37) * 65535)
                            for i in range(14))
            anim.ticker(cv, bot - 1, "heap." + hexs, t, speed=15.0,
                        fg=shade(P["violet"], 0.42), x0=2, x1=w - 26)
    if space >= 10:
        st = ("01 cage" if t < t_cage else
              "02 shell" if t < t_dark else
              "03 idle" if t < t_whis else "04 execution")
        cv.put(2, bot - 3, "▸", shade(P["phos"], 0.95))
        cv.text(4, bot - 3, _fit("%s   t%+06.2f   pid 0x1F7" % (
            st, tl - 15.4), w - 8), shade(P["soft"], 0.7))

    # tiny screens: keep the cursor alive and nothing else
    if tiny:
        if int(t * 1.8) % 2 == 0:
            cv.put(max(2, w // 2), cy, "▮", shade(P["phos"], 0.7))

    if not tiny:
        fx.scanlines(cv, 0.9)
        fx.vignette(cv, 0.18)
# ==========================================================================
# 14 · END CARD
# ==========================================================================

EC_A = "0123456789ABCDEF"
EC_B = "+*·/\\|<>[]{}"


def _ec_noise(cv, y, t, w, fg, seed=0):
    """Hex that is rewritten every frame: the machine is still talking."""
    kk = int(t * 8.0)
    for x in range(1, w - 1):
        v = int(h01(x, kk, seed) * 65536)
        cv.put(x, y, EC_A[(v >> 5) & 15],
               shade(fg, 0.24 + 0.30 * h01(x, kk, seed + 3)))


class EndCardScene(Scene):
    key = "endcard"
    accent = "grey_dim"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        _endcard(cv, t, w, h, self)


def _endcard(cv, t, w, h, sc):
    top, bot = _rows(cv)
    space = bot - top + 1
    full = h >= 22 and w >= 84
    mid = h >= 17 and w >= 66
    comp = h >= 13 and w >= 46
    tiny = not (full or mid or comp)
    cx = w // 2
    cy = top + (bot - top) // 2 - 1
    if tiny:
        cy = top + 1 + max(0, space - 2) // 2
    dim = P["grey_dim"]
    t_as = sc.t0 + 0.16
    t_exit = sc.t0 + 1.55
    t_off = sc.t0 + 3.55
    t_end = sc.t0 + 4.97

    # ---- the noise it makes on the way out --------------------------------
    if space >= 13 and not tiny:
        _ec_noise(cv, top, t, w, dim, seed=1)
        _ec_noise(cv, top + 1, t, w, shade(dim, 0.8), seed=2)
        _ec_noise(cv, top + 2, t, w, shade(dim, 0.6), seed=5)
        _ec_noise(cv, bot - 1, t, w, shade(dim, 0.8), seed=3)
        _ec_noise(cv, bot, t, w, dim, seed=4)
    elif not tiny:
        _ec_noise(cv, top, t, w, dim, seed=1)
        _ec_noise(cv, bot, t, w, dim, seed=3)
    # loose glyphs that never settle
    for i in range(10 if not tiny else 4):
        x = 1 + int(h01(i, int(t * 7), 5) * (w - 3))
        y = top + 2 + int(h01(i, int(t * 5), 6) * max(1, space - 4))
        if top + 2 <= y < bot - 1 and top + 2 <= y:
            cv.put(x, y, EC_B[i % len(EC_B)],
                   shade(dim, 0.28 + 0.28 * h01(i, int(t * 9), 7)))

    # ---- the title assembles out of that noise ---------------------------
    title = "world.execute(me);"
    ty = (cy - 4) if space >= 15 else (cy - 2)
    kk = ramp(t, t_as, t_as + 1.28)
    tx = max(1, cx - len(title) // 2)
    if tiny or ty - top < 3:
        cv.ctext(ty, title if sw(title) <= w - 4 else "execute(me);",
                 shade(P["phos"], 0.3 + 0.6 * kk))
    elif kk < 1.0:
        anim.assemble(cv, tx, ty, [title], kk,
                      shade(P["phos"], 0.30 + 0.60 * kk), seed=9,
                      spread=6, snap=0.55, y_min=top)
    else:
        cv.ctext(ty, title, shade(P["phos"], 0.92))
        cv.hline(max(1, cx - 9), ty + 1, 18, "─", shade(P["grey"], 0.40))

    # ---- uptime counts the whole song out --------------------------------
    up = 211.97 * min(1.0, max(0.0, (t - sc.t0) / (t_end - sc.t0)))
    sec = int(up)
    stamp = "%02d:%02d.%d" % (sec // 60, sec % 60, int((up - sec) * 10))
    if space >= 12 and w >= 52:
        cv.text(2, cy - 2, "$", shade(P["phos"], 0.8))
        shown, typ = fx.typewriter("exit 0", t - t_exit, 13.0)
        cv.text(4, cy - 2, shown, shade(P["phos"], 0.9))
        if typ and int(t * 8) % 2 == 0:
            cv.put(4 + sw(shown), cy - 2, "▮", shade(P["phos"], 0.75))
        cv.rtext(cy - 2, _fit("uptime %s" % stamp, w - 6),
                 shade(P["ice"], 0.75), right=w - 3)
    # a thin pulse where the heart used to be
    if not tiny:
        p = 0.5 + 0.5 * math.sin((t - sc.t0) * 6.0)
        cv.put(cx, cy, "·" if p < 0.5 else "●",
               shade(P["phos"], 0.25 + 0.4 * p))

    # ---- the credits, typed one line at a time ---------------------------
    creds = (
        ("MiLi  ·  Miracle Milk (2016)", sc.t0 + 1.95, P["grey"], 0.85),
        ("thank you for executing me", sc.t0 + 2.42, P["grey_dim"], 1.0),
        ("感谢你执行我", sc.t0 + 2.92, P["grey_dim"], 1.0),
    )
    for i, (txt, at, fg, br) in enumerate(creds):
        yy = cy + 2 + i
        if yy > bot - 2 or t < at - 0.10:
            continue
        shown, typ = fx.typewriter(txt, t - at, 26.0)
        if tiny:
            cv.ctext(yy, shown, shade(fg, br))
        else:
            cv.ctext(yy, shown, shade(fg, br))
        if typ and int(t * 9) % 2 == 0:
            cv.put(cx + sw(shown) // 2 + 1, yy, "▮", shade(fg, br * 0.8))

    # ---- the status and the roll, still running --------------------------
    if space >= 11:
        anim.ticker(cv, bot - 2, "credits.roll · MiLi · Miracle Milk (2016) · "
                    "thank you for executing me · gan xie ni zhi xing wo · "
                    "world.execute(me); · exit 0 · ", t, speed=17.0,
                    fg=shade(dim, 2.2), x0=2, x1=w - 3)
    if space >= 14:
        sy_ = min(cy + 5, bot - 3)
        if sy_ != bot - 2:
            cv.put(2, sy_, "▸", shade(P["phos"], 0.9))
            cv.text(4, sy_, _fit("pid 1 · uptime %s · exit 0 · %d frames" % (
                stamp, int((t - sc.t0) * 30)), w - 8),
                shade(P["grey"], 0.65))

    # ---- power off: the picture collapses to a line, then to a dot -------
    if t >= t_off:
        kv = ramp(t, t_off, t_off + 0.40)
        keep = max(1, int(round(space * (1.0 - kv))))
        y0 = cy - (keep - 1) // 2
        y1 = y0 + keep - 1
        for y in range(top, bot + 1):
            if y < y0 or y > y1:
                cv.fill(0, y, w, 1, " ", None, None)
        kh = ramp(t, t_off + 0.40, t_off + 0.84)
        if kh > 0.0:
            kw = max(1, int(round((w - 2) * (1.0 - kh))))
            x0 = cx - kw // 2
            x1 = x0 + kw - 1
            for y in range(top, bot + 1):
                if y < y0 or y > y1:
                    continue
                if x0 > 1:
                    cv.fill(0, y, max(0, x0), 1, " ", None, None)
                if x1 < w - 2:
                    cv.fill(max(0, x1 + 1), y, max(0, w - 1 - x1),
                            1, " ", None, None)
            if kh >= 0.999:
                for y in range(top, bot + 1):
                    cv.fill(0, y, w, 1, " ", None, None)
                kd = ramp(t, t_off + 0.84, t_off + 1.14)
                br = 1.0 - 0.55 * kd
                cv.put(cx, cy, "█" if kd < 0.45 else ("▪" if kd < 0.8 else "·"),
                       shade(P["white"], br))
                if kd < 0.55:
                    cv.hline(max(1, cx - 6), cy, 13, "─",
                             shade(P["white"], 0.35 * (1 - kd / 0.55)))
            else:
                cv.hline(max(1, x0), y0, max(0, kw), "▁",
                         shade(P["white"], 0.55))
        elif kv >= 0.999:
            cv.hline(max(1, y0 and 1), y0, max(0, w - 2), "▁",
                     shade(P["white"], 0.35))

    if not tiny:
        fx.scanlines(cv, 0.88)
        fx.vignette(cv, 0.24)
