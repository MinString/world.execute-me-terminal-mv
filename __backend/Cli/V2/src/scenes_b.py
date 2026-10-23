"""Scenes: verse 3, pre-chorus 2, chorus 2, bridge, build, chant,
final chorus, outro, shutdown, end card."""

import math

import art
import fx
from base import Scene, stamp, fade_window, ramp, cue, glow_text
from renderer import mix, shade, grey, P, h01, sw


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

        cx = int(w * 0.42)
        youx, youy = int(w * 0.82), h // 2

        # faint grid / starfield
        fx.starfield(cv, t, P["violet"], n=40, seed=17)

        # the "you" diamond is always there on the right
        for j, line_ in enumerate(art.YOU["diamond"]):
            cv.text(youx - 2, youy - 2 + j, line_, P["pink"])
        cv.text(youx + 2, youy, '"you"', shade(P["pink"], 0.8))

        def particles(cv2, t0, t1, color, ch_set="+·"):
            if t < t0 or t > t1 + 0.5:
                return
            n = 16
            for i in range(n):
                u = ((t - t0) * 0.9 + i / n) % 1.0
                sx = cx + 6
                sy = h // 2 + int(math.sin(i * 1.7) * 3)
                x = int(sx + (youx - 4 - sx) * u)
                y = int(sy + (youy - 2 - sy) * u + math.sin(u * 6 + i) * 1.5)
                c = shade(color, 0.4 + 0.6 * (1 - u))
                cv2.put(x, y, ch_set[int(h01(i, int(t * 4)) * len(ch_set))], c)

        def label(cv2, idx, what, yield_):
            cv2.text(2, h - 3, "[ %02d ]" % idx, shade(P["grey"], 0.8))
            cv2.text(8, h - 3, what, P["white"])
            cv2.text(8 + sw(what) + 2, h - 3, "yield: " + yield_, shade(P["soft"], 0.8))
            for i in range(4):
                c = P["white"] if i <= idx else shade(P["grey_dim"], 0.8)
                cv2.put(w - 3 - (3 - i) * 2, h - 3, "◆" if i <= idx else "◇", c)

        # ---- eggplant ----------------------------------------------
        a = fade_window(t, t_egg - 0.25, t_tom + 0.45, 0.45, 0.45)
        if a > 0.01:
            def egg(cv2):
                egg_art = art.ART["eggplant"]
                ew = max(sw(l) for l in egg_art)
                x = cx - ew // 2
                y = h // 2 - len(egg_art) // 2 + 1
                for j, ln in enumerate(egg_art):
                    if j < 3:
                        cv2.text(x, y + j, ln, P["phos_dim"])
                    else:
                        cv2.text(x, y + j, ln, mix(P["violet"], P["magenta"], 0.35))
                particles(cv2, t_nut, t_tom, P["violet"], "·+")
                if t >= t_nut:
                    cv2.ctext(y - 2, "nutrients →", shade(P["violet"], 0.9))
                label(cv2, 1, "eggplant", "nutrients")
            stamp(cv, egg, a)

        # ---- tomato ------------------------------------------------
        a = fade_window(t, t_tom - 0.25, t_cat + 0.45, 0.45, 0.45)
        if a > 0.01:
            def tom(cv2):
                tm = art.ART["tomato"]
                ew = max(sw(l) for l in tm)
                x = cx - ew // 2
                y = h // 2 - len(tm) // 2 + 1
                for j, ln in enumerate(tm):
                    cv2.text(x, y + j, ln, mix(P["red"], P["rose"], 0.35))
                if t >= t_ant:
                    cv2.ctext(y - 2, "antioxidants →", P["rose"])
                particles(cv2, t_ant, t_cat, P["rose"], "o·")
                label(cv2, 2, "tomato", "antioxidants")
            stamp(cv, tom, a)

        # ---- cat ---------------------------------------------------
        a = fade_window(t, t_cat - 0.25, t_god + 0.45, 0.45, 0.45)
        if a > 0.01:
            def cat(cv2):
                ct = art.ART["cat"]
                ew = max(sw(l) for l in ct)
                x = cx - ew // 2
                y = h // 2 - len(ct) // 2 + 1
                col = mix(P["amber"], P["gold"], 0.4)
                for j, ln in enumerate(ct):
                    c = col if j not in (2, 4) else P["soft"]
                    cv2.text(x, y + j, ln, c)
                if t >= t_purr:
                    for i in range(6):
                        ph = t * 2.2 + i * 0.8
                        rr = (ph % 2.0)
                        for k in range(4):
                            px = x + ew + int(k * 2 + rr * 4)
                            py = y + 3 + int(math.sin(ph + k) * (k + 1) * 0.6)
                            cv2.put(px, py, "~", shade(P["amber"], 0.7 - k * 0.12))
                    s = "p u r r r r"
                    cv2.text(cx - len(s) // 2, y + len(ct) + 1, s,
                             mix(P["amber"], P["white"], 0.4 + 0.4 * math.sin(t * 6)))
                label(cv2, 3, "tabby cat", "purr")
            stamp(cv, cat, a)

        # ---- god ---------------------------------------------------
        a = fade_window(t, t_god - 0.25, self.t1 + 0.3, 0.5, 0.3)
        if a > 0.01:
            def god(cv2):
                r = max(4, min(w // 8, h // 3))
                gk = ramp(t, t_god, t_god + 1.0)
                # rays
                for i in range(20):
                    ang = t * 0.25 + i * math.pi / 10
                    rr = int((r + 1) * (1.2 + 0.25 * math.sin(t * 1.3 + i)))
                    px = cx + int(math.cos(ang) * rr * 1.8)
                    py = h // 2 - 2 + int(math.sin(ang) * rr / 1.5)
                    cv2.put(px, py, "·" if i % 2 else "✦",
                            shade(P["gold"], 0.35 + 0.5 * gk))
                # halo rings
                for d in range(3):
                    fx.circle(cv2, cx, h // 2 - 2, r + d * 2,
                              shade(P["gold"], 0.5 - d * 0.12), "·", ry=(r + d * 2) / 2)
                # head
                head = ["  ▄▄▄▄▄  ", " █ ◉   ◉ █ ", " █   ▄   █ ", " ▀███████▀ "]
                for j, ln in enumerate(head):
                    cv2.text(cx - 5, h // 2 - 3 + j, ln, P["gold"])
                # body
                body = ["╱▐█████▌╲", "  █████  ", " ╱██ ██╲ "]
                for j, ln in enumerate(body):
                    cv2.text(cx - 5, h // 2 + 1 + j, ln, mix(P["gold"], P["amber"], 0.5))
                # proof certificate
                if t >= t_proof - 0.1:
                    kk = ramp(t, t_proof - 0.1, t_proof + 0.7)
                    px, py = 3, h - 9
                    fx.panel(cv2, px, py, 30, 6, shade(P["gold"], 0.7), title="proof")
                    s1 = 'proof_of_existence'
                    s2 = '  = "you"   ✓'
                    if kk > 0.3:
                        cv2.text(px + 2, py + 2, s1, P["amber"])
                    if kk > 0.7:
                        cv2.text(px + 2, py + 3, s2, P["gold"])
                label(cv2, 4, "the only god", "existence")
            stamp(cv, god, a)

        fx.scanlines(cv, 0.88)
        fx.vignette(cv, 0.2)


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

        # ---------- gender switch -----------------------------------
        a = fade_window(t, t_gender - 0.2, t_whatever + 0.3, 0.4, 0.4)
        if a > 0.01:
            def gender(cv2):
                sc = 2 if w > 60 else 1
                swap = 0.5 + 0.5 * math.sin(t * 2.0)
                dx = int(6 * swap)
                # F sliding left<->right, M the other way
                y0 = cy - 6
                draw_banner(cv2, "F", y0, mix(P["pink"], P["white"], 0.2 * swap),
                            sc, cx=cx - 10 + dx)
                draw_banner(cv2, "M", y0, mix(P["cyan"], P["white"], 0.2 * (1 - swap)),
                            sc, cx=cx + 5 - dx)
                # symbols cycle
                syms = ["♀", "⚥", "♂"]
                idx = int(t * 1.6) % 3
                for i, s in enumerate(syms):
                    c = P["white"] if i == idx else shade(P["violet"], 0.5)
                    cv2.text(cx - 1 + (i - 1) * 4, cy + 5, s, c)
                cv2.ctext(cy + 7, "gender: undefined ⇄ any", shade(P["violet"], 0.8))
            stamp(cv, gender, a)

        # ---------- AM -> PM ----------------------------------------
        a = fade_window(t, t_whatever - 0.3, t_role + 0.3, 0.4, 0.4)
        if a > 0.01:
            def ampm(cv2):
                k = ramp(t, t_ampm - 0.2, t_ampm + 2.2)
                sc = 2 if w > 60 else 1
                # sky arc
                for i in range(24):
                    u = i / 23.0
                    ang = math.pi * (1 - u)
                    x = int(cx + math.cos(ang) * (w * 0.34) * -1)
                    y = cy + 3 - int(math.sin(ang) * (h * 0.26))
                    cv2.put(x, y, "·", shade(P["violet"], 0.25))
                u = k
                ang = math.pi * (1 - u)
                sx = int(cx + math.cos(ang) * (w * 0.34) * -1)
                sy = cy + 3 - int(math.sin(ang) * (h * 0.26))
                cv2.put(sx, sy, "☼" if k < 0.55 else "☾",
                        mix(P["amber"], P["ice"], max(0.0, (k - 0.5) * 2)))
                txt = "AM" if k < 0.5 else "PM"
                draw_banner(cv2, txt, cy - 4, mix(P["amber"], P["ice"], k), sc)
                cv2.ctext(cy + 8, "12:00 → 24:00", shade(P["soft"], 0.7))
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

        fx.scanlines(cv, 0.82)
        fx.vignette(cv, 0.3)


# ==========================================================================
# 7 · CHORUS 2 — vibrations / completion / abandonment
# ==========================================================================

class Chorus2Scene(Scene):
    key = "chorus2"
    accent = "ice"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_vib = cue("If I can feel your vibrations")
        t_comp = cue("Then I can finally be completion")
        t_left = cue("Though you have left")
        t_iso = cue("You have left me in isolation")
        cx = w // 2

        sync = ramp(t, t_vib - 0.3, t_comp + 1.2)     # 0..1 phase lock
        desat = ramp(t, t_left - 0.2, t_iso)          # colour drains
        y1 = h // 2 - 5
        y2 = h // 2 + 3

        # ---------- two heartbeats ----------------------------------
        if t < t_iso - 0.6:
            amp1 = min(4, h // 8)
            amp2 = amp1
            lost = ramp(t, t_comp + 1.0, t_left + 0.4)
            for x in range(w):
                u1 = (x * 0.045 + t * 1.05)
                v1 = fx.ecg(u1)
                cv2y = y1 - int(amp1 * v1)
                cv.put(x, cv2y, "·", P["rose"])
                # you: phase offset shrinks as they sync
                off = (1 - sync) * 0.16
                u2 = (x * 0.045 + t * 1.05 + off)
                v2 = fx.ecg(u2) * (1 - lost)
                y = y2 - int(amp2 * v2)
                cv.put(x, y, "·", mix(P["cyan"], P["grey_dim"], lost))
            cv.text(2, y1 - 2, "me", shade(P["rose"], 0.8))
            cv.text(2, y2 + 2, "you", mix(P["cyan"], P["grey"], lost))
            if t >= t_comp and lost < 0.5:
                kk = ramp(t, t_comp, t_comp + 1.0)
                cv.ctext(h // 2 - 1, "vibrations: locked ♥",
                         mix(P["white"], P["rose"], kk))
            if lost > 0.15:
                if int(t * 4) % 3:
                    cv.text(w - 24, y2 + 2, "you: signal lost", P["grey"])
                cv.hline(int(w * 0.1), y2, int(w * 0.8), "─", shade(P["grey_dim"], 0.8))

        # ---------- you leaves --------------------------------------
        if t >= t_left - 0.25:
            def leaving(cv2):
                steps = [(110.92, 0), (112.42, 1), (113.385, 2), (114.35, 3),
                         (115.315, 4), (116.28, 5)]
                n = 0
                for tt, idx in steps:
                    if t >= tt:
                        n = idx
                prog = ramp(t, t_left, t_iso)
                # path up-right
                px = int(cx + 14 + prog * (w * 0.34))
                py = int(h // 2 - 8 - prog * (h * 0.34))
                fade = 1.0 - prog * 0.75
                if t < t_iso:
                    for j, ln in enumerate(art.YOU["diamond"]):
                        cv2.text(px - 2, py - 2 + j, ln,
                                 shade(P["pink"], max(0.15, fade)))
                    # trailing echoes
                    for e in range(3):
                        ex = int(px - (e + 1) * 3)
                        ey = int(py + (e + 1) * 2)
                        cv2.put(ex, ey, "◇", shade(P["pink"], 0.25 - e * 0.06))
                # the word "left" drifting away
                for e in range(min(5, n)):
                    ex = int(w * 0.72 + e * 3)
                    ey = int(h * 0.18 + e * 2 + (t - t_left) * 3)
                    cv2.text(ex, ey, "left", shade(P["pink"], max(0.0, 0.55 - e * 0.1)))
                # me poses: reach -> reach2 -> sad
                pose = "reach" if n < 2 else ("reach2" if n < 4 else "sad")
                me = art.ME[pose]
                mx = cx - 4
                my = h - len(me) - 2
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln,
                             mix(P["phos"], P["grey"], desat * 0.9))
                if n >= 2:
                    cv2.text(mx + 9, my + 1, '..."you"?', shade(P["grey"], 0.7))
            stamp(cv, leaving, fade_window(t, t_left - 0.25, t_iso + 0.2, 0.3, 0.3))

        # ---------- isolation ---------------------------------------
        if t >= t_iso - 0.5:
            def iso(cv2):
                kk = ramp(t, t_iso - 0.5, t_iso + 0.5)
                bw = int(w * 0.7 - (w * 0.62) * kk)
                bh = int(h * 0.8 - (h * 0.6) * kk)
                bw = max(12, bw)
                bh = max(7, bh)
                x = cx - bw // 2
                y = h // 2 - bh // 2
                fx.bracket(cv2, x, y, bw, bh, mix(P["grey"], P["white"], 0.2),
                           style="<>")
                me = art.ME["sit"]
                for j, ln in enumerate(me):
                    cv2.text(cx - 4, h // 2 + 1 - len(me) + j, ln, P["grey"])
                if kk > 0.9 and int(t * 3) % 2 == 0:
                    cv2.ctext(y - 2, "ISOLATION", shade(P["white"], 0.7))
            stamp(cv, iso, fade_window(t, t_iso - 0.5, self.t1 + 0.3, 0.3, 0.2))

        if desat > 0:
            fx.desaturate(cv, min(1.0, desat * 1.1), 1.0 - 0.25 * desat)
        fx.scanlines(cv, 0.8)
        fx.vignette(cv, 0.25 + 0.25 * desat)


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

        # ---------- file list ---------------------------------------
        a = fade_window(t, t_erase - 0.4, t_maybe + 0.6, 0.4, 0.4)
        if a > 0.01:
            def files(cv2):
                px, py = max(2, int(w * 0.12)), max(2, int(h * 0.10))
                pw, phh = min(52, w - 2 * px), min(11, h - 4)
                fx.panel(cv2, px, py, pw, phh, shade(P["cyan"], 0.8),
                         title="~/world/mili/memories")
                rows = [
                    ("ac_dc.wav", 1.0), ("tangents.png", 2.0),
                    ("nutrients.dat", 3.0), ("purr.wav", 4.0),
                    ("god.ray", 5.0), ("you/", 6.0),
                ]
                for i, (name, ord_) in enumerate(rows):
                    at = t_erase + 0.35 + ord_ * 0.55
                    yy = py + 2 + i
                    if yy >= py + phh - 1:
                        break
                    cv2.text(px + 2, yy, "├─", shade(P["grey_dim"], 0.9))
                    if t < at:
                        cv2.text(px + 5, yy, name, shade(P["soft"], 0.9))
                        continue
                    k = ramp(t, at, at + 0.55)
                    if name == "you/":
                        if k > 0.4:
                            cv2.text(px + 5, yy, "you/", P["pink"])
                            err = "rm: cannot remove 'you': not empty"
                            if k > 0.75:
                                cv2.text(px + 5, yy + 1,
                                         err[:pw - 7], P["red"])
                        continue
                    diss = name[:max(0, len(name) - int(k * len(name)))]
                    cv2.text(px + 5, yy, diss, shade(P["grey"], 0.7))
                    if k > 0.35:
                        cv2.hline(px + 5, yy, len(name), "─", shade(P["red"], 0.7))
                    if k > 0.9:
                        cv2.text(px + 5, yy, "deleted", shade(P["grey_dim"], 0.9))
                cv2.text(px + 2, py + phh - 2, "$ rm -rf ./pointless/*",
                         shade(P["phos"], 0.75))
            stamp(cv, files, a)

        # ---------- hug the last fragment ---------------------------
        a = fade_window(t, t_maybe - 0.3, t_god + 0.3, 0.4, 0.4)
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
        t_trap = cue("Though we are trapped")
        cx = w // 2

        # storm rain
        fx.matrix_rain(cv, t * 1.2, shade(P["blood"], 0.5), density=0.22,
                       charset="✕†;", speed=20.0, seed=13, tail=4)

        # ---------- rows of programs being executed ------------------
        a = fade_window(t, t_give - 0.3, t_only + 1.2, 0.4, 0.6)
        if a > 0.01:
            def rows(cv2):
                sweep = (t * 0.55) % 1.0
                killed = 0
                for r in range(4):
                    y = 4 + r * 4
                    if y >= h - 8:
                        break
                    for i in range(w // 3):
                        x = 2 + i * 3
                        if x >= w - 2:
                            break
                        d = abs(x / w - sweep)
                        jen = h01(r, i, 21) < 0.75
                        if not jen:
                            continue
                        if d < 0.02:
                            ch, c = "▮", P["white"]
                        elif h01(r, i, 4) < sweep * 0.9:
                            ch, c = "✕", shade(P["blood"], 1.3)
                            killed += 1
                        else:
                            ch, c = "▮", shade(P["grey"], 0.6)
                        cv2.put(x, y, ch, c)
                if t >= t_give + 0.5:
                    cv2.text(2, h - 8, "executed: %04d" % (40 + int((t - t_give) * 90)),
                             shade(P["red"], 0.9))
                    cv2.text(2, h - 7, "them.all(execution) → done",
                             shade(P["grey"], 0.7))
            stamp(cv, rows, a)

        # ---------- me reaching for ghost-you -----------------------
        a = fade_window(t, t_only - 0.2, t_trap + 0.8, 0.4, 0.5)
        if a > 0.01:
            def reach(cv2):
                me = art.ME["reach2"]
                mx = cx - 4
                my = h - len(me) - 3
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, mix(P["phos"], P["white"], 0.3))
                if t >= t_back - 0.3:
                    kk = ramp(t, t_back - 0.3, t_back + 0.8)
                    flick = 0.45 + 0.4 * math.sin(t * 9) if t < t_back + 1.4 else 0.75
                    gx = cx
                    gy = 4
                    for j, ln in enumerate(art.YOU["ghost"]):
                        cv2.text(gx - 2, gy + j, ln, shade(P["ice"], kk * flick))
                    if kk > 0.8:
                        cv2.ctext(gy + 6, "you?", shade(P["ice"], 0.7))
                    # light between them
                    for i in range(6):
                        yy = int(my - 1 - i * 2)
                        cv2.put(cx, yy, "│", shade(P["ice"], 0.2 + 0.1 * i))
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
                # hearts creep along the wall
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
                # tiny ghost of you beside
                for j, ln in enumerate(art.YOU["small"]):
                    cv2.text(mx + 9, my + 2 + j, ln, shade(P["ice"], 0.7))
                if kk > 0.9:
                    cv2.ctext(y - 2, "trapped", shade(P["pink"], 0.85))
            stamp(cv, cage, fade_window(t, t_trap - 0.3, self.t1 + 0.3, 0.3, 0.2))

        fx.scanlines(cv, 0.78)
        fx.vignette(cv, 0.3)
        if t > t_trap:
            fx.desaturate(cv, 0.35 * ramp(t, t_trap, self.t1), 0.95)


# ==========================================================================
# 12 · OUTRO — algebra of love
# ==========================================================================

class OutroScene(Scene):
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
        t_trapped = cue("I am trapped")
        t_love = cue("Trapped in lo-o-ove")
        cx = w // 2

        # chalkboard
        board_x, board_y = 2, 2
        board_w, board_h = w - 4, h - 6
        cv.fill(board_x, board_y, board_w, board_h, " ", None, (18, 16, 14))
        cv.frame(board_x, board_y, board_w, board_h, shade(P["amber"], 0.45),
                 bg=(18, 16, 14), style="thin")
        chalk = mix(P["amber"], P["white"], 0.25)
        chalk_dim = shade(P["amber"], 0.55)

        # ---------- studying formulas -------------------------------
        if t < t_free - 0.4:
            formulas = [
                (t_study + 0.3, "love := Σ ( you → me )"),
                (t_proper + 0.2, "∂me/∂you > 0"),
                (t_proper + 1.1, "∀ stimulation ∃ satisfaction"),
                (t_ans + 0.3, "Q: what is love?"),
                (t_ans + 1.2, "A: you."),
            ]
            y = board_y + 2
            for at, s in formulas:
                if t < at:
                    break
                shown, typing = fx.typewriter(s, t - at, 40.0)
                col = chalk
                if s.startswith("Q:"):
                    col = mix(P["amber"], P["white"], 0.4)
                if s.startswith("A:"):
                    col = mix(P["pink"], P["white"], 0.3)
                cv.text(board_x + 3, y, shown, col)
                if typing and int(t * 16) % 2 == 0:
                    cv.put(board_x + 3 + sw(shown), y, "_", col)
                y += 2
            # little me studying, chalk in hand
            me = art.ME["idle"]
            mx = board_x + board_w - 14
            my = board_y + board_h - len(me) - 1
            for j, ln in enumerate(me):
                cv.text(mx, my + j, ln, shade(P["phos"], 0.85))
            cv.text(mx - 2, my - 1, "✎", chalk)

        # ---------- the algebraic expression ------------------------
        if t >= t_alg - 0.5 and t < t_free - 0.4:
            def alg(cv2):
                k = ramp(t, t_alg - 0.5, t_alg + 1.2)
                bw = min(40, w - 8)
                x = cx - bw // 2
                y = board_y + 3
                cv2.fill(x - 1, y - 1, bw + 2, 9, " ", None, (18, 16, 14))
                cv2.frame(x - 1, y - 1, bw + 2, 9, shade(P["amber"], 0.5),
                          bg=(18, 16, 14))
                rows = [
                    "love :  you  ×  me",
                    "─────────────────────",
                    "∃ you   ⇒   ∃ me",
                    "me.love(you) = me",
                ]
                for i, s in enumerate(rows):
                    if k < (i + 1) / 5.2:
                        break
                    xx = x + (bw - sw(s)) // 2
                    cv2.text(xx, y + i * 2, s,
                             mix(P["gold"], P["white"], 0.15 if i != 1 else 0.0))
            stamp(cv, alg, 1.0)
            # sparkle
            fx.sparkle(cv, cx, board_y + 6, t, P["gold"], seed=int(t * 5), n=6, rad=10)

        # ---------- free vs trapped --------------------------------
        if t >= t_free - 0.5:
            def split(cv2, ):
                pass
            def both(cv2):
                half = w // 2
                # left: you free, floating up
                k = ramp(t, t_free, t_love + 1.0)
                yx = half // 2
                yy = board_y + board_h - 4 - int(k * (board_h * 0.55))
                for j, ln in enumerate(art.YOU["diamond"]):
                    cv2.text(yx - 2, yy - 2 + j, ln, mix(P["pink"], P["white"], 0.3))
                for i in range(5):
                    a2 = t * 0.6 + i * 1.2
                    cv2.put(yx + int(math.cos(a2) * 6), yy + int(math.sin(a2) * 3),
                            "·", shade(P["pink"], 0.5))
                cv2.ctext(2, "you  are  free", mix(P["ice"], P["white"], 0.3))
                cv2.text(3, 2, " ", None)
                # right: me trapped in a heart cage
                bx = half + 3
                bw = min(24, w - bx - 2)
                bh = max(8, board_h - 6)
                by = board_y + 3
                fx.bracket(cv2, bx, by, bw, bh, shade(P["rose"], 0.9), style="<>")
                me = art.ME["sit"]
                mx = bx + bw // 2 - 4
                my = by + bh - len(me) - 1
                for j, ln in enumerate(me):
                    cv2.text(mx, my + j, ln, P["grey"])
                # hearts eat the cage
                kk = ramp(t, t_love - 0.3, t_love + 1.2)
                cells = []
                for i in range(1, bw - 1):
                    cells.append((bx + i, by))
                    cells.append((bx + i, by + bh - 1))
                for j in range(1, bh - 1):
                    cells.append((bx, by + j))
                    cells.append((bx + bw - 1, by + j))
                n = int(len(cells) * min(1.0, kk * 1.15))
                for i in range(n):
                    px, py = cells[(i * 7) % len(cells)]
                    cv2.put(px, py, "♥", mix(P["rose"], P["pink"], h01(i, 5)))
                cv2.ctext(2, "I  am  trapped", shade(P["pink"], 0.9))
                if t >= t_love + 0.2:
                    cv2.ctext(h // 2 + 3, "trapped in lo-o-ove",
                              mix(P["rose"], P["white"], 0.35))
            stamp(cv, both, fade_window(t, t_free - 0.5, self.t1 + 0.4, 0.6, 0.6))

        if t > t_love + 0.4:
            fx.desaturate(cv, 0.55 * ramp(t, t_love + 0.4, self.t1), 0.9)
        fx.scanlines(cv, 0.85)
        fx.vignette(cv, 0.25)


# ==========================================================================
# 13 · SHUTDOWN — process terminated
# ==========================================================================

class ShutdownScene(Scene):
    key = "shutdown"
    accent = "grey"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        tl = t - self.t0
        cx, cy = w // 2, h // 2
        lx = max(2, cx - 26)

        # ---------- CRT collapse at the very end ---------------------
        if tl >= 14.0:
            k = ramp(tl, 14.0, 15.2)
            band = 1.0 - min(1.0, k * 1.8)
            top = int(cy - (cy - 1) * band)
            bot = int(cy + (h - 2 - cy) * band)
            for y in range(h):
                if y < top or y > bot:
                    for x in range(w):
                        cv.ch[y][x] = " "
                        cv.fg[y][x] = None
            for y in (top, bot):
                if 0 <= y < h:
                    cv.hline(0, y, w, "▁" if y == bot else "▀",
                             shade(P["white"], 0.75))
            if k > 0.62:
                for y in range(h):
                    for x in range(w):
                        cv.ch[y][x] = " "
                        cv.fg[y][x] = None
                d = max(0.0, 1.0 - (k - 0.62) * 3.2)
                if d > 0.05:
                    cv.hline(0, cy, w, "─", shade(P["white"], d * 0.7))
                    cv.put(cx, cy, "·", shade(P["white"], d))
            fx.scanlines(cv, 0.8)
            return

        # ---------- faint rain while the process dies ---------------
        if tl < 5.0:
            fx.matrix_rain(cv, t * 0.35,
                           shade(P["phos_dim"], 0.16 * (1 - tl / 5.0)),
                           density=0.1, charset="01", seed=23, tail=3)

        # ---------- terminal lines ----------------------------------
        def tline(y, s, c, at, cps=44.0):
            if t < at:
                return False
            shown, typing = fx.typewriter(s, t - at, cps)
            cv.text(lx, y, shown[:max(4, w - 4)], c)
            if typing and int(t * 12) % 2 == 0:
                cv.put(lx + sw(shown), y, "▮", c)
            return typing

        dim_at = self.t0 + 7.0
        fade = 1.0 if t < dim_at else max(0.0, 1.0 - (t - dim_at) / 1.6)
        if fade > 0.01:
            tline(cy - 4, "[Process finished with exit code 0]",
                  shade(P["soft"], 1.0 * fade), self.t0 + 0.55)
            tline(cy - 2, "$ ", shade(P["phos"], 0.9 * fade), self.t0 + 1.5)
            if t > self.t0 + 1.5 and fade > 0.5:
                if int(t * 1.6) % 2 == 0:
                    cv.put(lx + 2, cy - 2, "▮", shade(P["white"], fade))
            tline(cy, "# everything that remains",
                  shade(P["grey_dim"], fade), self.t0 + 2.3)
            # the program's last act, typed by itself
            cmd = "me.execute(love);"
            at = self.t0 + 3.1
            if t >= at:
                shown, typing = fx.typewriter(cmd, t - at, 11.0)
                cv.text(lx + 2, cy - 2, shown, shade(P["white"], fade))
                if typing and int(t * 10) % 2 == 0 and fade > 0.5:
                    cv.put(lx + 2 + sw(shown), cy - 2, "▮", shade(P["red"], fade))
                if not typing:
                    tline(cy + 2, "[1] Terminated   world.execute(me);",
                          shade(P["grey"], fade), at + 1.5, cps=60.0)

        # ---------- long dark, only a cursor breathing --------------
        if self.t0 + 8.4 <= t < self.t0 + 12.6:
            e = ctx.e_at(t)
            kb = ramp(t, self.t0 + 8.4, self.t0 + 9.6)
            if int(t * 0.9) % 2 == 0 or e > 0.06:
                cv.put(cx, cy, "▮", shade(P["grey"], (0.35 + 1.6 * e) * kb))
            cv.ctext(cy + 2, "exit 0", shade(P["grey_dk"], kb))

        # ---------- the whisper -------------------------------------
        if t >= 205.0:
            k = ramp(t, 205.0, 206.4)
            s = "...execution."
            cv.ctext(cy, s, shade(P["grey"], 0.9 * k))
            if k > 0.5 and int(t * 1.6) % 2 == 0:
                cv.put(cx + sw(s) // 2 + 1, cy, "▮", shade(P["grey"], 0.55 * k))
            if t < 206.6:
                b = abs(math.sin((t - 205.0) * 2.4))
                cv.put(cx, cy - 3, "♥", shade(P["blood"], 0.25 + 0.6 * b))

        fx.scanlines(cv, 0.82)


# ==========================================================================
# 14 · END CARD
# ==========================================================================

class EndCardScene(Scene):
    key = "endcard"
    accent = "grey_dim"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        cx, cy = w // 2, h // 2
        k = ramp(t, self.t0 + 0.3, self.t0 + 2.2)
        if k <= 0:
            return
        c1 = shade(P["phos"], 0.55 * k)
        cv.ctext(cy - 3, "world.execute(me);", c1)
        cv.ctext(cy - 1, "Mili  ·  Miracle Milk (2016)", shade(P["grey"], 0.85 * k))
        cv.ctext(cy + 2, "thank you for executing me", shade(P["grey_dim"], 1.0 * k))
        cv.ctext(cy + 3, "感谢你执行我", shade(P["grey_dim"], 1.0 * k))
        # last cursor, stops blinking
        if t < 209.6:
            if int(t * 1.4) % 2 == 0:
                cv.text(cx + 3, cy + 5, "▮", shade(P["phos"], 0.5))
        fx.vignette(cv, 0.5 * k)
