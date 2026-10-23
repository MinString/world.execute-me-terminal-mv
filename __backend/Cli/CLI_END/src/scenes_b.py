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
                    k = ramp(t, t_ant, t_ant + 0.8)
                    tx2, ty2 = cx, y + len(tm) // 2
                    rx2 = ew // 2 + 4
                    ry2 = len(tm) // 2 + 2
                    # the antioxidant shield
                    for i in range(46):
                        ang = i * 0.137 + t * 0.45
                        px = tx2 + int(math.cos(ang) * rx2)
                        py = ty2 + int(math.sin(ang) * ry2 * 0.6)
                        c = shade(P["rose"], (0.25 + 0.35 * math.sin(t * 2.4 + i * 0.4)) * k)
                        cv2.put(px, py, "·" if i % 3 else "∘", c)
                    # reactive oxygen species (free radicals) closing in
                    scav = 0
                    for i in range(14):
                        ph = (t * 0.6 + h01(i, 92)) % 1.0
                        ang = h01(i, 93) * 6.283 + t * 0.2
                        dist = 1.75 - ph * 0.9
                        px = tx2 + int(math.cos(ang) * rx2 * dist)
                        py = ty2 + int(math.sin(ang) * ry2 * 0.62 * dist)
                        if ph < 0.86:
                            cv2.put(px, py, "✳" if h01(i, int(t * 5)) < 0.45 else "*",
                                    shade(mix(P["red"], P["amber"], 0.45), 0.9))
                        else:
                            scav += 1
                            cv2.put(px, py, "○", shade(P["ice"], 0.55))
                            cv2.put(px + (1 if h01(i, 95) < 0.5 else -1), py,
                                    "+", shade(P["phos"], 0.65))
                    cv2.ctext(y - 2, "·O₂⁻ + e⁻ → O₂   antioxidant shield",
                              mix(P["rose"], P["ice"], 0.2 + 0.3 * math.sin(t * 2)))
                    cv2.ctext(y + len(tm) + 1,
                              "radicals neutralised %3d / 999" % min(999, int((t - t_ant) * 9) + scav),
                              shade(P["ice"], 0.6))
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

        # ---------- gender switch: edit /etc/me.conf in place -------
        a = fade_window(t, t_gender - 0.2, t_whatever + 0.3, 0.4, 0.4)
        if a > 0.01:
            def gender(cv2):
                k = ramp(t, t_gender + 0.2, t_fm + 1.9)     # F -> M
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
                            aa = max(0.0, 1.0 - k * 1.15)
                            if aa > 0.03 and h01(i, j, 77) < 0.35 + aa * 0.65:
                                cv2.put(px + 3 + i, fy0 + j, ch,
                                        shade(P["pink"], aa))
                        for i, ch in enumerate(row_m):
                            if ch == " ":
                                continue
                            bb = max(0.0, (k - 0.12) * 1.15)
                            if bb > 0.03 and h01(i, j, 78) < 0.35 + bb * 0.65:
                                cv2.put(px + pw - 8 + i, fy0 + j, ch,
                                        shade(P["cyan"], bb))
                    # slider between the two letters
                    sx0, sx1 = px + 10, px + pw - 11
                    sy = fy0 + 2
                    if sx1 > sx0 + 4:
                        cv2.hline(sx0, sy, sx1 - sx0, "═", shade(P["grey"], 0.45))
                        kx = sx0 + int((sx1 - sx0) * min(1.0, max(0.0, k)))
                        cv2.put(kx, sy, "●", mix(P["pink"], P["cyan"], k))
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
                    cv2.put(px + 19, cy0, "Y" if k > 0.55 else "X",
                            shade(P["cyan"], 0.45 + 0.55 * k))
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
        fx.scanlines(cv, 0.85)
        fx.vignette(cv, 0.25)


# ==========================================================================
# 13 · SHUTDOWN — process terminated
# ==========================================================================

