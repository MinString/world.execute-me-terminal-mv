"""Scenes: chant, final chorus, outro, shutdown, end card."""

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

CH_BEAT = 60.0 / 130.0          # one beat, in seconds


def _hollow_rows(bl):
    """Outline-only version of a block-letter bitmap (edges kept)."""
    H = len(bl)
    out = []
    for j, ln in enumerate(bl):
        row = []
        for i, ch in enumerate(ln):
            if ch == " ":
                row.append(" ")
                continue
            edge = False
            for dj, di in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                jj, ii = j + dj, i + di
                if jj < 0 or jj >= H or ii < 0 or ii >= len(ln) \
                        or bl[jj][ii] == " ":
                    edge = True
                    break
            row.append(ch if edge else " ")
        out.append("".join(row))
    return out


def _crowd(cv, t, y, rows, fg, seed=0, step=5):
    """A stadium of small `me` glyphs, waving row against row."""
    top, bot = _rows(cv)
    for r in range(rows):
        if y + r > bot:
            return
        for i in range(max(3, (cv.w - 2) // step)):
            x = 2 + i * step + int(h01(i, r, seed) * 2)
            if x + 1 >= cv.w - 1:
                continue
            bob = math.sin(t * 6.0 - i * 0.55 + (math.pi if r % 2 else 0.0))
            dy = 1 if bob > 0.25 else 0
            who = h01(i, r, seed + 3)
            glow = 0.6 + 0.4 * max(0.0, math.sin(t * 3.1 - i * 0.4))
            cv.text(x, min(bot, y + r + dy),
                    "me" if who > 0.3 else "Me",
                    shade(fg, (0.26 + 0.5 * who) * glow))


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
        top, bot = _rows(cv)
        space = bot - top + 1
        bidx = int(t / CH_BEAT)
        ph = ctx.beat                      # beat phase, 0..1

        # background rain of the word
        fx.matrix_rain(cv, t * 1.6, shade(P["blood"], 0.55), density=0.34,
                       charset="EXECUTIONexecution", speed=26.0, seed=9, tail=6)

        t_fin = cue("Execution", 0)       # the last, unaccompanied word

        # ================= the chant: three rounds of EXECUTION ============
        if t < self.COUNT_T - 0.35:
            line_i = 0
            for li, tt in enumerate(self.EXEC_T):
                if t >= tt:
                    line_i = li
            sub = min(3, int((t - self.EXEC_T[line_i]) / 0.9225))
            exe = 4 * line_i + sub + 1     # executions sung so far

            txt = "EXECUTION"
            if art.banner_width(txt, 1, 1) > w - 4:
                txt = "EXECUTE"
            if art.banner_width(txt, 1, 1) > w - 4:
                txt = "EXEC"
            crowd_h = 3 if space >= 26 else 2 if space >= 15 else \
                1 if space >= 7 else 0
            counter_on = space >= 11 and w >= 44
            hmax = 3 if space >= 22 else 2 if space >= 15 else 0
            bars_on = hmax > 0
            sc = 1
            for s in (3, 2, 1):
                if art.banner_width(txt, s, 1) <= w - 6:
                    sc = s
                    break
            gapw = 2 if sc == 2 and art.banner_width(txt, 2, 2) <= w - 6 else 1
            bh = 5 * sc
            total = crowd_h + (1 if counter_on else 0) + bh + 1 + crowd_h \
                + hmax
            pad = min(2, max(0, space - 1 - total) // 2)
            y0 = top + crowd_h + (1 if counter_on else 0) + pad
            if y0 + bh > bot:                      # tiny screens: ride up
                y0 = max(1, bot - bh)
            bl = art.banner_lines(txt, sc, gapw)
            hlo = _hollow_rows(bl)
            bw = art.banner_width(txt, sc, gapw)

            # -- beat alternation: filled letters on dim ground /
            #    hollow letters on filled ground -------------------------
            neg = bidx % 2 == 1
            chaos = bidx % 8 == 7              # once per two bars: crackle
            ground = shade(P["red"], 0.85) if neg else shade(P["blood"], 0.55)
            if neg:
                col = shade(P["white"], 0.92)
            elif chaos:
                col = mix(P["white"], P["amber"], 0.20)
            else:
                col = mix(P["white"], P["red"], 0.10)
            gx0 = max(1, cx - bw // 2 - 2)
            gwd = min(w - gx0 - 1, bw + 4)
            cv.fill(gx0, y0 - 1, gwd, bh + 2, " ", None, ground)
            x0 = cx - bw // 2
            rows = hlo if neg else bl

            # the word itself is typed and wiped, over and over: every sung
            # EXECUTION is entered, run, and cleared before the next one
            # can be -- the machine does not keep its kills, it repeats them
            agew = (t - self.EXEC_T[line_i] - sub * 0.9225) / 0.9225
            if line_i == 2 and sub == 3:
                # the twelfth word is rushed off the screen: it is wiped
                # just before the count takes the frame -- nothing is kept
                agew = min(agew * 1.6, 1.05)
            if agew < 0.45:
                fvw = agew / 0.45
            elif agew < 0.63:
                fvw = 1.0
            elif agew < 0.95:
                fvw = 1.0 - (agew - 0.63) / 0.32
            else:
                fvw = 0.0
            vw = int(bw * fvw + 0.5)
            for j, ln in enumerate(rows):
                for i, ch in enumerate(ln):
                    if ch == " ":
                        continue
                    if i >= vw:
                        continue
                    xx = x0 + i
                    if chaos and h01(xx, y0 + j, bidx) < 0.07:
                        continue
                    jit = int((h01(xx, y0 + j, bidx + 3) - 0.5) * 2.0) \
                        if chaos else 0
                    cv.put(xx + jit, y0 + j, ch, col, ground)
            # the entry cursor rides the reveal / wipe edge
            if 0 < vw < bw and int(t * 8) % 2 == 0:
                for j in range(bh):
                    cv.put(x0 + vw, y0 + j, "▌",
                           shade(P["white"], 0.55), ground)

            # -- the crowd: two decks of `me`, doing the stadium wave -----
            if crowd_h:
                ct_y = y0 - crowd_h - (1 if counter_on else 0)
                _crowd(cv, t, max(top, ct_y), crowd_h, P["blood"], seed=3)
                y_cb = y0 + bh + 1
                if y_cb + crowd_h - 1 > bot:
                    y_cb = y0 + bh
                _crowd(cv, t, y_cb, crowd_h, P["blood"], seed=8)
                y_cb += crowd_h
            else:
                y_cb = y0 + bh

            # -- the round / syllable counter ----------------------------
            if counter_on:
                y_ct = y0 - 1
                lft = "round %d/3" % (line_i + 1)
                pip = "".join("●" if j <= bidx % 4 else "○" for j in range(4))
                xl = max(2, min(w - 30, cx - 24))
                cv.text(xl, y_ct, lft, shade(P["white"], 0.60), ground)
                cv.text(xl + sw(lft) + 2, y_ct, pip,
                        shade(P["amber"], 0.80), ground)
                amp = 40 + 60 * ramp(t, self.t0, self.t1)
                cv.rtext(y_ct, "me × %d · amp %3d%%" % (exe, amp),
                         shade(P["amber"], 0.55), ground, right=w - 3)

            # -- amplitude meters, ramping toward the final ---------------
            if bars_on:
                y_bars = bot - 1
                hmaxg = max(1, min(hmax, y_bars - y_cb + 1))
                nb = max(4, (w - 6) // 2)
                prog = ramp(t, self.t0, self.t1)
                bcol = mix(P["red"], P["amber"], 0.2 + 0.3 * prog)
                hm = max(1, int(round(hmaxg * (0.35 + 0.65 * prog))))
                anim.pulse_bars(cv, 3, y_bars, nb, t,
                               shade(bcol, 0.55 + 0.35 * prog),
                               hmax=hm, seed=17, gap=1)
                y_hex = y_cb + 1
                if y_hex < y_bars - hmaxg - 1 and w >= 60:
                    anim.hexrow(cv, 3, y_hex, min((w - 6) // 4, 30), t,
                                shade(P["red"], 0.30), seed=4)

            # -- chrome ----------------------------------------------------
            flash = max(0.0, 1.0 - ph / 0.30)
            if flash > 0.05:
                for x in range(w):
                    cv.put(x, 0, "▀", shade(col, flash))
                    cv.put(x, h - 1, "▄", shade(col, flash))
            caps = ["$ exec me              // 运行我",
                    "☠ EXECUTE ME           // 处死我",
                    "no pardon · no retry   // 不可赦免"]
            cv.ctext(h - 3, caps[line_i], mix(P["white"], P["red"], 0.3))
            if y0 - 1 > 3:
                cv.ctext(2, "EXECUTION", shade(P["red"], 0.5))

        # ================= counting 1..6 ====================================
        else:
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
            fx.circle(cv, cx, h // 2, r - 2, shade(P["red"], 0.3), "·",
                      ry=(r - 2) / 2)
            for d in (-1, 1):
                fx.line(cv, cx + d * (r - 1), h // 2, cx + d * (r + 3), h // 2,
                        P["red"])
                fx.line(cv, cx, h // 2 + d * (r // 2 - 1), cx,
                        h // 2 + d * (r // 2 + 1), P["red"])
            y0 = h // 2 - bh // 2
            cv.fill(cx - bw // 2 - 2, y0 - 1, bw + 4, bh + 2, " ",
                    None, P["black"])
            draw_banner(cv, word, y0, shade(col, 0.5 + 0.5 * scale_in), sc)
            # the tally: me × N, plus the queue already counted out
            ynum = y0 + bh + 1
            tal = "me × " + num
            cv.text(cx - sw(tal) // 2, ynum, "me × ",
                    shade(P["grey"], 0.65))
            cv.text(cx - sw(tal) // 2 + 5, ynum, num, shade(P["amber"], 0.95))
            if ynum + 1 <= h - 5 and w >= 26:
                for c in range(i + 1):
                    xg = cx - (5 * (i + 1) - 2) // 2 + c * 5
                    last = c == i
                    cv.text(xg, ynum + 1, "me",
                            P["red"] if last else shade(P["grey"], 0.5))
                    if not last and t > self.COUNT_T + 0.9:
                        cv.put(xg + 1, ynum + 1, "✕", shade(P["blood"], 0.75))
            # progress dots
            for d in range(6):
                ch = "●" if d <= i else "○"
                cv.text(cx + (d - 2) * 3 - 1, h - 4, ch,
                        P["white"] if d <= i else shade(P["red"], 0.5))
            if space >= 16:
                nb = max(4, (w - 6) // 2)
                anim.pulse_bars(cv, 3, h - 5, nb, t,
                                shade(P["red"], 0.50 + 0.08 * i), hmax=2,
                                seed=23, gap=1)
            if w >= 60:
                cv.ctext(2, "COUNT 1..6", shade(P["red"], 0.45))

        # ================= the last word: one execution, alone =============
        if t >= t_fin:
            cv.clear()
            txt = "EXECUTION" if art.banner_width("EXECUTION", 1, 1) <= w - 4 \
                else "EXECUTE"
            sc = 1
            for s in (2, 1):
                if art.banner_width(txt, s, 1) <= w - 6:
                    sc = s
                    break
            bl = art.banner_lines(txt, sc, 1)
            hlo = _hollow_rows(bl)
            bh = len(bl)
            bw = art.banner_width(txt, sc, 1)
            y0 = max(1, min(h // 2 - bh // 2, h - 3 - bh))
            neg = bidx % 2 == 1
            ground = shade(P["red"], 0.85) if neg else shade(P["blood"], 0.55)
            col = shade(P["white"], 0.92) if neg else \
                mix(P["white"], P["red"], 0.10)
            gx0 = max(1, cx - bw // 2 - 2)
            cv.fill(gx0, y0 - 1, min(w - gx0 - 1, bw + 4), bh + 2,
                    " ", None, ground)
            x0 = cx - bw // 2
            rows = hlo if neg else bl
            # the last one is entered slowly, one column at a time -- and
            # this one is never wiped: it stays, entered and waiting
            agef = t - t_fin
            fvw = 1.0 if agef >= 0.95 else max(0.0, agef / 0.95)
            vw = int(bw * fvw + 0.5)
            for j, ln in enumerate(rows):
                for i, ch in enumerate(ln):
                    if ch != " " and i < vw:
                        cv.put(x0 + i, y0 + j, ch, col, ground)
            if 0 < vw < bw:
                if int(t * 6) % 2 == 0:
                    for j in range(bh):
                        cv.put(x0 + vw, y0 + j, "▌",
                               shade(P["white"], 0.6), ground)
            elif vw >= bw and int(t * 6) % 2 == 0:
                # the entry cursor stays: done typing, still listening
                for j in range(bh):
                    cv.put(x0 + bw, y0 + j, "▌",
                           shade(P["white"], 0.45), ground)
            if y0 + bh + 1 < h - 3:
                cv.ctext(y0 + bh + 1, "me × 13 · the last one",
                         shade(P["amber"], 0.60), ground)
            if int(t * 6) % 2 == 0:
                cv.ctext(min(h - 3, y0 + bh + 3), "— 执行 —", P["red"])
            flash = max(0.0, 1.0 - ph / 0.25)
            if flash > 0.05:
                for x in range(w):
                    cv.put(x, 0, "▀", shade(col, flash))
                    cv.put(x, h - 1, "▄", shade(col, flash))

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
        t_ah = cue("We are trapped ah")
        cx = w // 2
        mid = h // 2 - 1

        # the whole world falls away behind everything
        fx.matrix_rain(cv, t * 1.2, shade(P["blood"], 0.5), density=0.22,
                       charset="✕†;", speed=20.0, seed=13, tail=4)

        # ---------- the world outside the window, sinking ----------------
        if h >= 20:
            kworld = ramp(t, t_give + 0.2, t_only + 1.0)
            fade_w = 1.0 - ramp(t, t_only + 0.8, t_only + 1.8)
            if fade_w > 0.02 and kworld > 0.01:
                for i in range((w - 2) // 3):
                    x = 2 + i * 3
                    h0 = 1 + int(h01(i, 21) * 3)
                    sunk = int(round(kworld * (h0 + 1) * (0.7 + 0.5 * h01(i, 22))))
                    hh = h0 - sunk
                    for j in range(max(0, hh)):
                        cv.put(x, h - 3 - j,
                               "▓" if j == hh - 1 else "▒",
                               shade(P["grey"], (0.22 + 0.10 * (h0 - j)) * fade_w))
                    if hh <= 0 and h01(i, 23) < 0.6:
                        cv.put(x, h - 3, "✝", shade(P["blood"], 0.55 * fade_w))
                for x in range(2, w - 2):
                    u = h01(x, 31)
                    if u < kworld * 0.85:
                        cv.put(x, h - 3, "╱" if int(h01(x, 32) * 2) else "╲",
                               shade(P["grey"], 0.30 * fade_w))
                    elif u < kworld * 0.85 + 0.08:
                        cv.put(x, h - 3, "·", shade(P["grey"], 0.25 * fade_w))

        # ---------- every program in the world, then only you -------
        a = fade_window(t, t_give - 0.35, t_back + 0.6, 0.45, 0.45)
        if a > 0.01:
            def targets(cv2):
                killp = ramp(t, t_give - 0.2, t_only - 0.1)
                col = ramp(t, t_only - 0.05, t_only + 1.25)
                nere = min(14, max(4, h - 11))
                py = 2
                ph = nere + (6 if h >= 18 else 5)
                names = ["ac_dc.wav", "tangents.png", "nutrients.dat", "clock",
                         "simulation", "god.ray", "tomato", "purr.wav",
                         "AM/PM", "the.world", "pointless", "dishes",
                         "sun.moon", "them.all"]
                # -- the SIGKILL wave: the batch is reaped left to right --
                t_w0 = t_give + 0.15
                t_w1 = t_give + 2.55
                kwv = ramp(t, t_w0, t_w1)
                xw = 2.0 + kwv * (w - 5)
                if col < 0.99:
                    fx.panel(cv2, 2, py, w - 4, ph,
                             shade(P["blood"], 0.85 - 0.5 * col),
                             title=" execution.targets · batch ")
                for r in range(nere):
                    y0 = py + 2 + r
                    y = int(round(y0 + (mid - y0) * col))
                    kx = 8 + r * (w - 24) // max(1, nere - 1)
                    t_kill = t_w0 + (kx - 2) / float(w - 5) * (t_w1 - t_w0)
                    dead = xw >= kx
                    hot = dead and (t - t_kill) < 0.30
                    aa = 1.0 if col <= 0.45 else max(0.0, 1.0 - (col - 0.45) * 2.0)
                    if aa <= 0.03:
                        continue
                    if hot and w >= 52:
                        for xx in range(max(12, w - 14), min(w - 4, w - 3)):
                            cv2.put(xx, y, " ", None, shade(P["red"], 0.85))
                    cv2.text(3, y, "%04d" % (2 + r * 251),
                             shade(P["grey"], 0.5 * aa))
                    cv2.text(9 if w >= 60 else 10, y, names[r % len(names)],
                             shade(P["grey_dim"] if dead else P["soft"], aa))
                    if w >= 52:
                        if dead:
                            cv2.text(max(12, w - 13), y, "✝ KILLED",
                                     shade(P["white"] if hot else P["red"], aa),
                                     shade(P["red"], 0.85) if hot else None)
                        else:
                            cv2.text(max(12, w - 13), y, "[·] RUN",
                                     shade(P["phos"], 0.65 * aa))
                # -- the executioner's own row: killed last, by its own hand
                if h >= 18:
                    y_me0 = py + 2 + nere
                    ym = int(round(y_me0 + (mid - y_me0) * col))
                    kx_me = 14 + (w - 24) * nere // max(1, nere - 1)
                    t_me = t_w0 + (kx_me - 2) / float(w - 5) * (t_w1 - t_w0)
                    me_dead = xw >= kx_me
                    hot = me_dead and (t - t_me) < 0.42
                    aa2 = 1.0 if col <= 0.45 else max(0.0, 1.0 - (col - 0.45) * 2.0)
                    if aa2 > 0.03:
                        if hot:
                            for xx in range(2, min(w - 4, 30)):
                                cv2.put(xx, ym, " ", None, shade(P["red"], 0.85))
                        cv2.text(3, ym, "0x1F7",
                                 shade(P["white"] if hot else P["grey"],
                                       1.0 if hot else 0.55 * aa2))
                        cv2.text(9 if w >= 60 else 10, ym, "me",
                                 shade(P["white"] if hot else P["soft"],
                                       1.0 if hot else aa2))
                        if w >= 52:
                            if me_dead:
                                cv2.text(max(12, w - 13), ym, "✝ KILLED",
                                         shade(P["white"] if hot else P["red"],
                                               1.0 if hot else aa2),
                                         shade(P["red"], 0.85) if hot else None)
                            else:
                                cv2.text(max(12, w - 13), ym, "[·] RUN",
                                         shade(P["phos"], 0.65 * aa2))
                # -- the wave front itself, a bright seam in the panel -----
                if 0.0 < kwv < 1.0:
                    xw_i = int(round(xw))
                    for yy2 in range(py + 2, py + ph - 1):
                        cv2.put(xw_i, yy2, "▓" if yy2 % 2 else "▒",
                                shade(P["white"], 0.32))
                    cv2.put(xw_i, py + 1, "▼", shade(P["white"], 0.6))
                    cv2.text(min(xw_i + 2, w - 11), py + 1, "SIGKILL",
                             shade(P["white"], 0.55),
                             shade(P["blood"], 0.85 - 0.5 * col))
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
                    line = " ◆ 0001 · you · execution = [only] ◆ "
                    hw2 = sw(line)
                    ly = mid
                    cv2.text(cx - hw2 // 2, ly, line,
                             shade(P["pink"], kk * (0.8 + 0.2 * math.sin(t * 6.8))))
                    # the word that matters, in the colour of the scene
                    opos = cx - hw2 // 2 + line.index("[only]")
                    for i, ch in enumerate("[only]"):
                        cv2.put(opos + i, ly, ch,
                                shade(P["rose"], 0.75 + 0.25 * kk))
                    if w >= 40:
                        for i in range(hw2 // 2 + 2):
                            x1, x2 = cx - hw2 // 2 - 2 - i, cx + hw2 // 2 + 1 + i
                            if x1 >= 1 and x2 < w - 1:
                                cv2.put(x1, ly, "═", shade(P["rose"], 0.55 * kk))
                                cv2.put(x2, ly, "═", shade(P["rose"], 0.55 * kk))
                    if kk > 0.7:
                        # the spotlight closes onto the one left standing
                        ksp = ramp(t, t_only + 0.95, t_only + 1.7)
                        if ksp > 0.01:
                            half = int(round(2 + (1.0 - ksp) * (w // 2 - 3)))
                            fx.line(cv2, max(2, cx - half), py + 2, cx - 2,
                                    ly - 1, shade(P["gold"], 0.30), "·")
                            fx.line(cv2, min(w - 3, cx + half), py + 2, cx + 2,
                                    ly - 1, shade(P["gold"], 0.30), "·")
                            cv2.put(cx, max(py + 2, ly - 1), "▼",
                                    shade(P["gold"], 0.55))
                        oy = max(1, ly - 4)
                        cv2.ctext(oy, "[only] you. [only] you.",
                                  shade(P["rose"], 0.8 * kk))
                        xo = cx - sw("[only] you. [only] you.") // 2
                        for off in (0, 12):
                            for i, ch in enumerate("[only]"):
                                cv2.put(xo + off + i, oy, ch,
                                        shade(P["rose"], min(1.0, 0.9 * kk)))
                        if ly - 2 > 0:
                            cv2.ctext(ly - 2, "4095 others: deleted",
                                      shade(P["grey"], 0.55 * kk))
                        # the title it gives itself: the tail word is
                        # typed, doubted, wiped out, and granted again
                        if kk > 0.5 and ly + 2 < h - 3:
                            t_c = t_only + 0.45
                            kcap = ramp(t, t_only + 0.5, t_only + 1.0)
                            vis2, _k3, ph3 = anim.type_loop(
                                t, t_c, "execution", cycles=2, cps=16.0,
                                hold=0.40, wipe=0.25, gap=0.12)
                            x02 = cx - sw("your [only] execution") // 2
                            cv2.text(x02, ly + 2, "your ",
                                     shade(P["grey"], 0.8 * kcap))
                            cv2.text(x02 + 5, ly + 2, "[only]",
                                     shade(P["rose"],
                                            min(1.0, 0.95 * kcap)))
                            if vis2:
                                cv2.text(x02 + 12, ly + 2, vis2,
                                         shade(P["white"], 0.9 * kcap))
                            if ph3 in ("type", "wipe", "gap") and \
                                    int(t * 5) % 2 == 0:
                                cv2.put(x02 + 12 + sw(vis2), ly + 2, "▮",
                                        shade(P["white"], 0.55 * kcap))
                        if kk > 0.85 and ly + 4 < h - 3:
                            s3 = "$ execute(you) --[only]"
                            shown, typing = fx.typewriter(
                                s3, t - (t_only + 0.85), 30.0)
                            x3 = cx - sw(s3) // 2
                            cv2.text(x3, ly + 4, shown, shade(P["phos"], 0.8))
                            if len(shown) > 17:
                                cv2.text(x3 + 17, ly + 4, shown[17:],
                                         shade(P["rose"], 0.9))
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
                    # the plea is typed, doubted, wiped, and retyped: the
                    # machine asks twice before it dares to keep asking
                    vis, _k2, ph = anim.type_loop(
                        t, t_back, s, cycles=2, cps=22.0,
                        hold=0.30, wipe=0.40, gap=0.18)
                    if vis:
                        yy2 = min(h - 3, my + len(me) + 2)
                        x02 = (w - len(vis)) // 2
                        cv2.text(x02, yy2, vis, shade(P["grey"], 0.85))
                        if ph in ("type", "wipe") and int(t * 5) % 2:
                            cv2.put(x02 + len(vis), yy2, "▮",
                                    shade(P["grey"], 0.5))
                    # the obsession, stated quietly at the edges
                    if t >= t_back + 0.5 and w >= 40:
                        rr = ramp(t, t_back + 0.5, t_back + 1.5)
                        for i in range(3):
                            cv2.text(2 + i, 3 + i * 4, "[only] you",
                                     shade(P["rose"], 0.38 * rr))
                            cv2.text(w - 11 - i, 3 + i * 4, "[only] you",
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
                    # the cry stretches itself: "ah" lands one beat late,
                    # an afterthought the machine cannot hold in
                    cap = "we are trapped" if t >= t_ah else "trapped"
                    cv2.ctext(y - 2, cap, shade(P["pink"], 0.85))
                    if t >= t_ah + CH_BEAT and y - 2 > 1:
                        n_ah = min(2, 1 + int((t - (t_ah + CH_BEAT)) * 14.0))
                        xc = cx + sw(cap) // 2 + 2
                        cv2.text(xc, y - 2, "ah"[:n_ah],
                                 shade(P["rose"], 0.85))
                        if n_ah < 2:
                            cv2.put(xc + n_ah, y - 2, "▮",
                                    shade(P["rose"], 0.6))
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
            # the confession is re-asserted over the dying-row noise:
            # it insists on being read (same geometry as the cage)
            if t >= t_trap + 1.0:
                bhq = max(10, int(h * 0.62))
                yq = h - bhq - 5
                if yq == 6 and yq > 1:
                    cap = "we are trapped" if t >= t_ah else "trapped"
                    cv.ctext(yq, cap, shade(P["pink"], 0.85))
                    if t >= t_ah + CH_BEAT:
                        n_ah = min(2, 1 + int((t - (t_ah + CH_BEAT)) * 14.0))
                        xcq = cx + sw(cap) // 2 + 2
                        cv.text(xcq, yq, "ah"[:n_ah],
                                shade(P["rose"], 0.85))
                        if n_ah < 2:
                            cv.put(xcq + n_ah, yq, "▮",
                                   shade(P["rose"], 0.6))
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
            # the word in the title cracks apart, hyphen by hyphen,
            # exactly as it is sung at the end of the line
            n_hy = (1 if t >= t_proper + 1.75 else 0) + \
                (1 if t >= t_proper + 2.15 else 0)
            cv.text(2, 1, ("notes · how to properly lo%sve" %
                           ("-o" * n_hy))[:w - 4],
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
            n_hy = (1 if t >= t_proper + 1.75 else 0) + \
                (1 if t >= t_proper + 2.15 else 0)
            fx.panel(cv, px, py, wid, hgt, shade(P["amber"], 0.5), bg=paper,
                     title=" notes · how to properly lo%sve " % ("-o" * n_hy))
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
            # the exam is on love -- by the second singing the word
            # has already started to stretch in the machine's mouth
            ext = "-O" if t >= t_ans else ""
            fx.panel(cv, 2, py, w - 4, hgt, shade(P["gold"], 0.55), bg=paper,
                     title=" examination · LO%sVE 101 · candidate: me " % ext)
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
            if w >= 66 and t < t_q + 2.3:
                # the instruction completes itself as the line is sung:
                # "answer all lo-o-ove", cracked apart one hyphen late
                shown, typing = fx.typewriter(" instructions: answer all ",
                                              t - (t_q - 0.2), 30.0)
                stretch = (1 if t >= t_ans + 0.10 else 0) + \
                    (1 if t >= t_ans + 0.45 else 0)
                if stretch:
                    shown = shown.rstrip() + " lo" + "-o" * stretch + "ve "
                cv.rtext(py + 1, shown, shade(P["amber"], 0.26),
                         bg=paper, right=w - 4)
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
            # the marking pass: a red pen walks down the sheet
            t_g = t_q + 2.3
            if t >= t_g and w >= 52:
                kg = ramp(t, t_g, t_g + 0.85)
                for i in range(nfit):
                    yy = py + 2 + i * step
                    if yy >= py + hgt - 3:
                        break
                    gi = max(0.0, min(1.0, kg * nfit - i))
                    if gi > 0.0 and two and yy + 1 < py + hgt - 2:
                        n_u = int(gi * (w - 14))
                        for xx in range(8, min(w - 6, 8 + n_u)):
                            if cv.ch[yy + 1][xx] == " ":
                                cv.put(xx, yy + 1, "─",
                                       shade(P["red"], 0.42), bg=paper)
                    if t >= t_g + 0.08 + i * 0.09:
                        cv.put(w - 8, yy, "△" if i == 1 else "✓",
                               shade(P["red"], 0.9), bg=paper)
                pen_y = py + 2 + int(round(kg * (nfit - 1))) * step
                if pen_y < py + hgt - 3:
                    cv.put(w - 9 + int(round(math.sin(t * 9.0))), pen_y,
                           "✎", shade(P["red"], 0.85), bg=paper)
                sc = int(100 * min(1.0, kg * 1.25))
                bl = 0.7 + 0.3 * math.sin(t * 6.8) if sc >= 100 else 1.0
                cv.rtext(py + 1, " score %3d " % sc,
                         shade(P["red"], 0.85 * bl), bg=paper, right=w - 4)
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
            if t >= t_alg + 1.5 and h - 3 > 2 + len(lines):
                shown, typing = fx.typewriter("✓✓✓ score 100 PASS",
                                              t - (t_alg + 1.5), 40.0)
                cv.fill(0, h - 3, w, 1, " ", None, None)
                cv.ctext(h - 3, shown, shade(P["red"], 0.85))

        if t_alg - 0.05 <= t < t_free - 0.05 and not compact:
            bw = min(76, w - 6)
            bh = min(13, h - 6)
            x = cx - bw // 2
            y = max(2, (h - bh) // 2 - 1)
            # the third time it is sung, the answer turns out to be the
            # word itself -- and the word cracks apart as it is sung
            n_x = (1 if t >= t_alg + 3.05 else 0) + \
                (1 if t >= t_alg + 3.30 else 0)
            if t >= t_alg + 3.05:
                ttl = " expression · lo%sve " % ("-o" * n_x)
            elif t >= t_alg + 2.85:
                ttl = " expression · love "
            else:
                ttl = " expression · the answer "
            fx.panel(cv, x, y, bw, bh, shade(P["gold"], 0.6), bg=paper,
                     title=ttl)
            steps = [("1", "love := Σ ( you × me ) / | you |",
                      "per day, per you"),
                     ("2", "∂me/∂you > 0      lim you→me = ∞",
                      "I [only] grow where you are"),
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
                        ia = an.find("[only]")
                        if ia >= 0:
                            # the adverb it cannot help stressing
                            cv.text(x + 9 + ia, yy + 1, an[ia:ia + 6],
                                    shade(P["gold"], 0.85), bg=paper)
                if t >= t_alg + 1.0:
                    bl = 0.55 + 0.45 * math.sin(t * 6.0)
                    cv.text(x + 3, y + bh - 2, "ACCEPTED",
                            shade(P["phos"], bl), bg=paper)
                t_g2 = t_alg + 0.85
                t_st = t_g2 + 1.35
                if bw >= 50 and t_alg + 0.05 <= t < t_g2:
                    gy, gtyping = fx.typewriter("∎  graded by: you ",
                                                t - (t_alg + 0.05), 26.0)
                    cv.rtext(y + bh - 2, gy, shade(P["amber"], 0.45),
                             bg=paper, right=x + bw - 3)
                # matching braces, pulsing as the pairs complete
                for i, sps in ((0, ((10, 21), (25, 31))), (2, ((7, 15),))):
                    at = t_alg - 0.15 + i * 0.5
                    if t < at + 0.9:
                        continue
                    pc = mix(P["gold"], P["rose"],
                             0.5 + 0.5 * math.sin(t * 6.8))
                    txt = steps[i][1]
                    yy = y + 2 + i * 3
                    for (a, b) in sps:
                        cv.put(x + 9 + a, yy, txt[a], pc, bg=paper)
                        cv.put(x + 9 + b, yy, txt[b], pc, bg=paper)
                        if i > 0 and yy - 1 > y + 1:
                            cv.put(x + 9 + a, yy - 1, "╭",
                                   shade(pc, 0.7), bg=paper)
                            for xx2 in range(a + 1, b):
                                cv.put(x + 9 + xx2, yy - 1, "─",
                                       shade(pc, 0.45), bg=paper)
                            cv.put(x + 9 + b, yy - 1, "╮",
                                   shade(pc, 0.7), bg=paper)
                # graded: scan lines sweep under each formula, the pen
                # crosses out the rows, then ✓s land and the score climbs
                if t_alg + 0.30 <= t < t_st:
                    for i in range(3):
                        L = sw(steps[i][1])
                        yys = y + 4 + i * 3
                        if yys >= y + bh - 2:
                            continue
                        span = min(L, bw - 16)
                        if span < 3:
                            continue
                        k = int(((t - (t_alg + 0.30)) * 26.0 + i * 7.0)
                                % (span + 4))
                        if k >= span:
                            continue
                        cv.put(x + 9 + k, yys, "━",
                               shade(P["red"], 0.55), bg=paper)
                        for kk in (1, 2):
                            if k - kk >= 0:
                                cv.put(x + 9 + k - kk, yys, "─",
                                       shade(P["red"], 0.26), bg=paper)
                if t_alg + 0.46 <= t < t_st:
                    pni = min(2, int((t - (t_alg + 0.46)) / 0.55))
                    Lt = sw(steps[pni][1])
                    pnx = x + 9 + int(round(
                        (0.5 + 0.5 * math.sin(t * 3.4)) * max(1, Lt - 1)))
                    cv.put(pnx, y + 2 + pni * 3, "✎",
                           shade(P["red"], 0.9), bg=paper)
                if t >= t_g2:
                    kg2 = ramp(t, t_g2, t_g2 + 0.8)
                    for i in range(3):
                        if t >= t_g2 + 0.2 * i:
                            cv.put(x + bw - 7, y + 2 + i * 3, "✓",
                                   shade(P["red"], 0.9), bg=paper)
                    sc = int(100 * min(1.0, kg2 * 1.15))
                    if bw >= 50:
                        cv.rtext(y + bh - 2, " score %d/100 " % sc,
                                 shade(P["red"], 0.85), bg=paper,
                                 right=x + bw - 3)
                    if t >= t_st and bw >= 44:
                        ks = ramp(t, t_st, t_st + 0.25)
                        jit = int(round(math.sin(t * 40.0))) \
                            if t < t_st + 0.12 else 0
                        bx = x + bw - 13
                        by = y + bh - 6
                        cv.text(bx + jit, by, "┌─ PASS ──┐",
                                shade(P["red"], 0.8 * ks), bg=paper)
                        cv.text(bx + jit, by + 1, "│ %3d/100 │" % sc,
                                shade(P["red"], 0.95 * ks), bg=paper)
                        cv.text(bx + jit, by + 2, "└─────────┘",
                                shade(P["red"], 0.8 * ks), bg=paper)
            else:
                for i, (sn, txt, ann) in enumerate(steps):
                    at = t_alg - 0.15 + i * 0.5
                    if t < at:
                        continue
                    shown, typing = fx.typewriter(txt, t - at, 34.0)
                    cv.text(x + 3, y + 1 + i, shown,
                            mix(P["gold"], P["white"], 0.2), bg=paper)
                if t >= t_alg + 1.5 and y + 4 < h - 2:
                    yg = y + 4 if y + 4 < y + bh - 1 else h - 3
                    shown, typing = fx.typewriter("✓ ✓ ✓ · score 100 · PASS",
                                                  t - (t_alg + 1.5), 44.0)
                    cv.text(x + 3, yg, shown, shade(P["red"], 0.85),
                            bg=paper)
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
                # the box that holds you: locks on, then steps apart
                k_lock = ramp(t, t_free - 0.06, t_free + 0.12)
                if kv < 0.04 and k_lock > 0.01:
                    anim.brackets(cv, sy0 - 1, ey - 1, sw(yout) + 2, 3,
                                  shade(P["gold"], 0.35 + 0.35 * k_lock),
                                  k=k_lock)
                elif kv < 0.8:
                    sep = int(round(kv * 8))
                    bcol = shade(P["gold"], 0.55)
                    cv.put(sy0 - 1 - sep, ey, "╞", bcol)
                    cv.put(sy0 + sw(yout) + sep, ey, "╡", bcol)
            else:
                s2 = "love := Σ ( ♥ me ♥ )"
                x2 = max(2, cx - sw(s2) // 2)
                cv.text(x2, ey, s2, ink)
                mp = x2 + sw("love := Σ ( ♥ ")
                # the trap: a box whose lid closes cell by cell
                bx0 = x2 + sw("love := Σ ") - 1
                bwid = sw("( ♥ me ♥ )") + 2
                kd_ = ramp(t, t_trap + 0.2, t_trap + 1.0)
                tcol = shade(P["rose"], 0.55)
                cv.put(bx0, ey, "│", tcol)
                cv.put(bx0 + bwid - 1, ey, "│", tcol)
                if kd_ > 0.03:
                    cv.hline(bx0 + 1, ey + 1, bwid - 2, "▁", tcol)
                    nd = int(round(kd_ * (bwid - 2)))
                    for i in range(nd):
                        cv.put(bx0 + 1 + i, ey - 1, "▀",
                               shade(P["rose"],
                                     0.5 + 0.3 if i == nd - 1 else 0.5))
                if kd_ >= 1.0:
                    bb = 0.6 + 0.4 * math.sin(t * 6.8)
                    cv.put(bx0 + bwid // 2, ey - 1, "▀",
                           shade(P["rose"], 0.4 + 0.4 * bb))
                    if ctx.beat < 0.16:
                        cv.put(bx0 - 1, ey + 1, "╱", shade(P["rose"], 0.45))
                        cv.put(bx0 + bwid, ey + 1, "╲", shade(P["rose"], 0.45))
                for i in range(2):
                    cv.put(mp + i, ey - 1, "♥", shade(P["rose"], 0.8))
                    cv.put(mp + i, ey + 1, "◆", shade(P["rose"], 0.6))
            # `you` lifts out of the sum and drifts to the corner
            ex_ = max(6, w - 15)
            ey_ = max(1, ey - 5)
            yx = int(round(sy0 + kh * (ex_ - sy0)))
            yy = int(round(ey - kv * (ey - ey_)))
            for rr in (yy, yy + 1):
                if 0 <= rr < h and rr != ey:
                    cv.fill(0, rr, w, 1, " ", None, None)
            for i in range(1, 4):
                kh2 = kh - i * 0.10
                if kh2 > 0.15:
                    cv.put(int(round(sy0 + kh2 * (ex_ - sy0))),
                           int(round(ey - kv * (ey - ey_))), "·",
                           shade(P["ice"], 0.4 * (1 - kh)))
            cv.put(yx + 2, yy, "◆", mix(P["ice"], P["white"], 0.3 * (1 - kh)))
            if kh > 0.9 and w >= 40:
                cv.text(yx + 1, yy + 1, "free", shade(P["ice"], 0.55))
            # captions, in the order they are sung
            if t >= t_free + 0.15:
                # "free" is typed, taken back, and granted again -- only
                # then is the leaving offered, quietly, as an afterthought
                tf0 = t_free + 0.15
                pre = "you are "
                pre_s = pre[:min(len(pre), int((t - tf0) * 26.0))]
                ts = tf0 + len(pre) / 26.0
                vis, _kf, pht = anim.type_loop(t, ts, "free", cycles=2,
                                               cps=14.0, hold=0.25,
                                               wipe=0.22, gap=0.10)
                tland = ts + 4 / 14.0 + 0.25 + 0.22 + 0.10 + 4 / 14.0
                sfx = " — you may leave any time" if w >= 46 else ""
                s_shown = ""
                styp = False
                if t >= tland and sfx:
                    s_shown, styp = fx.typewriter(sfx, t - tland, 30.0)
                whole = pre_s + vis + s_shown
                cv.fill(0, ey + 2, w, 1, " ", None, None)
                xw = cx - sw(whole) // 2
                cv.text(xw, ey + 2, whole, shade(P["ice"], 0.85))
                cur_on = (pht in ("type", "wipe", "gap")) or \
                    (styp and len(s_shown) < len(sfx))
                if cur_on and int(t * 5) % 2 == 0:
                    cv.put(xw + sw(whole), ey + 2, "▮",
                           shade(P["ice"], 0.6))
            if t >= t_trap + 0.2 and w >= 36 and ey + 4 < h - 2:
                # typed once and kept: the cursor stays on it, listening
                shown, typing = fx.typewriter("I am trapped",
                                              t - (t_trap + 0.2), 16.0)
                cv.fill(0, ey + 4, w, 1, " ", None, None)
                x0t = cx - sw(shown) // 2
                cv.text(x0t, ey + 4, shown, shade(P["pink"], 0.9))
                if not typing and int(t * 2.2) % 2 == 0:
                    cv.put(x0t + sw(shown), ey + 4, "▮",
                           shade(P["pink"], 0.75))
            if t >= t_love:
                kk = ramp(t, t_love, t_love + 0.4)
                yy2 = min(h - 2, ey + 6)
                cv.fill(0, yy2 - 1, w, 3, " ", None, None)
                if h >= 18:
                    for i in range(7):
                        xx = 2 + int(h01(i, 11) * (w - 4))
                        cv.put(xx, yy2 + (i % 2) * 2 - 1, "♥",
                               shade(P["rose"], 0.45 * kk))
                # typed as "trapped in love", then the word stretches
                # itself, hyphen by hyphen, as it cracks on the last note
                age = t - t_love
                s2 = "trapped in love"[:min(15, int(age * 40.0))]
                ns = (1 if t >= t_love + 0.45 else 0) + \
                    (1 if t >= t_love + 0.62 else 0)
                if ns:
                    s2 = s2[:13] + "-o" * ns + s2[13:]
                if s2:
                    xx0 = cx - sw(s2) // 2
                    cv.text(xx0, yy2, s2,
                            mix(P["rose"], P["white"], 0.35 * kk))
                    if ns:      # the fresh hyphens, still hot from the crack
                        for i2 in range(2 * ns):
                            cv.put(xx0 + 13 + i2, yy2, s2[13 + i2],
                                   shade(P["rose"], 0.95))

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
        # the SIGTERM wave: reaps the widget rail, then sweeps the cage
        t_w0 = sc.t0 + 0.40
        kwv = ramp(t, t_w0, t_cage)
        if 0.0 < kwv < 1.0:
            xw = int(round(3 + kwv * (w - 7)))
            for yy in range(top + 1, bot):
                cv.put(xw, yy, "▓" if yy % 2 else "▒",
                       shade(P["white"], 0.30))
            cv.put(xw, top + 1, "▼", shade(P["white"], 0.60))
            if w >= 40:
                cv.text(min(xw + 2, w - 10), bot - 2, "SIGTERM",
                        shade(P["white"], 0.55))
        if ph_ and space >= 16:
            # the rail of little instruments, each one dying as it passes
            y_wl = top + th + 1
            nwid = 5
            bx0_c = max(40, w - 28)
            for i in range(nwid):
                wx = 4 + i * ((w - 12) // nwid)
                if wx + 7 > bx0_c - 2:
                    continue
                nm = ("sig", "bus", "hex", "irq", "tmr")[i]
                frac = (wx + 1.0) / (w - 7)
                t_die = t_w0 + frac * (t_cage - t_w0)
                if kwv >= frac:
                    hot = (t - t_die) < 0.4
                    cv.put(wx, y_wl + 1, "✝",
                           shade(P["red"], 0.85 if hot else 0.45))
                    cv.text(wx + 2, y_wl + 1, nm,
                            shade(P["grey"], 0.40))
                    if hot:
                        cv.hline(wx, y_wl + 2, 3, "▔",
                                 shade(P["red"], 0.5))
                else:
                    cv.text(wx, y_wl + 1, nm, shade(P["cyan"], 0.6))
                    anim.pulse_bars(cv, wx, y_wl + 3, 3, t,
                                    shade(P["cyan"], 0.5), hmax=2,
                                    seed=i + 40, gap=0)
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
        # kernel log: the system narrates its own teardown, up top
        if space >= 12:
            krows = min(5, ybase - top - 1)
            if krows >= 2:
                klog = ((2.95, "kill(0x1A0 chant.exe) → exited"),
                        (3.25, "kill(0x1A7 you.sock) → exited"),
                        (3.55, "kill(0x1F7 me) → ignored"),
                        (3.90, "0x1F7: still running. still here."),
                        (4.25, "execve(love) → ENOENT"),
                        (4.85, "core.dump: 8192 KiB flushed"),
                        (5.45, "sync · sync · umount /heart"),
                        (6.10, "reboot: System halted."))
                vis = [(at, m) for (at, m) in klog
                       if t >= sc.t0 + at][-krows:]
                for j, (at, m) in enumerate(vis):
                    yy = top + 1 + (krows - len(vis)) + j
                    head = "[ %06.2f ] " % at
                    col = 0.30 + 0.55 * j / max(1, len(vis) - 1)
                    shown, typ = fx.typewriter(m, t - (sc.t0 + at), 70.0)
                    cv.text(2, yy, head, shade(P["grey"], 0.30))
                    cv.text(2 + len(head), yy, shown, shade(P["grey"], col))
                    if typ and int(t * 10) % 2 == 0:
                        cv.put(2 + len(head) + sw(shown), yy, "▮",
                               shade(P["grey"], col))
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
        # the exit stamp assembles, pulses, dims before the flash
        t_st = sc.t0 + 12.30
        if t_st <= t < sc.t0 + 13.50 and space >= 12:
            ks = ramp(t, t_st, t_st + 0.35)
            kdim = 1.0 - 0.35 * ramp(t, sc.t0 + 12.95, sc.t0 + 13.50)
            bl = (0.7 + 0.3 * math.sin(t * 6.8)) * kdim
            rows = ("┌─ exit ─────┐",
                    "│ code = 0 ✓ │",
                    "└────────────┘")
            anim.assemble(cv, cx - 7, max(top + 1, cy - 6), rows, ks,
                          shade(P["phos"], bl), seed=9, spread=5)
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
                t_hb = t_off + 1.12
                kd = ramp(t, t_off + 0.84, t_off + 1.06)
                br = 1.0 - 0.55 * kd
                if kd < 0.55:
                    cv.hline(max(1, cx - 6), cy, 13, "─",
                             shade(P["white"], 0.35 * (1 - kd / 0.55)))
                if t < t_hb:
                    cv.put(cx, cy,
                           "█" if kd < 0.45 else ("▪" if kd < 0.8 else "·"),
                           shade(P["white"], br))
                elif t < t_hb + 0.24:
                    # the last heartbeat: two soft pulses, then dark
                    tau = t - t_hb
                    hb = math.exp(-tau * 16.0)
                    if tau >= 0.11:
                        hb = max(hb, 0.85 * math.exp(-(tau - 0.11) * 16.0))
                    cv.put(cx, cy, "♥",
                           shade(P["rose"], 0.30 + 0.60 * min(1.0, hb)))
            else:
                cv.hline(max(1, x0), y0, max(0, kw), "▁",
                         shade(P["white"], 0.55))
        elif kv >= 0.999:
            cv.hline(max(1, y0 and 1), y0, max(0, w - 2), "▁",
                     shade(P["white"], 0.35))

    if not tiny:
        fx.scanlines(cv, 0.88)
        fx.vignette(cv, 0.24)
