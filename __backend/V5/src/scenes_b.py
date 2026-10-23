"""Scenes: verse 3, pre-chorus 2, chorus 2, bridge, build."""

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


def _v3_anim_rows(form, space, t):
    """Form rows with per-frame life: the cat blinks (●↔◉) and twitches its
    whiskers, god's halo rays slide around the crown.  Pure function of t."""
    rows = _v3_rows(form, space)
    if form == "cat":
        bph = (t * 0.37) % 1.0
        if bph < 0.055:
            eye = "‿"                     # a real blink, twice a minute-ish
        elif int(t * 3.1) % 5 == 0:
            eye = "◉"                     # wide open, startled
        else:
            eye = "●"
        tw = int(t * 5.0) % 2 == 0
        out = []
        for ln in rows:
            ln = ln.replace("●", eye)
            if tw:
                ln = ln.replace("╱╲", "╲╱")
            out.append(ln)
        return out
    if form == "god":
        o = int(round(1.5 + 1.5 * math.sin(t * 1.3)))
        crown = "✦" + " " * o + "▄▄▄▄▄▄▄" + " " * o + "✦"
        out = list(rows)
        if out:
            pad = max(0, V3_BOX - 3 - sw(crown))
            out[0] = " " * 3 + crown + " " * pad
        return out
    return rows


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
    """IF / THEN, typed above the object like a label on a stage.

    The machine cannot let a fulfilled promise rest: the moment a gift has
    landed, both lines rewind-delete (cursor blinking, backspace-speed),
    and the rows sit empty until the next form arrives.  Compulsive giving:
    delete the offer, become the next thing, offer again.
    """
    hy = sy - 2
    x0 = 33 if w >= 78 else 4
    maxw = w - x0 - 3
    if hy < top or maxw < 20:
        return
    # when this form's grant finishes landing, its contract gets shredded
    done_at = cues_then[idx] + 1.35
    lbl = "[only] god" if idx == 3 else V3_PAIRS[idx][0]
    s_if = 'IF   me := "%s"' % lbl
    t0 = cues_if[idx] - (0.30 if idx == 0 else 0.0)
    vis, _k, ph = anim.type_loop(
        t, t0, s_if, cycles=1, cps=30.0,
        hold=max(0.25, done_at - t0 - len(s_if) / 30.0),
        wipe=0.26, gap=9.0, del_last=True)
    if vis:
        dim = 0.6 if ph == "wipe" else 0.0
        cv.text(x0, hy, vis[:maxw],
                shade(mix(P["ice"], P["grey"], dim), 0.80))
        io = vis.find("[only]")
        if io >= 0 and io + 6 <= len(vis) and io < maxw:
            cv.text(x0 + io, hy, vis[io:io + 6][:maxw - io], P["magenta"])
        if ph in ("type", "wipe") and int(t * 12) % 2 == 0:
            cv.put(min(w - 3, x0 + len(vis)), hy, "▮",
                   shade(P["ice"], 0.7 if ph == "type" else 0.45))
    a_th = cues_then[idx] - 0.25
    s_th = "THEN " + V3_THEN[idx]
    vis2, _k2, ph2 = anim.type_loop(
        t, a_th, s_th, cycles=1, cps=32.0,
        hold=max(0.20, done_at - a_th - len(s_th) / 32.0),
        wipe=0.26, gap=9.0, del_last=True)
    if vis2:
        col = P["gold"] if idx == 3 else P["phos"]
        dim = 0.6 if ph2 == "wipe" else 0.0
        cv.text(x0, hy + 1, vis2[:maxw],
                shade(mix(col, P["grey"], dim), 0.78))
        # every gift is for you: the word itself carries the accent
        iy = vis2.find("you")
        if iy >= 0 and iy < maxw:
            cv.text(x0 + iy, hy + 1,
                    vis2[iy:iy + 3][:max(0, maxw - iy)], P["pink"])
        if ph2 in ("type", "wipe") and int(t * 12) % 2 == 0:
            cv.put(min(w - 3, x0 + len(vis2)), hy + 1, "▮", shade(col, 0.7))


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
        # the drip lands: a tiny splash kicks off the diamond
        if u > 0.90:
            kk = (u - 0.90) / 0.10
            for d in range(4):
                a = h01(i, d, 7) * 6.283
                rr = 1.0 + 2.6 * kk
                sxp = youx - 3 + int(round(math.cos(a) * rr))
                syp = dy_ + int(round(math.sin(a) * rr * 0.55))
                if top <= syp <= bot:
                    cv.put(sxp, syp, "·" if kk < 0.6 else "˙",
                           shade(P["violet"], 0.85 * (1.0 - kk)))
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
        # where the radical dies on the shell, its cost is written up
        if 0.70 < u < 0.94 and int(t * 9 + i) % 2 == 0:
            dx_ = youx + int(round(math.cos(a) * 9.0))
            dy2 = dy_ + int(round(math.sin(a) * 9.0 * 0.55))
            if top <= dy2 <= bot:
                cv.put(dx_, dy2, "0123456789ABCDEF"[int(h01(i, 91) * 16)],
                        shade(P["red"], 0.5 + 0.5 * (0.94 - u) / 0.24))


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
        sway = 0.22 * math.sin(t * 0.9)
        for i in range(26):
            a = math.pi + i * math.pi / 25.0 + sway
            xp = cx + int(round(math.cos(a) * 13))
            yp = cy - 3 + int(round(math.sin(a) * 9))
            if top <= yp <= bot:
                cv.put(xp, yp, "✦" if i % 4 == 0 else "·",
                       shade(P["gold"], (0.3 + 0.6 * kk)
                             * (0.55 + 0.45 * math.sin(t * 3 + i))))
        # the choir: three ✦ orbiting the crown while the witness is read
        for c in range(3):
            ang = t * 1.6 + c * 2.094
            xp = cx + int(round(math.cos(ang) * 11))
            yp = cy - 3 + int(round(math.sin(ang) * 7))
            if top <= yp <= bot:
                cv.put(xp, yp, "✦",
                       shade(P["gold"], 0.45 + 0.40 *
                             (0.5 + 0.5 * math.sin(t * 3.0 + c))))
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
    gk = [0.0, 0.0, 0.0, 0.0]              # per-gift transfer progress 0..1
    for i in range(4):
        a = cues_then[i]
        b = (cues_if[i + 1] - 0.12) if i < 3 else sc.t1
        gk[i] = min(1.0, max(0.0, (t - a) / max(0.15, b - a)))
    gifts = sum(gk)
    transferred = 0
    for i in range(4):
        transferred += int(gk[i] * 512)

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
        # the [only] motif: the god row's "only" carries the scene accent
        # (row text and layout stay exactly as they were)
        if ph_ >= 9:
            cv.text(px_ + 6, py_ + 5, "only",
                    P["magenta"] if idx == 3 else shade(P["magenta"], 0.55),
                    bgp)
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
            # per-gift transfer-rate sparklines: each row of the table now
            # shows its own live rate instead of one shared hazard stripe
            sx_ = px_ + 2
            for i in range(4):
                done = t >= cues_then[i]
                if done or (i == idx and gk[i] > 0.02):
                    amp = 0.35 + 0.65 * gk[i]
                else:
                    amp = 0.12
                col = (shade(P["phos"], 0.55) if done else
                       shade(P["violet"], 0.95) if i == idx else
                       shade(P["grey"], 0.45))
                cv.put(sx_, py_ + 6, "%d" % (i + 1), shade(P["grey"], 0.6), bgp)
                for j in range(4):
                    v = amp * (0.5 + 0.5 * math.sin(t * 5.0 + j * 1.3 + i * 2.1))
                    cv.put(sx_ + 1 + j, py_ + 6,
                           "▁▂▃▄▅▆▇"[min(6, int(v * 6.99))], col, bgp)
                sx_ += 6
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
                _v3_spr(c2, _v3_anim_rows(prev, spr_space, t), cx, sy,
                        _v3_colf(prev, t))
            elif k >= 1.0:
                _v3_spr(c2, _v3_anim_rows(cur, spr_space, t), cx, sy,
                        _v3_colf(cur, t))
            else:
                anim.dissolve(c2, t, a0, a0 + 0.62,
                              lambda c, f=prev: _v3_spr(
                                  c, _v3_anim_rows(f, spr_space, t), cx, sy,
                                  _v3_colf(f, t)),
                              lambda c, f=cur: _v3_spr(
                                  c, _v3_anim_rows(f, spr_space, t), cx, sy,
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
            # the [only] motif: the last contract brackets its own
            # exclusivity, the way the machine says it
            lbl = "[only] god" if idx == 3 else V3_PAIRS[idx][0]
            s1, typ1 = fx.typewriter(
                'if (me is %s) yield "%s";' % (lbl, V3_PAIRS[idx][1]),
                age, 34.0)
            cv.text(3, cy_, _fit(s1, w - 6), shade(P["ice"], 0.88))
            io = s1.find("[only]")
            if io >= 0 and io + 6 <= len(s1):
                cv.text(3 + io, cy_, "[only]", P["magenta"])
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
        io = s3.find("only")
        if idx == 3 and io >= 0:
            cv.text(4 + io, bot - 3, "only", P["magenta"])

    fx.scanlines(cv, 0.88)
    fx.vignette(cv, 0.22)


# ==========================================================================
# 6 · PRE-CHORUS 2 — switch gender / time / role / trance
# ==========================================================================

class Pre2Scene(Scene):
    key = "pre2"
    accent = "violet"

    SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        top, bot = _rows(cv)
        space = bot - top + 1
        cx = w // 2
        cy = top + space // 2
        t_gender = cue("Switch my gender")
        t_fm = cue("To F to M")
        t_whatever = cue("And then do whatever")
        t_ampm = cue("From AM to PM")
        t_role = cue("Oh switch my role")
        t_sm = cue("To S to M")
        t_enter = cue("So we can enter")
        t_trance = cue("The trance the trance")

        # ---- the machine's ground hum: it never stops rewriting itself ----
        _rain(cv, t, P["violet"], step=(8 if w < 70 else 7), seed=47, dens=2)
        stage = ("gender" if t < t_whatever else
                 "clock" if t < t_role else
                 "role" if t < t_enter else "trance")
        anim.ticker(cv, bot,
                    "me.conf · mode=%s · identity: polymorphic · rewriting… · "
                    "do not unplug · " % stage,
                    t, speed=16.0, fg=shade(P["violet"], 0.55),
                    x0=2, x1=w - 3)

        # ---------- gender switch: /etc/me.conf edited as a live diff ------
        a = fade_window(t, t_gender - 0.2, t_whatever + 0.3, 0.4, 0.4)
        if a > 0.01:
            def gender(cv2):
                k = ramp(t, t_gender + 0.2, t_fm + 1.9)     # F -> M
                # once it has switched, it keeps switching: the machine can
                # never make up its mind, so the slider never comes to rest
                kp = k if k < 0.999 else 0.5 + 0.5 * math.sin(
                    (t - t_fm) * 1.7)
                cur = "M" if kp > 0.5 else "F"
                old = "F" if cur == "M" else "M"
                big = space >= 14 and w >= 56
                pw = min(w - 4, 64)
                ph = 13 if big else (9 if space >= 10 and w >= 44 else 0)
                spin = self.SPIN[int(t * 10) % 10]
                if ph:
                    px = (w - pw) // 2
                    py = top + max(0, (space - ph) // 2)
                    fx.panel(cv2, px, py, pw, ph, shade(P["violet"], 0.9),
                             title=" /etc/me.conf ")
                    cv2.text(px + 2, py + 2, "$ me --set gender=%s" % cur,
                             shade(P["phos"], 0.9))
                    # the live diff: one line struck out, one line landing
                    if t >= t_gender + 0.45:
                        cv2.text(px + 2, py + 3, "- gender = %s" % old,
                                 shade(P["red"], 0.75))
                    if t >= t_fm - 0.1:
                        cv2.text(px + 2, py + 4, "+ gender = %s" % cur,
                                 shade(P["cyan"], 0.9))
                    # the apply spinner: it never finishes applying
                    cv2.text(px + 2, py + 5, "apply %s 0x%02X" % (
                        spin, int(0x46 + (0x4D - 0x46) * kp)),
                        shade(P["grey"], 0.8))
                    if big:
                        fy0 = py + 6
                    else:
                        fy0 = 0
                    # chromosome + symbols: one instrument row
                    yy = py + ph - 2
                    cv2.text(px + 2, yy, "XX", shade(
                        P["pink"] if kp < 0.5 else P["grey"], 0.9))
                    cv2.text(px + 5, yy, "⇄", shade(P["grey"], 0.6))
                    cv2.text(px + 7, yy, "XY", shade(
                        P["cyan"] if kp > 0.45 else P["grey"], 0.9))
                    idxs = int(t * 1.6) % 3
                    for i, sm in enumerate(("♀", "⚥", "♂")):
                        cv2.text(px + 12 + i * 3, yy, sm,
                                 P["white"] if i == idxs else
                                 shade(P["violet"], 0.5))
                    cv2.text(px + 23, yy, "gender: undefined",
                             shade(P["violet"], 0.75))
                else:
                    px, py, pw, ph = max(1, (w - 34) // 2), top, min(w - 2, 36), 0
                    cv2.text(px, py, "$ me --set gender=%s" % cur,
                             shade(P["phos"], 0.9))
                    cv2.text(px, py + 1, "-%s + %s %s" % (old, cur, spin),
                             shade(P["grey"], 0.8))
                    fy0 = 0
                    yy = py + 1
                # big F dissolves into big M, cell by cell
                fcols = [" ███", "█   ", "███ ", "█   ", "█   "]
                mcols = ["█   █", "██ ██", "█ █ █", "█   █", "█   █"]
                if fy0 and fy0 + 5 <= py + ph - 1:
                    for j in range(5):
                        for i, ch in enumerate(fcols[j]):
                            if ch == " ":
                                continue
                            aa = max(0.0, 1.0 - kp * 1.15)
                            if aa > 0.03 and h01(i, j, 77) < 0.35 + aa * 0.65:
                                cv2.put(px + 3 + i, fy0 + j, ch,
                                        shade(P["pink"], aa))
                        for i, ch in enumerate(mcols[j]):
                            if ch == " ":
                                continue
                            bb = max(0.0, (kp - 0.12) * 1.15)
                            if bb > 0.03 and h01(i, j, 78) < 0.35 + bb * 0.65:
                                cv2.put(px + pw - 8 + i, fy0 + j, ch,
                                        shade(P["cyan"], bb))
                    # slider between the two letters — the one that keeps
                    # oscillating long after the edit "finished"
                    sx0, sx1 = px + 10, px + pw - 11
                    sy = fy0 + 2
                    if sx1 > sx0 + 4:
                        cv2.hline(sx0, sy, sx1 - sx0, "═",
                                  shade(P["grey"], 0.45))
                        kx = sx0 + int((sx1 - sx0) * min(1.0, max(0.0, kp)))
                        cv2.put(kx, sy, "●", mix(P["pink"], P["cyan"], kp))
                        cv2.put(kx, sy - 1, "▲", shade(P["white"], 0.8))
                        cv2.put(sx0, sy, "┤", shade(P["pink"], 0.7))
                        cv2.put(sx1, sy, "├", shade(P["cyan"], 0.7))
                elif ph:
                    # compact panel: the slider alone carries the switch
                    sy = py + 6
                    sx0, sx1 = px + 3, px + pw - 5
                    if sx1 > sx0 + 6:
                        cv2.text(sx0, sy, "F", shade(P["pink"], 0.9))
                        cv2.text(sx1, sy, "M", shade(P["cyan"], 0.9))
                        cv2.hline(sx0 + 2, sy, sx1 - sx0 - 3, "═",
                                  shade(P["grey"], 0.45))
                        kx = sx0 + 2 + int((sx1 - sx0 - 3) *
                                           min(1.0, max(0.0, kp)))
                        cv2.put(kx, sy, "●", mix(P["pink"], P["cyan"], kp))
                        cv2.put(kx, sy - 1, "▲", shade(P["white"], 0.8))
                else:
                    # tiny: the slider is the whole panel
                    sx0, sx1 = px + 1, px + pw - 2
                    sy = yy + 1 if yy + 1 <= bot else yy
                    if sx1 > sx0 + 4 and sy <= bot:
                        cv2.text(sx0, sy, "F", shade(P["pink"], 0.9))
                        cv2.text(sx1, sy, "M", shade(P["cyan"], 0.9))
                        mid0, mid1 = sx0 + 2, sx1 - 2
                        cv2.hline(mid0, sy, max(1, mid1 - mid0), "─",
                                  shade(P["grey"], 0.45))
                        kx = mid0 + int((mid1 - mid0) *
                                        min(1.0, max(0.0, kp)))
                        cv2.put(kx, sy, "●", mix(P["pink"], P["cyan"], kp))
            stamp(cv, gender, a)

        # ---------- AM -> PM: a 24-hour band under the sky ----------
        a = fade_window(t, t_whatever - 0.3, t_role + 0.3, 0.4, 0.4)
        if a > 0.01:
            def ampm(cv2):
                k = ramp(t, t_ampm - 0.2, t_ampm + 2.4)
                small = space < 9
                by = min(bot - (1 if small else 2),
                         top + max(2, int(space * 0.62)))   # the hour band
                topy = top if small else top + 1
                hz = by - (1 if small else 2)               # horizon
                arcH = max(1, hz - topy - 1)
                bx0 = max(2, int(w * 0.09))
                bx1 = w - bx0
                if bx1 <= bx0 + 12:
                    return

                def band_x(hh):
                    return bx0 + int((bx1 - bx0) * (hh % 24) / 24.0)

                hour = 6.0 + 18.0 * k                       # 06:00 -> 24:00

                def sky_pos(hh):
                    x = band_x(hh)
                    if 6.0 <= hh <= 18.0:
                        u = (hh - 6.0) / 12.0
                    else:
                        u = ((hh - 18.0) % 24.0) / 12.0
                    return x, hz - int(round(math.sin(math.pi * u) * arcH))

                # ---- sky: stars come out for the night hours ----------
                night = 0.0 if hour < 18.0 else min(1.0, (hour - 18.0) / 4.0)
                ns = 8 if small else 26
                for i in range(ns):
                    if h01(i, 73) > 0.12 + 0.88 * night:
                        continue
                    sx = int(2 + h01(i, 71) * (w - 4))
                    sy = topy + int(h01(i, 72) * max(1, hz - topy))
                    tw = 0.3 + 0.7 * h01(i, int(t * 4.0))
                    cv2.put(sx, sy, "✦" if h01(i, 74) < 0.3 else "·",
                            shade(mix(P["ice"], P["white"], tw),
                                  0.22 + 0.6 * tw))
                # ---- the day's trajectory ------------------------------
                for i in range(25):
                    px, py = sky_pos(6 + i * 0.5)
                    cv2.put(px, py, "·", shade(P["violet"], 0.16))

                # ---- sun and moon trade places across the band ---------
                def body(hh, glyph, col, glow):
                    px, py = sky_pos(hh)
                    up = py < hz
                    col2 = col if up else shade(col, 0.30)
                    if not up:
                        py = hz + 1
                        if py > by - 1:
                            py = by - 1
                    if up:
                        for d in range(1, 4):
                            for s2x, s2y in ((d, 0), (-d, 0), (0, d), (0, -d)):
                                cv2.put(px + s2x, py + s2y, "·",
                                        shade(glow, 0.30 / d))
                    cv2.put(px, py, glyph, col2)
                    for d in range(1, 3):
                        cv2.put(px - d, py, "─", shade(col2, 0.35))
                        cv2.put(px + d, py, "─", shade(col2, 0.35))

                body(hour, "☼", mix(P["amber"], P["gold"],
                                    0.5 + 0.5 * math.sin(t * 2.2)), P["amber"])
                body((hour + 12.0) % 24.0, "☾",
                     mix(P["ice"], P["white"], 0.45), P["ice"])

                # ---- a small clock whose hand never stops sweeping ------
                if space >= 7 and w >= 40:
                    ccx, ccy = min(bx1 - 4, bx0 + 8), by - 3
                    if ccy > topy + 1:
                        for i in range(12):
                            ang = i * math.pi / 6.0
                            cv2.put(ccx + int(round(math.cos(ang) * 3)),
                                    ccy + int(round(math.sin(ang) * 1.7)),
                                    "·", shade(P["grey"], 0.55))
                        cv2.put(ccx, ccy, "◉", shade(P["violet"], 0.9))
                        ha = t * 9.4                       # fast sweep
                        cv2.put(ccx + int(round(math.cos(ha) * 3)),
                                ccy + int(round(math.sin(ha) * 1.7)),
                                "●", P["white"])
                        hb = hour / 12.0 * math.pi * 2.0 - math.pi / 2
                        cv2.put(ccx + int(round(math.cos(hb) * 2)),
                                ccy + int(round(math.sin(hb) * 1.2)),
                                "•", shade(P["amber"], 0.9))

                # ---- the 24 hour band ---------------------------------
                cv2.hline(bx0, by, bx1 - bx0, "─", shade(P["soft"], 0.35))
                for hh in range(0, 24, 3):
                    tx = band_x(hh)
                    cv2.put(tx, by, "┼", shade(P["soft"], 0.5))
                    if (hh % 6 == 0 or w >= 76) and by + 1 < bot:
                        cv2.text(tx - 1, by + 1, "%02d" % hh,
                                 shade(P["grey"], 0.6))
                cv2.put(bx1, by, "┤", shade(P["soft"], 0.5))
                if by + 1 < bot:
                    cv2.text(bx1 - 1, by + 1, "24", shade(P["grey"], 0.6))
                # AM / PM halves, the one we are in lit up
                am_on = hour < 12.0
                cv2.text(bx0 - 1 if bx0 > 3 else 1, by - 1, "AM",
                         P["amber"] if am_on else shade(P["grey"], 0.45))
                cv2.text(min(w - 3, bx1 - 1), by - 1, "PM",
                         shade(P["grey"], 0.45) if am_on else P["ice"])
                # ---- where we are: cursor + time + Δt ------------------
                cxp = band_x(hour)
                cv2.put(cxp, by, "▼", P["rose"])
                mins = int(360 + 1080 * k)
                ts = "%02d:%02d" % ((mins // 60) % 24, mins % 60)
                tx = min(w - 7, max(1, cxp - 2))
                if by + 2 <= bot:
                    cv2.text(tx, by + 2, ts, P["white"])
                    cv2.text(min(w - 4, tx + 6), by + 2, "Δt+%02dh" % (
                        max(0, int(hour) - 6)), shade(P["amber"], 0.8))
                else:
                    # no room below: read the time on the band itself
                    cv2.text(max(1, w - 12), by, ts, P["white"])
                if not small and by + 3 <= bot:
                    cv2.text(bx0 + 4, by + 3,
                             "06:00 sunrise↑ 12:00 noon 18:00 sunset↓",
                             shade(P["grey"], 0.55))
            stamp(cv, ampm, a)

        # ---------- S <-> M: two boxes physically trade places ----------
        a = fade_window(t, t_role - 0.3, t_enter + 0.3, 0.4, 0.4)
        if a > 0.01:
            def roles(cv2):
                k0, k1 = t_role + 0.2, t_sm + 1.6
                u0 = ramp(t, k0, k1)
                # after the exchange it keeps trading: S/M is a loop, not a
                # setting — same disease as the gender slider
                u = u0 if u0 < 0.999 else 0.5 + 0.5 * math.sin((t - k1) * 1.5)
                L = min(16, max(7, w // 4))
                x0s, x1s = cx - L - 3, cx + L - 3
                ymid = top + max(2, space // 2)
                amp = 2 if space >= 8 else 1

                def path(xa, xb, up, uu):
                    bx = int(xa + (xb - xa) * uu)
                    dy = int(round(math.sin(math.pi * uu) * amp))
                    return bx, ymid - dy if up else ymid + dy

                # the two crossing paths, drawn as dashed rails
                for uu in range(0, 25):
                    v = uu / 24.0
                    for xa, xb, up in ((x0s, x1s, True), (x1s, x0s, False)):
                        px, py = path(xa, xb, up, v)
                        if h01(uu, 3) < 0.7:
                            cv2.put(px, py, "·", shade(P["grey"], 0.30))

                # the slots they trade between
                if space >= 6:
                    for sx in (x0s, x1s):
                        fx.bracket(cv2, sx, ymid - 1, 7, 3,
                                   shade(P["grey"], 0.5), style="<>")

                def box(txt, xa, xb, up, col):
                    bx, by = path(xa, xb, up, u)
                    if space >= 6:
                        fx.bracket(cv2, bx, by - 1, 7, 3, col, style="[]")
                        cv2.text(bx + 3, by, txt, col)
                    else:
                        cv2.put(bx + 3, by, txt, col)
                    # trailing dots + an arrowhead showing the direction
                    d = 1 if xb > xa else -1
                    for tr in range(1, 4):
                        px, py = path(xa, xb, up, max(0.0, u - tr * 0.05))
                        cv2.put(px + 3, py, "·", shade(col, 0.55 - tr * 0.13))
                    px, py = path(xa, xb, up, min(1.0, u + 0.07))
                    cv2.put(px + 3, py, "»" if d > 0 else "«",
                            shade(col, 0.85))

                box("S", x0s, x1s, True, mix(P["violet"], P["white"], 0.4))
                box("M", x1s, x0s, False, mix(P["rose"], P["white"], 0.4))
                if w >= 44:
                    cv2.text(x0s, min(bot, ymid + 3), "master",
                             shade(P["violet"], 0.6))
                    cv2.text(x1s, min(bot, ymid + 3), "servant",
                             shade(P["rose"], 0.6))
                cv2.ctext(min(bot, ymid + 4), "S ⇄ M   master ⇄ servant",
                          shade(P["violet"], 0.9))
            stamp(cv, roles, a)

        # ---------- trance ------------------------------------------
        a = fade_window(t, t_enter - 0.2, self.t1 + 0.3, 0.4, 0.3)
        if a > 0.01:
            def trance(cv2):
                spin = t * (1.8 + 1.6 * ramp(t, t_enter, t_trance))
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
                # rings that pulse with the beat, pulling the eye in
                fx.ripple(cv2, cx, cy, t, P["violet"], n=3, speed=8.0,
                          period=0.9)
                pulse = 0.5 + 0.5 * math.sin(t * 4.0)
                cv2.put(cx, cy, "◎" if pulse > 0.6 else "◉",
                        mix(P["violet"], P["white"], pulse))
                if t >= t_trance:
                    # the lyric doubles: "the trance the trance" -- the
                    # echo types in behind the first, dimmer, possessed
                    if w >= 44:
                        anim.echo_row(cv2, 0, min(bot, cy + 9),
                                      "the trance", t, t_trance, n=2,
                                      fg=P["pink"], sep="  ",
                                      decay=0.55, cps=14.0, cx=cx)
                    else:
                        cv2.ctext(min(bot, cy + 9), "the trance", P["pink"])
                    cv2.ctext(min(bot, cy + 10),
                              "inducing… %3d%%" % int(min(99, 100 * ramp(
                                  t, t_enter, t_trance + 1.2))),
                              shade(P["violet"], 0.7))
            stamp(cv, trance, a)
            fx.row_wave(cv, t * 0.7, amp=1.6 * a, freq=0.4, speed=2.4)

        anim.scanline(cv, t, top, bot + 1, P["white"], speed=16.0, band=3,
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
        # while apart, each half beats on its own clock; the meters converge
        bpm_l = int(62 + 68 * sync + 6.0 * math.sin(t * 2.7))
        bpm_r = int(62 + 68 * sync + 6.0 * math.sin(t * 3.1 + 2.1))
        if t >= t_left1:
            bpm_r = 0                       # you are gone; nothing to beat
        if t >= t_iso:
            bpm_l = int(max(0, bpm_l * (1.0 - min(1.0, (t - t_iso) / 2.0))))

        def _bpm_row(y, lbl, val, col):
            cv.text(px_ + 2, y, lbl, shade(P["grey"], 0.7), bgp)
            bx = px_ + 8
            bwid = max(3, min(6, inner - 19))
            n = int(round(bwid * min(1.0, val / 130.0)))
            cv.put(bx, y, "▕", shade(P["grey"], 0.6), bgp)
            for i in range(bwid):
                cv.put(bx + 1 + i, y, "█" if i < n else "░",
                       col if i < n else shade(P["grey"], 0.3), bgp)
            cv.put(bx + 1 + bwid, y, "▏", shade(P["grey"], 0.6), bgp)
            cv.text(bx + bwid + 2, y, "%3d" % int(val), col, bgp)

        def _pips_row(y):
            left_n = 5 - taken
            pips = "".join("▰" if i < left_n else "▱" for i in range(5))
            cv.text(px_ + 2, y, _fit("left %s  %d/5" % (pips, left_n), inner),
                    shade(P["soft"], 0.9), bgp)

        def _dial_at(dx, dy):
            # the phase-alignment needle: it pins to 12 o'clock on the join
            if t < t_comp:
                dval = (1.0 - sync) * (0.5 + 0.5 * math.sin(t * 2.3))
            else:
                dval = 0.03 + 0.03 * math.sin(t * 1.7)
            anim.dial(cv, dx, dy, 2, dval, shade(P["ice"], 0.9), None, bgp)

        def _counter_row(y):
            anim.counter(cv, px_ + 2, y, "v",
                         int(432 + 64 * math.sin(t * 2.7) +
                             26 * math.sin(t * 11.0)),
                         "%5d Hz", shade(P["ice"], 0.9), bg=bgp,
                         dim_fg=shade(P["grey"], 0.45))

        def _word_row(y):
            word = ("approaching" if t < t_vib else
                    "vibrating" if t < t_comp else
                    "complete" if t < t_left1 else
                    "detaching" if t < t_iso else "isolated")
            cv.text(px_ + 2, y,
                    _fit("%s  %s" % (word, "·" * (1 + int(t * 3) % 6)), inner),
                    shade(P["pink"], 0.8), bgp)

        anim.meter(cv, px_ + 2, py_ + 1, "sync", sync * 100.0, 100.0, bw,
                   shade(P["rose"], 0.95), bg=bgp,
                   dim_fg=shade(P["grey"], 0.45))
        if ph_ >= 12:
            anim.meter(cv, px_ + 2, py_ + 2, "complete", complete, 100.0,
                       max(3, min(9, inner - 19)), shade(P["amber"], 0.95),
                       bg=bgp, dim_fg=shade(P["grey"], 0.45))
            _pips_row(py_ + 3)
            cv.hline(px_ + 2, py_ + 4, inner, "─", shade(P["rose"], 0.3), bgp)
            _bpm_row(py_ + 5, "♥ L", bpm_l, shade(P["rose"], 0.95))
            _bpm_row(py_ + 6, "♥ R", bpm_r, shade(P["cyan"], 0.95))
            _dial_at(px_ + 21, py_ + 7)
            cv.text(px_ + 20, py_ + 9, "Δφ", shade(P["ice"], 0.75), bgp)
            _counter_row(py_ + 8)
            kv = int(t * 14)
            s_ = "0x%04X 0x%04X 0x%04X" % (
                int(h01(kv, 1, 9) * 65535), int(h01(kv, 2, 9) * 65535),
                int(h01(kv, 3, 9) * 65535))
            cv.text(px_ + 2, py_ + 10, _fit(s_, inner),
                    shade(P["violet"], 0.45), bgp)
            _word_row(py_ + 11)
        elif ph_ >= 9:
            _pips_row(py_ + 2)
            _bpm_row(py_ + 3, "♥ L", bpm_l, shade(P["rose"], 0.95))
            _bpm_row(py_ + 4, "♥ R", bpm_r, shade(P["cyan"], 0.95))
            _dial_at(px_ + 20, py_ + 6)
            _counter_row(py_ + 7)
            kv = int(t * 14)
            s_ = "0x%04X 0x%04X" % (int(h01(kv, 1, 9) * 65535),
                                    int(h01(kv, 2, 9) * 65535))
            cv.text(px_ + 2, py_ + 8, _fit(s_, inner - 6),
                    shade(P["violet"], 0.45), bgp)
            _word_row(py_ + 9)
        else:
            _bpm_row(py_ + 2, "L", bpm_l, shade(P["rose"], 0.95))
            _bpm_row(py_ + 3, "R", bpm_r, shade(P["cyan"], 0.95))
            _pips_row(py_ + 4)
            _word_row(py_ + 5)
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

    # the snap: the seam WELDS shut, then a ring that travels out
    if 0.0 <= t - t_comp < 0.6 and not tiny:
        kk = 1.0 - (t - t_comp) / 0.6
        for y in range(hy, hy + nrow):
            cv.put(cx - 1, y, "│", shade(P["white"], 0.9 * kk))
            cv.put(cx, y, "│", shade(P["white"], 0.6 * kk))
        fx.sparkle(cv, cx, cy, t, P["white"], seed=int(t * 9), n=10,
                   rad=max(2, min(9, min(cy - top, bot - cy) + 1)))
    if 0.0 <= t - t_comp < 1.2 and not tiny:
        # welding sparks run down the seam, over and over
        for w_ in range(3):
            uu = ((t - t_comp) * 3.2 + w_ / 3.0) % 1.0
            yy = hy + int(uu * max(1, nrow - 1))
            cv.put(cx - 1 + (w_ % 2), yy, "✦", shade(P["amber"], 0.95))
            cv.put(cx + 1 - (w_ % 2), max(top, yy - 1), "·",
                   shade(P["amber"], 0.5))
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

    # the machine refuses to believe it: "you have left" -- typed, denied,
    # typed again, one loop per cut band and faster every time, as if
    # speed could undo it; after the last denial the row sits empty for a
    # beat, then at isolation it finally types the whole sentence, "me"
    # beating inside it, and the line never moves again
    if not tiny and space >= 9 and w >= 56:
        deny_y = hy - 1 if hy - 1 >= top else min(bot, hy + nrow + 2)
        if t >= cues_all[0] + 0.10 and top <= deny_y <= bot:
            if t >= t_iso:
                # the admission: the whole sentence, typed once, kept
                s = "you have left me in isolation"
                age = t - t_iso
                vis = s[:max(0, int(age * 19.0))]
                x0 = (w - len(s)) // 2
                cv.text(x0, deny_y, vis, shade(P["rose"], 0.85))
                if len(vis) > 14:
                    # "me" carries the accent, and it beats
                    bph = (t / 0.4615) % 1.0
                    beat = math.exp(-bph * 6.0)
                    cv.text(x0 + 14, deny_y, vis[14:16],
                            shade(P["pink"], 0.62 + 0.38 * beat))
                if 0 < len(vis) < len(s) and int(t * 4) % 2:
                    cv.put(x0 + len(vis), deny_y, "▮",
                           shade(P["rose"], 0.7))
            else:
                ci = 0
                for i in range(4):
                    if t >= cues_all[i] + 0.10:
                        ci = i
                # each denial types and deletes faster than the last
                vis, _k, ph = anim.type_loop(
                    t, cues_all[ci] + 0.10, "you have left", cycles=1,
                    cps=24.0 + 3.0 * ci, hold=0.04,
                    wipe=0.24 - 0.03 * ci, gap=9.0, del_last=True)
                if vis:
                    x0 = (w - len(vis)) // 2
                    cv.text(x0, deny_y, vis,
                            shade(mix(P["rose"], P["grey"], 0.25), 0.9))
                    if ph in ("type", "wipe") and int(t * 5) % 2:
                        cv.put(x0 + len(vis), deny_y, "▮",
                               shade(P["rose"], 0.7))

    # each band gets named as it is cut away
    if space >= 7 and w >= 56:
        _c2_names = ("touch", "warmth", "laughter", "support", "heartbeat")
        for b in range(5):
            age = t - (cues_all[b] + 0.16)
            if 0.0 <= age < 0.84:
                s_ = "band %d/5  − %s" % (b + 1, _c2_names[b])
                sh_, _ = fx.typewriter(s_, age - 0.04, 26.0)
                cv.ctext(min(bot, hy + nrow + 1), sh_,
                         mix(P["rose"], P["grey"], min(1.0, age / 0.6)))

    # the witness: still here, then in orbit around what we became, then not
    youx, youy = w - 6, cy
    ocx, ocy = w - 14, cy
    if t < t_left1:
        if t < t_comp + 0.2:
            bright = 0.55 + 0.35 * math.sin(t * 3.1)
            if space >= 9:
                for j, ln in enumerate(art.YOU["diamond"]):
                    cv.text(youx - 2, youy - 2 + j, ln,
                            shade(P["pink"], bright))
                cv.text(youx - 2, youy + 3, '"me"', shade(P["pink"], 0.6))
            else:
                cv.put(youx, youy, "◆", shade(P["pink"], bright))
            fx.sparkle(cv, youx, youy, t, P["pink"], seed=int(t * 5), n=4,
                       rad=max(1, min(4, youy - top, bot - youy)))
        elif space >= 7:
            # joined: you and me orbit a shared centre of mass
            kf = ramp(t, t_comp + 0.2, t_comp + 0.9)
            th = t * 1.5
            for i in range(12):
                ea = i * math.pi / 6.0
                cv.put(ocx + int(round(math.cos(ea) * 6)),
                       ocy + int(round(math.sin(ea) * 2)), "·",
                       shade(P["grey"], 0.35 * kf))
            cv.put(ocx, ocy, "+", shade(P["white"], 0.85 * kf))
            bph = (t * 2.1667) % 1.0            # 130 BPM thump, shared now
            beat = 0.35 + 0.65 * math.exp(-bph * 6.0)
            youx2 = ocx + int(round(math.cos(th) * 6))
            youy2 = ocy + int(round(math.sin(th) * 2))
            cv.put(youx2, youy2, "◆",
                   shade(P["pink"], (0.55 + 0.45 * beat) * kf))
            mex2 = ocx + int(round(math.cos(th + math.pi) * 4))
            mey2 = ocy + int(round(math.sin(th + math.pi) * 1.5))
            cv.put(mex2, mey2, "●",
                   shade(P["phos"], (0.5 + 0.5 * beat) * kf))
            if space >= 9 and w >= 76:
                cv.text(min(w - 2, youx2 + 2), youy2, "you",
                        shade(P["pink"], 0.5 * kf))
                cv.text(max(2, mex2 - 4), mey2, "me",
                        shade(P["phos"], 0.5 * kf))
    else:
        age = t - t_left1
        # me keeps circling the now-empty centre of mass, slower, dimmer
        if space >= 7 and t < t_iso:
            kf = max(0.3, 1.0 - 0.7 * ramp(t, t_left1, t_left1 + 3.2))
            for i in range(12):
                ea = i * math.pi / 6.0
                cv.put(ocx + int(round(math.cos(ea) * 6)),
                       ocy + int(round(math.sin(ea) * 2)), "·",
                       shade(P["grey"], 0.22 * kf))
            cv.put(ocx, ocy, "+", shade(P["white"], 0.5 * kf))
            th = t_left1 * 1.5 + (t - t_left1) * 0.5
            mex2 = ocx + int(round(math.cos(th + math.pi) * 2))
            mey2 = ocy + int(round(math.sin(th + math.pi) * 0.8))
            cv.put(mex2, mey2, "●", shade(P["phos"], 0.8 * kf))
        if age < 3.0 and space >= 8:
            thl = t_left1 * 1.5
            gx0 = ocx + int(round(math.cos(thl) * 6))
            gy0 = ocy + int(round(math.sin(thl) * 2))
            u = age / 3.0
            xx = int(gx0 + 16 * u)
            yy = gy0 - 2 - int(10 * u)
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
                        # the free heap CLIMBS as the blocks zero out
                        cv2.text(2, yh, "free", shade(P["grey"], 0.7))
                        bw2 = max(6, min(14, w - 20))
                        fx.bar(cv2, 7, yh, bw2, 0.88 * rel,
                               shade(P["amber"], 0.9), None)
                        cv2.text(9 + bw2, yh,
                                 "%2d%%" % int(0.88 * rel * 100),
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
                cv2.text(mx0 + 2, by2, "used", shade(P["grey"], 0.7))
                bw2 = max(6, min(16, mw - 22))
                fx.bar(cv2, mx0 + 7, by2, bw2, 1.0 - 0.88 * rel,
                       shade(P["amber"], 0.9), None)
                cv2.text(mx0 + 9 + bw2, by2, "%2d%%" % int((1 - 0.88 * rel) * 100),
                         shade(P["amber"], 0.85))
                # ...and the free heap climbs as the bytes zero out
                if mw >= 47:
                    fx.bar(cv2, mx0 + 29, by2, 8, 0.88 * rel,
                           shade(P["cyan"], 0.85), None)
                    cv2.text(mx0 + 38, by2, "free %2d%%" % int(0.88 * rel * 100),
                             shade(P["cyan"], 0.8))

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
                bob = 1 if (t * 0.9) % 2.0 > 1.72 else 0     # breathing
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j + bob, ln, mix(P["phos"], P["grey"], 0.4))
                # the folder
                fx.bracket(cv2, mx + 10, my + 1, 9, 4, P["pink"], style="<>")
                cv2.text(mx + 12, my + 2, "you/", P["pink"])
                # dust rising off the folder (drawn first; the chain wins)
                for i in range(8):
                    u = ((t * 0.5 + i / 8.0) % 1.0)
                    cv2.put(int(mx + 10 + math.sin(i * 2.1) * 3),
                            int(my - 2 - u * 5), "·", shade(P["grey"], 0.4))
                # ---- the chain of us, unlinked one node at a time ----
                if w >= 46 and h >= 16:
                    chy = my - 3
                    nxs = (cx - 10, cx - 5, cx + 1, cx + 6)
                    axs = (cx - 6, cx, cx + 5)
                    names = ("me", "you", "us", "…")
                    # arrows are cut right to left; each cut frees the node
                    # to its right, which drops into the bin
                    cuts = (122.90, 122.35, 121.80)
                    binx, biny = cx + 12, my + 5
                    fx.bracket(cv2, binx, biny, 9, 3, shade(P["grey"], 0.7),
                               style="[]")
                    cv2.text(binx, biny - 1, "bin", shade(P["grey"], 0.6))
                    dropped = 0
                    for i in range(3):
                        if t < cuts[i]:
                            cv2.text(axs[i], chy, "→",
                                     shade(P["violet"], 0.9))
                        else:
                            age = t - cuts[i]
                            cv2.text(axs[i], chy, "∅",
                                     shade(P["red"] if age < 0.35 else
                                           P["grey"], 0.9 if age < 0.35 else 0.6))
                    for j, nm in enumerate(names):
                        alive = (j == 0) or (t < cuts[j - 1])
                        if alive:
                            cv2.text(nxs[j], chy, "[%s]" % nm,
                                     P["phos"] if j == 0 else
                                     shade(P["violet"], 0.9))
                        elif t < cuts[j - 1] + 0.75:
                            # gravity arc into the bin
                            u = (t - cuts[j - 1]) / 0.75
                            fx_ = int(nxs[j] + (binx + 2 - nxs[j]) * u)
                            fy_ = int(chy + (biny + 1 - chy) * (u * u))
                            cv2.text(fx_, fy_, "[%s]" % nm,
                                     mix(P["violet"], P["grey"], u))
                        else:
                            dropped += 1
                    # the bin fills: everything but me fits in there
                    for d in range(min(3, dropped)):
                        cv2.put(binx + 2 + d * 2, biny + 1, "▓",
                                shade(P["grey"], 0.8 - 0.1 * d))
                    if dropped:
                        cv2.text(binx + 11, biny + 1,
                                 "freed %d/4" % dropped,
                                 shade(P["cyan"], 0.7))
                    if t >= 123.9:
                        s2 = "you: <null>"
                        sh2, ty2 = fx.typewriter(s2, t - 123.9, 16.0)
                        cv2.text(cx - 10, chy + 2, sh2,
                                 shade(P["grey"], 0.8))
                        if ty2 and int(t * 8) % 2 == 0:
                            cv2.put(cx - 10 + sw(sh2), chy + 2, "▮",
                                    shade(P["grey"], 0.6))
                    # the one memory that will not stay deleted: [you]
                    # flashes back into its old slot once, is re-erased,
                    # and does not come back
                    fl = t - 124.70
                    if 0.0 <= fl < 0.44:
                        if fl < 0.20:
                            b = 0.55 + 0.45 * (int(t * 24) % 3 == 0)
                            cv2.text(nxs[1], chy, "[you]",
                                     shade(mix(P["pink"], P["white"], 0.35),
                                            b))
                        else:
                            n_ = max(0, 5 - int((fl - 0.20) * 24))
                            if n_:
                                cv2.text(nxs[1], chy, "[you]"[:n_],
                                         shade(P["grey"], 0.42))
                # the one memory block that is not a pointless fragment
                if t >= t_maybe + 0.2:
                    kr = ramp(t, t_maybe + 0.2, t_maybe + 1.0)
                    yy = min(h - 5, my + len(art.ME["sit"]) + 1)
                    cv2.text(mx - 2, yy, "0x7ff8", shade(P["amber"], 0.6 * kr))
                    cv2.text(mx + 8, yy, "79 6f 75 00", shade(P["pink"], kr))
                    cv2.text(mx + 22, yy, '"you."', shade(P["pink"], kr))
                    cv2.put(mx + 30, yy, "♥",
                            shade(P["rose"], kr * (0.6 + 0.4 * math.sin(t * 5.0))))
                # "then maybe" -- the bargain, escalating: the short
                # version types, is doubted, deleted; then the plea
                # retypes itself LONGER, and this time it stays typed
                if w >= 60 and h >= 16:
                    if t < t_dis - 0.2:
                        vis, _k, ph = anim.type_loop(
                            t, t_maybe, "then maybe", cycles=1, cps=24.0,
                            hold=0.10, wipe=0.24, gap=9.0, del_last=True)
                        col = shade(P["grey"], 0.8)
                    else:
                        vis, _k, ph = anim.type_loop(
                            t, t_dis - 0.2, "then maybe you won't leave me",
                            cycles=1, cps=26.0, hold=60.0, wipe=0.20,
                            del_last=False)
                        col = shade(mix(P["grey"], P["rose"], 0.30), 0.85)
                    if vis:
                        x0m = (w - len(vis)) // 2
                        cv2.text(x0m, h - 4, vis, col)
                        if ph in ("type", "wipe") and int(t * 5) % 2:
                            cv2.put(x0m + len(vis), h - 4, "▮",
                                    shade(P["grey"], 0.55))
                if t >= t_dis - 0.2:
                    s = "maybe if I delete myself, you'll come back?"
                    shown, typing = fx.typewriter(s, t - t_dis + 0.2, 26.0)
                    cv2.ctext(h - 3, shown, shade(P["grey"], 0.85))
            stamp(cv, hug, a)
            # the beat breathes: nothing sits perfectly still while it waits
            fx.row_wave(cv, t * 0.9, amp=1.2 * a, freq=0.35, speed=1.4)

        # ---------- god looms ---------------------------------------
        a = fade_window(t, t_god - 0.3, t_ill + 1.2, 0.5, 0.5)
        if a > 0.01:
            def god(cv2):
                # keep the whole silhouette inside the picture rows
                if h >= 24:
                    godart, meart = art.ART["god"][:9], art.ME["reach2"]
                    gy = 4
                    my = h - len(meart) - 3
                elif h >= 19:
                    godart, meart = art.ART["god"][:7], art.ME["reach2"]
                    gy = 4
                    my = gy + len(godart) + 1
                elif h >= 15:
                    godart, meart = art.ART["god"][:5], None
                    gy = 4
                    my = h - 4
                else:
                    godart, meart = art.ART["god"][:3], None
                    gy = 4
                    my = h - 3
                for i, ln in enumerate(godart):
                    cv2.text(cx - 13, gy + i, ln, shade(P["gold"], 0.85))
                # light rays down, shimmering (the challenge is being read)
                for i in range(9):
                    x = cx - 20 + i * 5
                    for yy in range(gy + len(godart), h - 7):
                        if h01(x, yy, int(t * 7)) < 0.35:
                            cv2.put(x + (yy // 3) % 3, yy, "│",
                                    shade(P["amber"], 0.18))
                # a faint aura pulses around the throne
                if h >= 15:
                    fx.circle(cv2, cx, gy + 5, 15, shade(P["gold"], 0.13),
                              "·", ry=5)
                # tiny me with raised fist (or a lone dot, on a short screen)
                if meart:
                    mx = cx - 4
                    for j, ln in enumerate(meart):
                        cv2.text(mx, my + j, ln, P["phos"])
                else:
                    cv2.put(cx - 6, my, "●", P["phos"])
                if t >= t_god + 0.3:
                    cmd = "$ god2 --challenge" if w >= 50 else "$ god2"
                    cv2.text(cx + 2, my + (1 if meart else -1), cmd, P["phos"])
                if t >= t_ill - 0.1:
                    err = ("ERROR: illegal arguments" if w >= 64 else
                           "ERR: bad args")
                    cv2.text(cx + 2, my + (3 if meart else 0), err, P["red"])
            stamp(cv, god, a)

        # ---------- illegal arguments: the traceback types itself --
        if t >= t_ill - 0.15:
            def errors(cv2):
                lines = [
                    "Traceback (most recent call last):",
                    "  File \"me.js\", line 1, in <module>",
                    "    love(you)                      # illegal",
                    "TypeError: cannot convert 'love' to 'obedience'",
                    "  File \"kernel\", line 130, in execute",
                    "    god2(me)                       # illegal",
                    "FATAL: argument 'me' is not accepted by god()",
                    "Segmentation fault (core dumped)",
                    "Kernel panic — not syncing: world.execute(me)",
                    "FATAL: illegal arguments to love()",
                    "  at devotion (me.js:7:13)",
                ]
                n = int((t - (t_ill - 0.15)) * 3.0) + 1
                top_ = min(n, 11)
                for i in range(top_):
                    s = lines[i]
                    y = h - 4 - i
                    if y < 1:
                        break
                    if w < 64:
                        s = _fit(s, w - 6)
                    c = P["red"] if i % 2 == 0 else shade(P["blood"], 1.5)
                    cv2.text(2 + (i % 3) * 2, y, s, shade(c, 0.92 - i * 0.03))
                # the cursor blinks on the newest line: it is still typing
                if top_ <= 11:
                    y = h - 4 - (top_ - 1)
                    s = _fit(lines[top_ - 1], w - 6) if w < 64 else lines[top_ - 1]
                    if int(t * 6) % 2 == 0:
                        cv2.put(2 + ((top_ - 1) % 3) * 2 + sw(s), y, "▮",
                                shade(P["red"], 0.85))
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

    _TD = {  # 3x5 patterns for the big T-minus digits
        "0": ("███", "█ █", "█ █", "█ █", "███"),
        "1": (" █ ", "██ ", " █ ", " █ ", "███"),
        "2": ("███", "  █", "███", "█  ", "███"),
        "3": ("███", "  █", "███", "  █", "███"),
        "4": ("█ █", "█ █", "███", "  █", "  █"),
        "5": ("███", "█  ", "███", "  █", "███"),
        "6": ("███", "█  ", "███", "█ █", "███"),
        "7": ("███", "  █", "  █", "  █", "  █"),
        "8": ("███", "█ █", "███", "█ █", "███"),
        "9": ("███", "█ █", "███", "  █", "███"),
        "T": ("███", " █ ", " █ ", " █ ", " █ "),
        "-": ("   ", "   ", "███", "   ", "   "),
    }

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        top, bot = _rows(cv)
        space = bot - top + 1
        tl = t - self.t0
        cx = w // 2
        BEAT = 0.4615
        k = ramp(t, self.t0, self.t1 - 1.6)
        k2 = ramp(t, self.t0 + 7.2, self.t1 - 1.0)     # all layers in

        # ---- the error cascade, accelerating behind everything ----------
        rate = 3.0 + 26.0 * k * k
        chars = "ERROR0123456789/\\|<>[]{}()#@$%&*"
        cap = 40 if w >= 88 else (20 if w >= 62 else 10)
        for i in range(min(cap, int(tl * rate * 0.5))):
            y = top + 1 + int(h01(i, int(t * 3)) * max(1, space - 4))
            x = int(h01(i, int(t * 3) + 1) * max(1, w - 22))
            ln = "".join(chars[int(h01(i, j, int(t * 2)) * len(chars))]
                         for j in range(6 + int(h01(i, 5) * 14)))
            c = shade(mix(P["blood"], P["red"], h01(i, 9)), 0.30 + 0.28 * k)
            cv.text(x, y, ln, c)

        # ---- the layer stack: each instrument joins, then never stops ----
        # top row first in the list, but kick joins first (bottom of stack)
        lay = (("pad", "violet", 2, 0.52),
               ("arp", "magenta", 2, 0.64),
               ("lead", "rose", 1, 0.78),
               ("bass", "amber", 1, 0.90),
               ("kick", "red", 1, 1.00))
        joins = (self.t0 + 7.2, self.t0 + 5.6, self.t0 + 4.0,
                 self.t0 + 2.4, self.t0 + 0.8)
        full = h >= 22 and w >= 88
        mid = h >= 17 and w >= 62
        comp = h >= 13 and w >= 44

        # ---- the charging beam, aimed at the target ---------------------
        beam_k = ramp(t, self.t0 + 7.5, self.t1 - 0.7)
        tiny3 = space <= 3
        if tiny3:
            # no vertical room: the charge runs sideways into the target
            row = top + 1
            cv.text(2, row, "k▂b▄", shade(P["amber"], 0.8))
            fx.bar(cv, 8, row, 8, beam_k, shade(P["red"], 0.9), None)
            cv.text(17, row, "→", shade(P["gold"], 0.9))
            cv.put(19, row, "◆", mix(P["gold"], P["white"],
                                      0.4 + 0.4 * math.sin(t * 6.0)))
            if beam_k > 0.96 and int(t * 8) % 2 == 0:
                cv.put(20, row, "✦", P["white"])
        else:
            ty = top + 1
            cv.put(cx, ty, "◆", mix(P["gold"], P["white"],
                                     0.4 + 0.4 * math.sin(t * 6.0)))
            if (full or mid) and w >= 62:
                cv.text(cx + 2, ty, "you", shade(P["gold"], 0.7))
            btop = ty + (2 if (full or mid or comp) else 1)
            bh = int((bot - 1 - btop) * beam_k ** 1.6)
            for y in range(bot - 1 - bh, bot):
                d = (bot - 1 - y) / max(1, bh) if bh else 1.0
                c = mix(P["white"], P["red"], min(1.0, 0.25 + d))
                cv.put(cx - 1, y, "▐", c)
                cv.put(cx, y, "█", c)
                cv.put(cx + 1, y, "▌", c)
            if beam_k > 0.96:
                fx.sparkle(cv, cx, ty + 2, t, P["white"], seed=int(t * 9),
                           n=6, rad=3)
            if t >= self.t1 - 0.55 and beam_k > 0.97:
                # it fires: one white instant, then the world changes scenes
                for y in range(ty + 2, bot):
                    cv.put(cx, y, "█", P["white"])
                    cv.put(cx - 1, y, "▌", shade(P["gold"], 0.9))
                    cv.put(cx + 1, y, "▐", shade(P["gold"], 0.9))

        # ---- T-minus: the machine counts its own remaining beats --------
        beats_left = (self.t1 - t) / BEAT
        bph = ((t - self.t0) / BEAT) % 1.0
        flash = math.exp(-bph * 7.0)

        def _tblock(tx0, ty0, txt, col):
            for c in txt:
                pat = self._TD.get(c)
                if pat is None:
                    tx0 += 4
                    continue
                for j in range(5):
                    for i in range(3):
                        if pat[j][i] != " ":
                            cv.put(tx0 + i, ty0 + j, pat[j][i], col)
                tx0 += 4

        if full or mid:
            px = 2
            pw = 28 if full else 24
            ph = 14 if full else 12
            py = top + 2
            fx.panel(cv, px, py, pw, ph, shade(P["red"], 0.75),
                     title=" layer.stack ",
                     title_fg=shade(P["red"], 0.95))
            tx0 = min(w - 14, px + pw + 6 + (w - px - pw - 20) // 2)
            # big digits while they can still be counted on fingers
            if 0.0 <= beats_left <= 8.99:
                tn = max(0, int(beats_left))
                # clear a window so the errors don't eat the digits
                for j in range(5):
                    for i in range(12):
                        cv.put(tx0 - 1 + i, top + 3 + j, " ",
                               None, P["black"])
                col = mix(P["red"], P["white"], flash)
                _tblock(tx0, top + 3, "T-%d" % tn, col)
            else:
                mm = int(beats_left * BEAT) // 60
                ss = int(beats_left * BEAT) % 60
                cv.text(tx0, top + 4,
                        "t-minus %02d:%02d" % (mm, ss), shade(P["red"], 0.9))
            # the charge chant: "ex·e·cu·tion" assembles one syllable per
            # bar as the beam charges; it is whole exactly as the digits
            # take over, and then it beats with the countdown
            syls = ("ex", "e", "cu", "tion")
            bar_t = BEAT * 4.0
            n_on = sum(1 for j in range(4)
                       if t >= self.t0 + (2 + j) * bar_t)
            if n_on:
                yq = top + 9
                if n_on == 4:
                    cv.text(tx0, yq, "to ex·e·cu·tion",
                            mix(P["red"], P["white"], 0.45 * flash))
                else:
                    cv.text(tx0, yq, "to ", shade(P["grey"], 0.55))
                    xx = tx0 + 3
                    for j in range(n_on):
                        if j:
                            cv.put(xx, yq, "·", shade(P["red"], 0.5))
                            xx += 1
                        pop = max(0.0, 1.0 - (t - (self.t0 + (2 + j) * bar_t))
                                  / 0.35)
                        cv.text(xx, yq, syls[j],
                                mix(P["grey"], P["amber"], pop) if pop > 0
                                else shade(P["grey"], 0.7))
                        xx += len(syls[j])
                    if n_on < 4:
                        # the next syllable charging: the dot blinks
                        cv.put(xx, yq, "·",
                               shade(P["red"], 0.8 if int(t * 3) % 2 else 0.3))
            # readouts that climb and climb
            vel = int(96 + 56 * k2 + 6 * math.sin(t * 2.1))
            bpm = int(100 + 30 * k2 + 3 * math.sin(t * 1.3))
            ld = int(12 + 85 * k)
            rows_ = (("velocity", "%3d" % vel, P["amber"]),
                     ("tempo", "%3d BPM" % bpm, P["gold"]),
                     ("load", "%3d%%" % ld, P["red"]))
            for i, (nm, val, col) in enumerate(rows_):
                yy = top + 11 + i
                cv.text(tx0, yy, nm, shade(P["grey"], 0.75))
                cv.text(tx0 + len(nm) + 1, yy, val, col)
                if i == 0 and int(t * 3) % 2 == 0:
                    cv.put(tx0 + len(nm) + len(val) + 2, yy, "▲",
                           shade(col, 0.5))
        elif comp:
            # header row + the countdown at the right; layers below
            tn = max(0, int(beats_left))
            cv.rtext(top, "T-%d" % tn, P["red"], right=w - 3)
        elif space >= 4:
            tn = max(0, int(beats_left))
            cv.rtext(top + 1, "T-%d" % tn, P["red"], right=w - 3)
        else:
            tn = max(0, int(beats_left))
            cv.rtext(top + 1, "T-%d" % tn, P["red"], right=w - 3)

        # ---- layer rows (all tiers) -------------------------------------
        if full or mid:
            lx = px + 2
            for i, (nm, colk, mult, base) in enumerate(lay):
                y = py + 2 + i
                col = P[colk]
                on = t >= joins[i]
                if on:
                    e = ctx.e_at(t) * base
                    pop = min(1.0, (t - joins[i]) / 0.4)
                    cv.text(lx, y, nm, mix(col, P["white"], 0.3))
                    for j in range(4):
                        v = (0.35 + 0.65 * e) * (0.5 + 0.5 * math.sin(
                            t * 6.0 + j * 1.4 + i * 2.2))
                        cv.put(lx + 7 + j, y, "▁▂▃▄▅▆▇"[min(6, int(v * 6.99))],
                               shade(col, 0.55 + 0.45 * pop))
                    cv.text(lx + 12, y, "×%d" % mult, shade(P["grey"], 0.7))
                    act = base * (0.55 + 0.45 * k)
                    fx.bar(cv, lx + 15, y, 5, act, shade(col, 0.85), None)
                    cv.text(lx + 21, y, "%3d%%" % int(act * 100),
                            shade(col, 0.9))
                else:
                    cv.text(lx, y, nm, shade(P["grey_dim"], 0.8))
                    cv.text(lx + 7, y, "···", shade(P["grey_dim"], 0.6))
                    cv.text(lx + 15, y, "—", shade(P["grey_dim"], 0.7))
            # density + a live spectrum strip
            dy = py + ph - 4
            cv.text(lx, dy, "density", shade(P["grey"], 0.7))
            fx.bar(cv, lx + 8, dy, max(4, pw - 18), 0.15 + 0.85 * k,
                   shade(P["red"], 0.9), None)
            cv.text(lx + 8 + max(4, pw - 18) + 1, dy,
                    "%3d%%" % int((0.15 + 0.85 * k) * 100),
                    shade(P["red"], 0.85))
            anim.pulse_bars(cv, lx, py + ph - 2, max(4, (pw - 4) // 2),
                            t, shade(P["red"], 0.5), 2, seed=7, gap=1)
        elif comp:
            for i, (nm, colk, mult, base) in enumerate(lay):
                y = top + 1 + i
                col = P[colk]
                on = t >= joins[i]
                if on:
                    e = ctx.e_at(t) * base
                    cv.text(2, y, nm, mix(col, P["white"], 0.3))
                    for j in range(4):
                        v = (0.35 + 0.65 * e) * (0.5 + 0.5 * math.sin(
                            t * 6.0 + j * 1.4 + i * 2.2))
                        cv.put(8 + j, y, "▁▂▃▄▅▆▇"[min(6, int(v * 6.99))],
                               shade(col, 0.8))
                    cv.text(14, y, "%3d%%" % int(base * (0.55 + 0.45 * k) * 100),
                            shade(col, 0.9))
                else:
                    cv.text(2, y, nm, shade(P["grey_dim"], 0.8))
                    cv.text(8, y, "···", shade(P["grey_dim"], 0.6))
        elif not tiny3:
            # tiny: the stack as one line of tiny meters
            s_ = ""
            for i, (nm, colk, mult, base) in enumerate(lay[:3]):
                on = t >= joins[i + 2]
                s_ += ("%s%s " % (nm[:2], "▂" if on else "·"))
            cv.text(2, top + 1, s_, shade(P["amber"], 0.8))
            cv.text(2, top + 2, "vel %d bpm %d" % (int(96 + 56 * k2),
                                                   int(100 + 30 * k2)),
                    shade(P["amber"], 0.8))
            anim.pulse_bars(cv, 2, bot - 1, min(8, (w - 4) // 2), t,
                            shade(P["red"], 0.55), 1, seed=3, gap=1)

        # ---- a spectrum wall on the far edge (full/mid) ------------------
        if full:
            anim.pulse_bars(cv, w - 11, bot - 1, 8, t,
                           shade(P["red"], 0.65), min(6, space - 7),
                           seed=5, gap=1)
        elif mid:
            anim.pulse_bars(cv, w - 9, bot - 1, 7, t,
                            shade(P["red"], 0.6), min(5, space - 6),
                            seed=5, gap=1)

        # ---- bottom ticker: the machine narrates its own arming ---------
        if space >= 3:
            n_on = sum(1 for j in joins if t >= j)
            anim.ticker(cv, bot,
                        "build.log · layer %d/5 · vel %d · tempo %d · "
                        "beam %3d%% · t-minus %04.1fs · do not look away · "
                        % (n_on, int(96 + 56 * k2),
                           int(100 + 30 * k2), int(beam_k * 100),
                           max(0.0, self.t1 - t)),
                        t, speed=14.0 + 10.0 * k, fg=shade(P["red"], 0.6),
                        x0=2, x1=w - 3)

        # ---- header + the final word --------------------------------------
        if t < self.t1 - 1.5:
            cv.text(2, top, "KERNEL PANIC — EXECUTION PENDING", P["red"])
            if w >= 62 and int(t * 2.5) % 2 == 0:
                cv.rtext(top, "!! WARNING !!", P["red"], right=w - 3)
        else:
            cv.ctext(max(top, h // 2 - 1), "ready.",
                     mix(P["white"], P["red"], 0.4))

        fx.glitch(cv, t, 0.1 + 0.5 * k)
        fx.scanlines(cv, 0.8)
        fx.vignette(cv, 0.35)