class ShutdownScene(Scene):
    """3:11 — the song is over but the process is still trapped: the last
    equation lingers, then the shell comes back and logs the exit."""

    key = "shutdown"
    accent = "grey"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        tl = t - self.t0
        cx, cy = w // 2, h // 2
        lx = max(2, cx - 26)
        compact = h <= 10

        # ---------- CRT collapse at the very end ---------------------
        if tl >= 15.0:
            k = ramp(tl, 15.0, 15.4)
            band = 1.0 - min(1.0, k * 1.6)
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
            if k > 0.7:
                for y in range(h):
                    for x in range(w):
                        cv.ch[y][x] = " "
                        cv.fg[y][x] = None
                d = max(0.0, 1.0 - (k - 0.7) * 3.0)
                if d > 0.05:
                    cv.hline(0, cy, w, "─", shade(P["white"], d * 0.7))
                    cv.put(cx, cy, "·", shade(P["white"], d))
            fx.scanlines(cv, 0.8)
            return

        # ---------- A · the cage after the song ----------------------
        if tl < 3.1:
            k = ramp(tl, 0.0, 2.8)
            ey = (max(3, h // 2 - 3) if not compact else 3)
            if not compact and h >= 16:
                cv.ctext(max(1, ey - 3),
                         "while (trapped) { love; }   /* no exit */",
                         shade(P["grey_dim"], 0.55 + 0.2 * (1 - k)))
            s2 = "love := Σ ( ♥ me ♥ )"
            x2 = max(2, cx - sw(s2) // 2)
            cv.text(x2, ey, s2, mix(P["rose"], P["grey_dim"], 0.7 * k))
            mp = x2 + sw("love := Σ ( ♥ ")
            for i in range(2):
                cv.put(mp + i, ey - 1 if ey > 1 else ey,
                       "♥", shade(P["rose"], 0.8 - 0.5 * k))
                cv.put(mp + i, ey + 1, "◆", shade(P["rose"], 0.6 - 0.4 * k))
            # petals falling out of the cage, and staying fallen
            npet = 9 if not compact else 4
            for i in range(npet):
                at = 0.25 + i * 0.18
                if tl < at:
                    continue
                age = tl - at
                yy = ey + 2 + int(age * (3.0 + 2.0 * h01(i, 7)))
                if yy > h - 2:
                    continue
                xx = mp + int((h01(i, 3) - 0.5) * 14) + \
                     int(math.sin(age * 3.0 + i) * 2.0)
                cv.put(xx, yy, "♥" if i % 3 else "·",
                       shade(P["rose"], max(0.0, 0.55 - 0.4 * k)))
            yy = min(h - 2, ey + (7 if not compact else 2))
            cv.fill(0, yy, w, 1, " ", None, None)
            shown, typing = fx.typewriter("state: trapped · free: ∅ · love: ∞",
                                          max(0.0, tl - 0.45), 30.0)
            cv.ctext(yy, shown, shade(P["grey"], 0.8))

        # ---------- B · the shell comes back -------------------------
        t_exit = self.t0 + 3.2
        t_cmd = self.t0 + 5.3
        t_kill = self.t0 + 6.8
        t_dark = self.t0 + 9.0
        fade = 1.0 if t < t_dark else max(0.0, 1.0 - (t - t_dark) / 1.2)
        if fade > 0.01:
            if compact:
                rows = [2, 3, 4, 5]
            else:
                rows = [max(2, cy - 4), max(2, cy - 2), max(2, cy),
                        max(2, cy + 2)]

            def tline(y, s, c, at, cps=44.0):
                if t < at or y >= h - 1:
                    return False
                shown, typing = fx.typewriter(s, t - at, cps)
                cv.fill(0, y, w, 1, " ", None, None)
                cv.text(lx, y, shown[:max(4, w - 4)], c)
                if typing and int(t * 12) % 2 == 0:
                    cv.put(lx + sw(shown), y, "▮", c)
                return typing

            tline(rows[0], "[Process finished with exit code 0]",
                  shade(P["soft"], fade), t_exit)
            # the program's last act, typed by itself at the prompt
            cmd = "me.execute(love);"
            if t < t_cmd:
                if not tline(rows[1], "$ ", shade(P["phos"], 0.9 * fade),
                             self.t0 + 3.9):
                    if t > self.t0 + 3.9 and fade > 0.4:
                        if int(t * 1.6) % 2 == 0:
                            cv.put(lx + 2, rows[1], "▮",
                                   shade(P["white"], fade))
            elif rows[1] < h - 1:
                shown, typing = fx.typewriter(cmd, t - t_cmd, 11.0)
                cv.fill(lx, rows[1], 26, 1, " ", None, None)
                cv.text(lx, rows[1], "$ ", shade(P["phos"], 0.9 * fade))
                cv.text(lx + 2, rows[1], shown, shade(P["white"], fade))
                if typing and int(t * 10) % 2 == 0 and fade > 0.4:
                    cv.put(lx + 2 + sw(shown), rows[1], "▮",
                           shade(P["red"], fade))
                if not typing:
                    tline(rows[2], "[1] Terminated   world.execute(me);",
                          shade(P["grey"], fade), t_kill, cps=60.0)
                    tline(rows[3], "# everything that remains: me.",
                          shade(P["grey_dim"], fade), t_kill + 0.85, cps=40.0)

        # ---------- C · long dark, only a cursor breathing ----------
        if self.t0 + 10.4 <= t < 205.81:
            e = ctx.e_at(t)
            kb = ramp(t, self.t0 + 10.4, self.t0 + 11.6)
            yb = min(h - 2, cy)
            if int(t * 0.9) % 2 == 0 or e > 0.06:
                cv.put(cx, yb, "▮", shade(P["grey"], (0.35 + 1.6 * e) * kb))
            cv.fill(0, yb + 2, w, 1, " ", None, None)
            cv.ctext(min(h - 2, yb + 2), "exit 0",
                     shade(P["grey_dk"], kb))

        # ---------- D · the whisper ---------------------------------
        if t >= 205.81:
            k = ramp(t, 205.81, 207.40)
            s = "...execution."
            yy = min(h - 2, max(3 if compact else cy, 3))
            cv.fill(0, yy, w, 1, " ", None, None)
            cv.ctext(yy, s, shade(P["grey"], 0.9 * k))
            if k > 0.5 and int(t * 1.6) % 2 == 0:
                cv.put(cx + sw(s) // 2 + 1, yy, "▮",
                       shade(P["grey"], 0.55 * k))
            b = abs(math.sin((t - 205.81) * 2.4))
            cv.put(cx, max(1, yy - 3), "♥", shade(P["blood"], 0.25 + 0.6 * b))

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
