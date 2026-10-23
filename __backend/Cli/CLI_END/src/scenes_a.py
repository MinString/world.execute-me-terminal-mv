"""Scenes: intro, verse 1, verse 2, pre-chorus 1, chorus 1."""

import math

import art
import fx
import lyrics
from base import Scene, stamp, fade_window, ramp, cue, glow_text
from renderer import mix, shade, grey, P, h01, sw


# ==========================================================================
# 0 · INTRO — power on, the data fills the screen, boot checks
# ==========================================================================

def _corpus():
    """The bytes that fill the screen are the song's own words."""
    out = bytearray()
    for _t0, _t1, en, _zh in lyrics.LINES:
        out += en.encode("ascii", "ignore") + b". "
    if len(out) < 400:
        out = (bytes(out) * 3)[:900]
    return bytes(out)


DATA = _corpus()

# tag, what is being checked, result, extra note
INIT = [
    ("CPU",  "1 heart @ 130 BPM",                  "ok",   ""),
    ("MEM",  "640K, should be enough for anyone",  "ok",   ""),
    ("PWR",  "switch on the power line",           "ok",   ""),
    ("FS",   "mount /dev/world -> /world/mili",    "ok",   ""),
    ("MOD",  "load module love.ko",                "ok",   ""),
    ("PROT", "apply dielectric insulation",        "ok",   ""),
    ("OBJ",  'allocate object "me"',               "ok",   ""),
    ("REF",  'resolve reference "you"',            "ok",   ""),
    ("DEP",  "dependency you -> me",               "warn", "not symmetric"),
    ("REPO", "object repository",                  "ok",   ""),
    ("CC",   "compile love.dll",                   "ok",   "0 warnings"),
    ("MEM2", "load memories from /world/mili",     "warn", "none found"),
    ("SIM",  "simulation environment",             "ok",   ""),
    ("CLK",  "clock locked to 130.0 BPM",          "ok",   ""),
    ("SYS",  "all systems nominal",                "ok",   ""),
]


def _byte_color(k, y, alpha):
    r = h01(y * 7 + 1, k, 11)
    if r > 0.88:
        return shade(P["white"], 0.85 * alpha)
    if r > 0.55:
        return shade(P["phos"], 0.75 * alpha)
    return shade(P["phos_dim"], 1.05 * alpha)


def dump_nb(width):
    """Bytes per line for a hex dump of the given width."""
    return max(3, (width - 9) // 4)


def _dump_line(cv, y, x0, xmax, off, nb, alpha, head=False):
    """One hex-dump line: address, bytes, ascii column."""
    a = alpha * (0.95 if head else 0.75)
    acol = x0 + 7 + nb * 3
    cv.text(x0, y, "%04X " % ((off // max(1, nb)) & 0xFFFF),
            shade(P["phos_dim"], 0.7 * a))
    for k in range(nb):
        if x0 + 6 + k * 3 >= xmax:
            break
        b = DATA[(off + k) % len(DATA)]
        cv.text(x0 + 6 + k * 3, y, "%02X" % b, _byte_color(k, y, a))
        if acol + k < min(xmax, cv.w):
            ch = chr(b) if 32 <= b < 127 else "·"
            cv.put(acol + k, y, ch, shade(P["phos_dim"], 0.5 * a))


def draw_dump(cv, t, a, head_rows, skip=None):
    """Full-screen memory dump, written top to bottom."""
    w, h = cv.w, cv.h
    nb = dump_nb(w)
    for y in range(1, h):
        if y > head_rows:
            break
        if skip and skip[1] <= y <= skip[3]:
            continue
        part = 1.0
        if y > head_rows - 1:
            part = head_rows - int(head_rows)
            if part <= 0.01:
                continue
        xmax = 2 + int((w - 4) * part)
        if xmax < 12:
            continue
        head = y >= head_rows - 1
        _dump_line(cv, y, 0, xmax, y * nb, nb,
                   a * (0.55 if not head else 1.0), head=head)
        if head and xmax < w - 3:
            cv.put(xmax + 1, y, "▌", shade(P["white"], 0.9 * a))


class IntroScene(Scene):
    key = "intro"
    accent = "phos"

    T_CHECK = 4.25
    T_STEP = 0.50
    T_CMD = 11.80

    # the title arrives the hard way: shattered → garbled → locked on
    T_SIGN = 0.34       # the fragments hit the screen
    T_LOCK0 = 0.94      # they start coming back together
    T_LOCK1 = 2.18      # everything is locked, the card is up
    T_GONE = 3.72       # title card dissolves into the boot checks

    TITLE = "world.execute(me);"
    GARB = "▓▒░█@#%&$?*+=/\\<>{}[]~^;:"
    BLOCKS = "▓▒░█▚▞◣◢  "

    def _warm(self, cv, t):
        """Power-on: the raster opens from a line and blooms."""
        w, h = cv.w, cv.h
        cy = h // 2
        k = ramp(t, 0.02, 0.32)
        half = max(0, int(cy * k))
        phos = P["phos"]
        for y in range(cy - half, cy + half + 1):
            if 0 <= y < h:
                c = mix(P["white"], phos, abs(y - cy) / max(1, cy))
                cv.hline(0, y, w, "█", shade(c, 0.2 + 0.8 * k))
        # flyback streak + the little spark that starts it
        cv.hline(0, cy, w, "─", shade(phos, 0.55 * k))
        if int(t * 24) % 2 == 0:
            cv.put(w // 2, cy, "▌", P["white"])

    def _title_sig(self, cv, t, ty):
        """The title's three bad seconds: it half-appears, tears itself apart,
        then the pieces are pulled back and locked on, glyph by glyph."""
        w, h = cv.w, cv.h
        title = self.TITLE
        n = len(title)
        x0 = (w - n) // 2
        bandw = min(w - 2, n + 10)
        bx = (w - bandw) // 2
        step = int(t * 22)

        # identity confidence: how much of the title is currently itself
        if t < 0.52:
            ident = ramp(t, 0.35, 0.50) * 0.58        # the signal almost finds it
            scat = 0.22 * ramp(t, 0.44, 0.52)
        elif t < 1.05:
            u = ramp(t, 0.52, 1.05)
            ident = 0.58 * (1.0 - u)                  # it shreds
            scat = 0.22 + 0.78 * fx.ease_out(u)
        else:
            v = ramp(t, 1.02, self.T_LOCK1)
            ident = v                                 # it comes back
            scat = (1.0 - fx.ease_out(v)) ** 1.6

        # a strip of dead signal so the fragments read over the hex dump
        for y in (ty - 1, ty, ty + 1, ty + 2):
            if 0 <= y < h:
                cv.paint(bx, y, bandw, 1, None, (4, 9, 7))

        # corrupt blocks, denser the less the signal is itself
        nb = int((1.0 - ident) ** 2.0 * 14)
        for i in range(nb):
            bw = 2 + int(h01(i, step, 101) * 6)
            bh = 1 + int(h01(i, step, 102) * 2)
            bxx = int(h01(i, step, 103) * max(1, w - bw))
            byy = ty - 2 + int(h01(i, step, 104) * 6)
            for yy in range(byy, byy + bh):
                if not (0 < yy < h - 1):
                    continue
                for xx in range(bxx, min(w, bxx + bw)):
                    cv.put(xx, yy, self.BLOCKS[int(h01(xx, yy, step, 105) * len(self.BLOCKS))],
                           mix(P["phos"], P["black"], 0.45), (4, 12, 9))

        # debris shards thrown off the title
        for i in range(n):
            for j in range(3):
                pr = scat * (0.55 + 0.9 * h01(i, j, 21))
                ang = h01(i, j, 23) * 6.28318
                rad = (0.20 + 0.80 * h01(i, j, 25)) * w * 0.44 * pr
                px = x0 + i + math.cos(ang) * rad
                py = ty + math.sin(ang) * rad * 1.5
                px += (h01(i, j, step, 27) - 0.5) * 3.0 * pr
                py += (h01(i, j, step, 29) - 0.5) * 2.0 * pr
                if not (1 <= int(py) < h - 1):
                    continue
                gl = self.GARB[int(h01(i, j, step, 31) * len(self.GARB))]
                a = (0.16 + 0.5 * ident) * (0.45 + 0.55 * h01(i, j, 33))
                cv.put(int(px), int(py), gl,
                       mix(P["black"], mix(P["phos"], P["red"], 0.3), a))

        # the characters themselves
        nlock = 0
        for i, ch in enumerate(title):
            need = 0.14 + 0.76 * h01(i, 11)
            locked = ident >= need
            nlock += locked
            ex = (h01(i, 3) - 0.5) * 2.6
            ey = (h01(i, 5) - 0.5) * 2.4
            jx = (h01(i, step, 7) - 0.5) * 6.0 * scat
            jy = (h01(i, step, 9) - 0.5) * 3.0 * scat
            x = int(round(x0 + i + ex * w * 0.42 * scat + jx))
            y = int(round(ty + ey * h * 0.42 * scat + jy))
            a = 0.55 + 0.45 * min(1.0, ident * 1.3 + 0.15)
            if locked:
                glyph = ch
                c = mix(P["white"], P["phos"], 0.12 * h01(i, 13))
                if ident - need < 0.07:
                    glyph, c = "█", P["white"]       # the flash when it snaps
            else:
                glyph = self.GARB[int(h01(i, step, 15) * len(self.GARB))]
                c = mix(P["phos"], P["red"], 0.3 + 0.5 * h01(i, step, 17))
            if not (0 <= y < h):
                continue
            cv.put(x, y, glyph, mix(P["black"], c, a))
            if scat > 0.12:                          # motion smear behind the glyph
                sx = -1 if jx > 0 else 1
                if 0 <= x + sx < w:
                    cv.put(x + sx, y, glyph, mix(P["black"], c, a * 0.32))
            if scat > 0.15:                          # R/B fringing while it shakes
                if x > 0:
                    cv.put(x - 1, y, "·", mix(P["black"], (255, 62, 84), a * 0.5))
                if x + 1 < w:
                    cv.put(x + 1, y, "·", mix(P["black"], (86, 208, 255), a * 0.5))

        # lock meter — the program's own account of what is happening
        if t >= self.T_LOCK0 - 0.12:
            mw = max(6, min(20, bandw - 16))
            lab = "SYNC" if nlock < n else "LOCK"
            cv.text(bx + 2, ty + 2, lab, mix(P["phos"], P["black"], 0.30))
            cv.put(bx + 6, ty + 2, "▕", mix(P["phos"], P["black"], 0.5))
            fx.bar(cv, bx + 7, ty + 2, mw, nlock / float(n),
                   mix(P["phos"], P["white"], 0.25), None)
            cv.text(bx + 8 + mw, ty + 2, "%02d/%02d" % (nlock, n),
                    mix(P["phos"], P["white"], 0.45))
            if nlock >= n:
                cv.text(bx + 15 + mw, ty + 2, "40ms", mix(P["grey"], P["black"], 0.3))

        # the frame draws itself once the picture is stable
        if ident > 0.965:
            cv.frame(bx, ty - 1, bandw, 3, mix(P["phos"], P["black"], 0.22), style="thin")

        # caption types in under the title
        if t > self.T_LOCK1 - 0.30:
            k = ramp(t, self.T_LOCK1 - 0.30, self.T_LOCK1 + 0.45)
            lines = (
                "—  Mili  ·  Miracle Milk (2016)  —",
                "a terminal music video · 终端 ASCII MV",
                "中英双语字幕 · 与歌同步 · ♥",
                "NTSC 525/60 · 60Hz · PHOSPHOR P1",
            )
            for j, line in enumerate(lines):
                shown, typing = fx.typewriter(
                    line, max(0.0, t - (self.T_LOCK1 - 0.30 + j * 0.20)), 42.0)
                if not shown:
                    continue
                col = (P["white"] if j == 0 else P["soft"] if j == 1
                       else mix(P["phos"], P["black"], 0.35))
                cv.ctext(ty + 3 + j, shown, shade(col, min(1.0, k * 1.3)))
                if typing and int(t * 16) % 2 == 0:
                    cv.put((w - sw(shown)) // 2 + sw(shown), ty + 3 + j, "▌", P["white"])

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        cy = h // 2
        phos = P["phos"]
        panel_on = w >= 78
        list_rows = min(len(INIT), max(2, h - 8 - 4 + 1))
        by = min(4 + list_rows + 1, h - 3)     # bar sits right under the list
        list_rows = max(2, min(list_rows, by - 4))   # never overlap the bar

        # ---------- 1. the tube warms up ----------------------------
        if t < 0.34:
            self._warm(cv, t)
            return

        # ---------- 2. data fills the screen, row by row ------------
        card = fade_window(t, self.T_SIGN, self.T_GONE, 0.03, 0.42)
        ty = max(2, min(h - 9, h // 2 - 3))
        bandw = min(w - 2, len(self.TITLE) + 10)
        bx = (w - bandw) // 2
        hole = None
        if card > 0.02:
            hole = (bx - 1, ty - 2, bx + bandw + 1, ty + 8)

        fill_k = ramp(t, 0.22, 2.75)
        dump_a = 1.0
        if t > 3.30:
            dump_a = max(0.0, 1.0 - (t - 3.30) / 0.55)
        if fill_k > 0 and dump_a > 0.01:
            head_rows = fill_k * (h + 0.9)
            draw_dump(cv, t, dump_a, head_rows, hole)
            # status line under the dump
            if t < 2.9:
                pct = int(min(1.0, fill_k) * 100)
                s1 = "writing memory .... %3d%%" % pct
                cv.text(1, h - 1, s1, shade(P["phos_dim"], 0.9))
                if int(t * 8) % 2 == 0:
                    cv.put(1 + len(s1), h - 1, "▌", P["white"])

        # ---------- 3. the title: shatter → garble → lock ----------
        if card > 0.01:
            if card < 0.995:
                stamp(cv, lambda c2: self._title_sig(c2, t, ty), card)
            else:
                self._title_sig(cv, t, ty)

        # ---------- 5. boot checks, one by one ----------------------
        if t >= self.T_CHECK - 0.55:
            n = len(INIT)
            done = 0
            for i in range(n):
                if t >= self.T_CHECK + i * self.T_STEP:
                    done = i + 1
            cur = done                      # 0..n, index of the item being checked
            right = w - 2
            if panel_on:
                right = w - 38

            # header
            cv.text(3, 1, "DSH/BIOS v1.30", shade(phos, 0.85))
            cv.text(20, 1, "world.execute(me);  ·  terminal music video",
                    shade(P["grey_dim"], 1.0))
            cv.hline(3, 2, right - 3, "─", shade(phos, 0.3))

            rows_avail = list_rows
            top = 0
            if n > rows_avail:
                top = max(0, min(n - rows_avail, done + 1 - rows_avail + 2))
            for i in range(top, min(n, top + rows_avail)):
                tag, what, res, note = INIT[i]
                y = 4 + (i - top)
                t_done = self.T_CHECK + i * self.T_STEP
                age = t - t_done
                if age < -self.T_STEP * 0.92:
                    # not reached yet: a dim placeholder waiting its turn
                    cv.text(3, y, "[      ] ", shade(P["grey_dim"], 0.5))
                    cv.text(3 + 9, y, tag.ljust(5), shade(P["grey_dim"], 0.55))
                    cv.text(3 + 15, y, what[:max(0, right - 19)],
                            shade(P["grey_dim"], 0.45))
                elif age < 0:
                    # being checked right now: a bar fills while the text types
                    k = max(0.0, min(1.0, (t - (t_done - self.T_STEP * 0.92))
                                     / (self.T_STEP * 0.92)))
                    fill = int(k * 6.0)
                    c1 = mix(P["white"], P["phos"], 0.3)
                    shown, typing = fx.typewriter(what, k * self.T_STEP * 1.35, 90.0)
                    cv.put(3, y, "[", c1)
                    for bb in range(6):
                        cv.put(4 + bb, y, "█" if bb < fill else "░",
                               P["white"] if bb < fill else shade(P["phos"], 0.45))
                    cv.put(10, y, "]", c1)
                    cv.text(3 + 9, y, tag.ljust(5), P["white"])
                    cv.text(3 + 15, y, shown[:max(0, right - 19)],
                            shade(P["soft"], 0.9))
                    if typing and int(t * 14) % 2 == 0:
                        cv.put(3 + 15 + sw(shown), y, "▮", P["white"])
                else:
                    flash = max(0.0, 1.0 - age / 0.22)
                    if res == "warn":
                        head, c1, c2 = "[ WARN ] ", P["amber"], P["amber"]
                    else:
                        head, c1, c2 = "[  OK  ] ", P["phos"], P["soft"]
                    if flash > 0.05:
                        c1 = mix(c1, P["white"], flash)
                        c2 = mix(c2, P["white"], flash * 0.8)
                    cv.text(3, y, head, c1)
                    cv.text(3 + 9, y, tag.ljust(5),
                            mix(P["grey"], P["white"], flash))
                    cv.text(3 + 15, y, what[:max(0, right - 19)], c2)
                    if note and 17 + len(what) + 2 + len(note) < right - 3:
                        cv.text(3 + 17 + len(what), y, note,
                                shade(P["grey_dim"], 0.9))

            # progress bar + counters
            k = (done + (0.0 if done >= n else
                         min(1.0, max(0.0, (t - (self.T_CHECK + done * self.T_STEP
                                                - self.T_STEP * 0.92))
                               / self.T_STEP)) * 0.9)) / n
            k = min(1.0, max(0.0, k))
            bw = max(8, min(42, right - 34))
            cv.text(3, by, "progress", shade(P["grey"], 0.9))
            fx.bar(cv, 12, by, bw, k, P["phos"], None, full="█", rest="░")
            cv.text(12 + bw + 1, by, "%3d%%" % int(k * 100), P["white"])
            cv.text(12 + bw + 7, by, "%2d/%d checks" % (done, n),
                    shade(P["phos_dim"], 0.95))
            if done >= n and 12 + bw + 26 <= w:
                cv.text(12 + bw + 20, by, " PASS", P["phos"])

            # ---------- memory panel on the right ------------------
            if panel_on:
                px = w - 35
                phh = min(h - 10, 17)
                py = 3
                fx.panel(cv, px, py, 33, phh, shade(phos, 0.55),
                         title="memory", title_fg=shade(phos, 0.8))
                nb = max(3, (33 - 8) // 3)
                written = int(min(1.0, k) * 0x4000)
                rows_all = written // max(1, nb)
                rows_vis = phh - 4
                first = max(0, rows_all - rows_vis + 1)
                for yy in range(rows_vis):
                    ry = first + yy
                    y = py + 1 + yy
                    if ry > rows_all:
                        break
                    off = ry * nb
                    cv.text(px + 2, y, "%04X" % (off & 0xFFFF),
                            shade(P["phos_dim"], 0.7))
                    for j in range(nb):
                        b = DATA[(off + j) % len(DATA)]
                        xb = px + 7 + j * 3
                        if xb + 1 >= px + 32:
                            break
                        cv.text(xb, y, "%02X" % b, _byte_color(j, y, 0.9))
                cv.text(px + 2, py + phh - 2,
                        "%05X / %05X" % (written, 0x4000),
                        shade(P["grey_dim"], 0.9))

        # ---------- 6. the command --------------------------------
        if t >= self.T_CMD:
            yc = min(by + 2, h - 2)
            shown, typing = fx.typewriter("world.execute(me);",
                                          t - self.T_CMD, 22.0)
            cv.text(3, yc, "$ ", P["phos"])
            cv.text(5, yc, shown, P["white"])
            if typing and int(t * 10) % 2 == 0:
                cv.put(5 + sw(shown), yc, "▮", P["white"])
            if t >= self.T_CMD + 0.75:
                k2 = ramp(t, self.T_CMD + 0.75, self.T_CMD + 1.25)
                cv.text(3, yc + 1, "start" + "." * (1 + int(t * 4) % 3),
                        shade(P["phos"], k2))
                if int(t * 3) % 2 == 0 and k2 > 0.6:
                    cv.put(9 + (int(t * 4) % 3), yc + 1, "▮", P["white"])
            if t >= self.T_CMD + 1.25:
                left = 3 - int((t - self.T_CMD - 1.25) / 0.42)
                if left > 0:
                    cv.text(w // 2 - 10, yc + 1,
                            "simulation starts in", shade(P["grey"], 0.9))
                    for i in range(left):
                        cv.put(w // 2 + 3 + i * 3, yc + 1, "▓",
                               P["white"] if i == 0 else shade(P["phos"], 0.7))

        # ---------- 7. bottom spectrum ------------------------------
        if t > 4.4 and h > 12:
            e = ctx.e_at(t)
            yb = h - 2
            for x in range(0, w, 2):
                v = abs(math.sin(x * 0.055 + t * 1.7)) * (0.35 + 0.9 * e)
                v *= 0.55 + 0.45 * abs(math.sin(x * 0.013 + t * 0.6))
                lvl = min(1, int(v * 2.2))
                for kk in range(lvl + 1):
                    cv.put(x, yb - kk,
                           "▁▃"[min(1, kk + (1 if lvl else 0))],
                           shade(P["phos_dim"], 0.7 - kk * 0.15))

        # ---------- 8. CRT collapses into verse 1 ------------------
        if t > 14.15:
            k = ramp(t, 14.15, 15.0)
            for y in range(h):
                d = abs(y - cy) / max(1, cy)
                if d < k * 1.15:
                    ch = "█" if d < k * 0.9 else "▄"
                    c = mix(P["white"], P["phos"], min(1.0, d * 1.4))
                    cv.hline(0, y, w, ch, shade(c, 0.35 + 0.65 * k))


# ==========================================================================
# 1 · VERSE 1 — object creation
# ==========================================================================

class Verse1Scene(Scene):
    key = "verse1"
    accent = "phos"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        phos = P["phos"]
        t_pow = self.cue("Switch on the power line")
        t_prot = self.cue("Remember to put on protection")
        t_chess = self.cue("Lay down your pieces")
        t_obj = self.cue("And let's begin object creation")
        t_data = self.cue("Fill in my data parameters initialisation")
        t_world = self.cue("Setup our new world")
        t_sim = self.cue("And let's begin the simulation")

        cx = w // 2
        horizon = max(8, int(h * 0.70))
        me2 = art.scale2(art.ME["idle"])
        mh, mw = len(me2), max(sw(l) for l in me2)
        top = horizon - mh          # robot top row
        rx = cx - mw // 2

        # ---- the world: floor + skyline -----------------------------
        gk = 0.35 + 0.55 * ramp(t, t_world - 2.0, t_world + 1.2)
        fx.grid_floor(cv, horizon, shade(P["phos_dk"], gk), rows=4)

        # stars appear when the new world is set up
        wk = ramp(t, t_world, t_world + 2.0)
        if wk > 0:
            for i in range(26):
                sx = int(h01(i, 71) * w)
                sy = 2 + int(h01(i, 72) * max(1, horizon - 4))
                tw = 0.4 + 0.6 * abs(math.sin(t * 1.4 + i))
                if h01(i, 73) < wk:
                    cv.put(sx, sy, "·" if i % 5 else "✦",
                           shade(P["ice"], 0.5 * tw * wk))

        # ---- power line ---------------------------------------------
        a_pow = fade_window(t, t_pow - 0.15, t_world + 0.8, 0.35, 0.8)
        if a_pow > 0.01:
            def power(cv2):
                y = 2
                span = ramp(t, t_pow, t_pow + 1.4)
                x_end = max(2, int((w - 3) * span))
                line_ch = "═" if t < t_prot else "╪"
                line_col = P["amber"] if t < t_prot else P["cyan"]
                cv2.hline(2, y, x_end, line_ch, line_col)
                sx = 2 + int((t * 26) % max(1, x_end))
                cv2.put(sx, y, "◉", P["white"])
                cv2.put(sx, y - 1, "⌁", P["amber"])
                cv2.put(sx, y + 1, "⌁", P["amber"])
                cv2.text(3, 1, "AC 220V · POWER LINE", P["amber"])
                if t >= t_prot:
                    lab = "INSULATED ✓"
                    cv2.text(w - 3 - sw(lab), 1, lab, P["cyan"])
            stamp(cv, power, a_pow)

        # ---- chess pieces on the left -------------------------------
        a_chess = fade_window(t, t_chess, t_sim + 1.2, 0.3, 1.0)
        if a_chess > 0.01:
            def chess(cv2):
                for i, pc in enumerate(art.CHESS):
                    appear = t_chess + i * 0.24
                    if t < appear:
                        continue
                    k = ramp(t, appear, appear + 0.2)
                    x = 5 + i * 3
                    y = horizon - 1 - int((1 - k) * 5)
                    cv2.put(x, y, pc, mix(P["white"], P["soft"], 0.35))
            stamp(cv, chess, a_chess)

        # ---- the object materialises --------------------------------
        if t >= t_obj - 0.15:
            k = ramp(t, t_obj, t_obj + 1.6)
            rows = int(round(mh * k))
            # clear a window so grid/chess do not show through the robot
            cv.fill(rx - 1, top - 1, mw + 2, mh + 2, " ", None, P["black"])
            for j in range(rows):
                cv.text(rx, top + j, me2[j], P["phos"])
            if k < 1:
                fx.sparkle(cv, cx, top + rows, t, P["phos"],
                           seed=int(t * 8), n=8, rad=6)
            lab = 'new Object("me")'
            shown, typing = fx.typewriter(lab, t - t_obj - 0.5, 30.0)
            if shown:
                lx = max(2, rx - sw(lab) - 3)
                cv.text(lx, top + 3, shown, P["phos_dim"])
                if typing and int(t * 12) % 2 == 0:
                    cv.put(lx + sw(shown), top + 3, "▮", P["phos"])

        # ---- data initialisation panel ------------------------------
        a_form = fade_window(t, t_data - 0.2, t_world + 0.6, 0.35, 0.6)
        if a_form > 0.01:
            def form(cv2):
                pw = 27
                px = w - pw - 2
                py = max(4, horizon - 10)
                fx.panel(cv2, px, py, pw, 8, P["phos_dim"], title="initialisation")
                rows = [
                    ('name   : "me"', P["soft"]),
                    ('type   : lover_object', P["soft"]),
                    ('target : "you"', P["pink"]),
                    ('love   : true', P["rose"]),
                    ('         // immutable', P["grey_dim"]),
                ]
                for i, (s, c) in enumerate(rows):
                    at = t_data + 0.15 + i * 0.42
                    if t < at:
                        break
                    shown, typing = fx.typewriter(s, t - at, 50.0)
                    cv2.text(px + 2, py + 1 + i, shown, c)
                    if typing and int(t * 14) % 2 == 0:
                        cv2.put(px + 2 + sw(shown), py + 1 + i, "▮", c)
            stamp(cv, form, a_form)

        # ---- our new world ------------------------------------------
        a_dome = fade_window(t, t_world - 0.3, t_sim + 0.6, 0.7, 0.6)
        if a_dome > 0.01:
            def dome(cv2):
                r = max(6, min(w // 3, horizon - 3))
                # a planet horizon arcing over the robot
                for i in range(46):
                    ang = math.pi + i / 45.0 * math.pi
                    x = cx + int(r * 1.5 * math.cos(ang))
                    y = horizon - 1 + int(r * 0.42 * math.sin(ang) * -1)
                    if 1 <= y < horizon - 1:
                        cv2.put(x, y, "·", shade(P["ice"], 0.55))
                cv2.ctext(horizon - 1 - int(r * 0.42) - 1,
                          "S E T U P   N E W   W O R L D", shade(P["ice"], 0.55))
            stamp(cv, dome, a_dome)

        # ---- simulation start ---------------------------------------
        if t >= t_sim - 0.2:
            k = ramp(t, t_sim - 0.2, t_sim + 0.4)
            lab = "S I M U L A T I O N   S T A R T"
            cv.ctext(horizon - mh - 2, lab, mix(P["white"], P["phos"], 0.5))
            # the "you" reference pops in
            if t >= t_sim + 0.3:
                dy = top + 4 - int(2 * abs(math.sin(t * 2.2)))
                dx = rx + mw + 4
                for j, line_ in enumerate(art.YOU["diamond"]):
                    cv.text(dx - 2, dy - 2 + j, line_, P["pink"])
                cv.text(dx + 3, dy, '"you"', shade(P["pink"], 0.9))
                fx.sparkle(cv, dx, dy, t, P["pink"], seed=int(t * 5), n=5, rad=4)
            fx.sparkle(cv, cx, horizon - mh + 6, t, P["phos"],
                       seed=int(t * 6), n=12, rad=9)

        fx.scanlines(cv, 0.82)


# ==========================================================================
# 2 · VERSE 2 — mathematics
# ==========================================================================

class Verse2Scene(Scene):
    key = "verse2"
    accent = "cyan"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        cyan = P["cyan"]
        t_pts = cue("If I'm a set of points")
        t_dim = cue("Then I will give you my dimension")
        t_circ = cue("If I'm a circle")
        t_cf = cue("Then I will give you my circumference")
        t_sine = cue("If I'm a sine wave")
        t_tan = cue("Then you can sit on all my tangents")
        t_inf = cue("If I approach infinity")
        t_lim = cue("Then you can be my limitations")
        cx, cy = w // 2, max(6, int(h * 0.46))

        # ================= 1 · a set of points ----------------------
        # "If I'm a set of points / Then I will give you my dimension"
        #   A point set on its own is 0-dimensional: no axes, no distance,
        #   nothing to measure.  Dimension appears only when *you* stand at
        #   the origin and draw the axes -- then ONE number is enough to
        #   name a point (a line), TWO numbers (a plane), THREE (the space).
        #   So the same cloud is shown *being given* 0,1,2,3 numbers, and
        #   the instrument on the left shows what each dimension measures:
        #   a point (0), a length (1), an area (2), a volume (3).
        a = fade_window(t, t_pts - 0.30, t_circ - 0.04, 0.45, 0.42)
        if a > 0.01:
            def ac(c, k=1.0):
                return shade(c, a * k)
            big = h >= 16 and w >= 78
            k1 = ramp(t, t_dim - 0.06, t_dim + 0.52)     # 0 -> 1: a line
            k2 = ramp(t, t_dim + 0.56, t_dim + 1.12)     # 1 -> 2: a plane
            k3 = ramp(t, t_dim + 1.16, t_dim + 1.90)     # 2 -> 3: a volume
            dn = 3 if k3 > 0.02 else (2 if k2 > 0.02 else (1 if k1 > 0.02 else 0))
            gx0 = 30 if big else 3
            gx1 = w - 3
            gy0 = 4
            gy1 = (h - 5) if h >= 16 else (h - 4)
            ox = gx0 + 3
            oy = gy1 - 1
            ncol = max(3, min(16, (gx1 - ox - 4) // 4))
            nz = 4 if h >= 14 else 3
            nrow = max(1, min(8, (oy - 2 - (gy0 + nz if h >= 14 else gy0)) // 2 + 1))
            nn = min(120 if h >= 20 else (60 if h >= 14 else 24), ncol * nrow)

            # ---- what the axes will hold: plane grid, then the far face --
            xr0, xr1 = ox + 3, min(gx1, ox + 3 + 4 * (ncol - 1))
            yr0, yr1 = max(gy0, oy - 2 - 2 * (nrow - 1)), oy - 2
            if k2 > 0.04:
                gc = ac(P["cyan"], 0.11 * k2)
                for ri in range(nrow):
                    yy = max(gy0, oy - 2 - 2 * ri)
                    for xx in range(xr0, xr1 + 1):
                        cv.put(xx, yy, "·", gc)
                for ci in range(ncol):
                    xx = ox + 3 + 4 * ci
                    for yy in range(yr0, yr1 + 1):
                        cv.put(xx, yy, "·", gc)
            if k3 > 0.04 and nrow >= 2:
                # the far face of the box, then the frame that makes it read
                gv = ac(P["violet"], 0.22 * k3)
                fx0_, fx1_ = xr0 + 3 * nz, min(gx1, xr1 + 3 * nz)
                fy0_, fy1_ = max(gy0 + 1, yr0 - nz), max(gy0 + 1, yr1 - nz)
                for xx in range(fx0_, fx1_ + 1):
                    cv.put(xx, fy1_, "·", gv)
                    cv.put(xx, fy0_, "·", gv)
                for yy in range(fy0_, fy1_ + 1):
                    cv.put(fx0_, yy, "·", gv)
                    cv.put(fx1_, yy, "·", gv)
                # the front face is the plane: draw its frame a bit brighter
                gf = ac(P["ice"], 0.30 * k3)
                for xx in range(xr0, xr1 + 1):
                    cv.put(xx, yr1, "─", gf)
                    cv.put(xx, yr0, "─", gf)
                for yy in range(yr0, yr1 + 1):
                    cv.put(xr0, yy, "│", gf)
                    cv.put(xr1, yy, "│", gf)
                for (ccx, ccy, ch_) in ((xr0, yr0, "┌"), (xr1, yr0, "┐"),
                                        (xr0, yr1, "└"), (xr1, yr1, "┘")):
                    cv.put(ccx, ccy, ch_, ac(P["ice"], 0.55 * k3))
                # four depth edges
                for (bx_, by_) in ((xr0, yr0), (xr1, yr0), (xr0, yr1), (xr1, yr1)):
                    for u in range(1, nz + 1):
                        cv.put(min(gx1, bx_ + 3 * u), max(gy0 + 1, by_ - u),
                               "╱", ac(P["violet"], 0.42 * k3))

            # ---- the axes: only *you* can draw them ---------------------
            ytop = max(gy0 + 1, oy - 2 * (nrow - 1) - 3)
            if k1 > 0.02:
                ax1 = min(gx1, ox + 4 * (ncol - 1) + 6)
                fx.line(cv, ox, oy, ax1, oy, ac(P["cyan"], 0.55), "─")
                cv.put(ax1, oy, "▶", ac(P["cyan"], 0.9))
                if ax1 + 3 < w - 2:
                    cv.text(ax1 + 2, oy, "x", ac(P["cyan"], 0.95))
                else:
                    cv.text(ax1 - 1, oy - 1, "x", ac(P["cyan"], 0.95))
            if k2 > 0.02:
                fx.line(cv, ox, oy - 1, ox, ytop, ac(P["soft"], 0.55), "│")
                cv.put(ox, ytop, "▲", ac(P["soft"], 0.9))
                cv.text(ox + 1, ytop, "y", ac(P["soft"], 0.95))
            if k3 > 0.02:
                for u in range(1, nz + 3):
                    cv.put(min(gx1, ox + 3 * u), max(gy0 + 1, oy - u),
                           "╱", ac(P["violet"], 0.7 * k3))
                cv.text(min(w - 4, ox + 3 * (nz + 3)), max(gy0 + 1, oy - (nz + 3)),
                        "z", ac(P["violet"], 0.95))
            cv.put(ox, oy, "+", ac(P["white"], 0.95))

            # ---- you arrive at the origin -------------------------------
            if t >= t_dim - 0.42:
                ky = ramp(t, t_dim - 0.42, t_dim + 0.36)
                if ky >= 1.0:
                    cv.put(ox, oy, "◆", ac(P["pink"], 1.0))
                    if oy + 1 <= h - 5:
                        cv.text(ox + 2, oy + 1, "you = origin", ac(P["pink"], 0.85))
                else:
                    yx = int((w - 4) + (ox - (w - 4)) * ky)
                    yy = int(oy - 7 * (1 - ky) * (1 - ky))
                    cv.put(yx, max(gy0, yy), "◆", ac(P["pink"], 0.9))

            # ---- the cloud gets folded onto them, one number at a time --
            pts = []
            for i in range(nn):
                bx = gx0 + 1 + int(h01(i, 11) * (gx1 - gx0 - 2))
                by = gy0 + int(h01(i, 12) * max(1, gy1 - gy0))
                ci = i % ncol
                ri = (i // ncol) % nrow
                nx = ox + 3 + 4 * ci
                ny = max(gy0, oy - 2 - 2 * ri)
                zz = (0 if h01(i, 14) < 0.60
                      else 1 + int(h01(i, 15) * (nz - 1)))
                sx = min(gx1, nx + 3 * zz)
                sy = max(gy0, ny - zz)
                lx = ox + 3 + int((i / max(1.0, nn - 1.0)) * max(1, gx1 - ox - 6))
                qx = lx + (nx - lx) * k2 + (sx - nx) * k3
                qy = oy + (ny - oy) * k2 + (sy - ny) * k3
                x = int(round(bx + (qx - bx) * k1))
                y = int(round(by + (qy - by) * k1))
                pts.append((x, y, i))
            cur = mix(mix(P["ice"], P["cyan"], k1), P["phos"], k3 * 0.55)
            for (x, y, i) in pts:
                if k3 > 0.02 and h01(i, 14) >= 0.60:
                    cv.put(x, y, "∘", ac(P["violet"], 0.55))
                else:
                    cv.put(x, y, "•", ac(cur, 0.9))

            # ---- one point, addressed -----------------------------------
            if dn >= 1 and nrow >= 2:
                hh = 17 % nn
                hx_, hy_, _ = pts[hh]
                cv.put(hx_, hy_, "◉", ac(P["amber"], 1.0))
                if dn == 1:
                    s3 = "( %.2f )" % (h01(hh, 21) * 9)
                elif dn == 2:
                    s3 = "( %.2f , %.2f )" % (h01(hh, 21) * 9, h01(hh, 22) * 9)
                else:
                    s3 = "( %.2f , %.2f , %.2f )" % (h01(hh, 21) * 9,
                                                     h01(hh, 22) * 9, float(hh % nz))
                tx = hx_ + 2
                if tx + len(s3) > gx1:
                    tx = max(gx0, hx_ - len(s3) - 2)
                cv.fill(tx - 1, hy_, len(s3) + 2, 1, " ", None,
                        mix(P["black"], P["amber"], 0.06))
                cv.text(tx, hy_, s3, ac(P["amber"], 0.92))

            # ---- the instrument ----------------------------------------
            if big:
                bgp = mix(P["black"], P["cyan"], 0.06)
                pwl = 27
                phl = 16 if h >= 26 else (13 if h >= 20 else 10)
                px_, py_ = 2, 4
                fx.panel(cv, px_, py_, pwl, phl, ac(P["cyan"], 0.85), bgp,
                         " set P ", ac(P["ice"], 0.95))
                rw = int(t * 4)
                for r_ in range(3):
                    j = (rw + r_ * 7) % 4096
                    cv.text(px_ + 2, py_ + 1 + r_,
                            "p%-4d ( %4.2f , %4.2f )"
                            % (j + 1, h01(j, 21) * 9, h01(j, 22) * 9),
                            ac(P["soft"], 0.8), bgp)
                cv.text(px_ + 2, py_ + 4, "⋮", ac(P["grey"], 0.6), bgp)
                cnt = int(max(0.0, min(1.0, (t - t_pts) / 1.6)) * 4096)
                cv.text(px_ + 2, py_ + 5, "|P| = %4d" % cnt, ac(P["soft"], 0.85), bgp)
                cv.text(px_ + 2, py_ + 6, "dim(P) = %d" % dn,
                        ac(P["phos"], 1.0) if dn else ac(P["grey"], 0.8), bgp)
                cv.text(px_ + 2, py_ + 7,
                        "dim  " + "▮" * (dn + 1) + "▯" * (3 - dn),
                        ac(P["cyan"], 0.9), bgp)
                if phl >= 16:
                    cv.text(px_ + 2, py_ + 9, "what a dim measures",
                            ac(P["grey"], 0.65), bgp)
                    lad = [("•", "point     0 num"),
                           ("─", "length    1 num"),
                           ("▒", "area      2 num"),
                           ("▓", "volume    3 num")]
                    for d_, (gl, txt_) in enumerate(lad):
                        on = (d_ == dn)
                        cv.text(px_ + 1, py_ + 10 + d_, "▸" if on else " ",
                                ac(P["phos"], 1.0), bgp)
                        cv.text(px_ + 3, py_ + 10 + d_,
                                "%d %s  %s" % (d_, gl, txt_),
                                ac(P["phos"], 1.0) if on else ac(P["soft"], 0.42),
                                bgp)
                # the contract, typed under the instrument
                cy_ = py_ + phl + 1
                if cy_ <= h - 5:
                    s1, _ = fx.typewriter("if (me is a set of points)",
                                          t - (t_pts + 0.10), 34.0)
                    cv.text(px_, cy_, s1, ac(P["ice"], 0.85))
                if cy_ + 1 <= h - 5:
                    s2, _ = fx.typewriter("  return my.dimension;",
                                          t - (t_dim - 0.10), 30.0)
                    cv.text(px_, cy_ + 1, s2, ac(P["soft"], 0.8))
                if cy_ + 2 <= h - 5 and t >= t_dim + 2.0:
                    cv.text(px_, cy_ + 2, "  // 0 → 3", ac(P["phos"], 0.8))

            # ---- captions ----------------------------------------------
            cxm = (gx0 + gx1) // 2
            phr = ("a set of points: nothing to measure",
                   "one number names a point",
                   "two numbers name a point",
                   "three numbers name a point")[dn]
            if h >= 10:
                cv.ctext(h - 3, "dim(P) = %d      %s" % (dn, phr),
                         ac(mix(P["cyan"], P["phos"], k3), 0.9), cx=cxm)
            if h >= 11:
                s4 = ("P = { p₁ p₂ p₃ … pₙ }    no axes, no distance",
                      "P ⊂ ℝ¹    x = ( 3.14 )",
                      "P ⊂ ℝ²    ( x , y ) = ( 3.14 , 7.20 )",
                      "P ⊂ ℝ³    ( x , y , z ) = ( 3.14 , 7.20 , 1.00 )")[dn]
                cv.ctext(h - 4, s4, ac(P["soft"], 0.62), cx=cxm)

        # ================= 2 · a circle -----------------------------
        # "If I'm a circle / Then I will give you my circumference"
        #   a circle is only its outline: cut it at the top, unroll it,
        #   and what you get is a straight ruler C = 2πr -- the whole of
        #   me handed over, leaving nothing but the centre behind.
        a = fade_window(t, t_circ + 0.02, t_sine + 0.15, 0.40, 0.5)
        if a > 0.01:
            def ac2(c, k=1.0):
                return shade(c, a * k)
            tiny = h < 12
            if tiny:
                r, ry_ = 3, 1
                ccx = 9
                ccy = max(4, h - 4)
            else:
                r = max(4, min(w // 7, (h - 7) // 2))
                ccy = min(h - 4, max(5, h // 2 - 1))
                ry_ = max(2, min(r // 2, ccy - 5, h - 4 - ccy))
                ccx = max(r + 6, int(w * 0.19))
            # ---- the outline draws itself ---------------------------
            tr = ramp(t, t_circ + 0.10, t_circ + 1.10)
            fx.circle(cv, ccx, ccy, r, ac2(P["ice"], 0.95), "•",
                      a0=-math.pi / 2, a1=2 * math.pi * tr - math.pi / 2,
                      ry=ry_)
            cv.vline(ccx, ccy - ry_, ry_, "┊", ac2(P["cyan"], 0.45))
            cv.put(ccx, ccy - ry_ - 1, "✂", ac2(P["amber"], 0.9))
            if r >= 4:
                cv.text(ccx + 2, ccy - ry_ // 2, "r", ac2(P["ice"], 0.8))
            cv.put(ccx, ccy, "+", ac2(P["cyan"], 0.8))
            # ---- cut and unroll into a ruler ------------------------
            ku = ramp(t, t_cf + 0.10, t_cf + 1.45)
            rx0 = ccx + r + 5
            if w - 4 - rx0 < 18:
                rx0, rrow = 4, min(h - 3, ccy + ry_ + 3)
            else:
                rrow = ccy
            rx1 = w - 4
            Lr = rx1 - rx0
            N = 84
            moved = 0
            for j in range(N + 1):
                th = -math.pi / 2 + 2 * math.pi * j / N
                ex = ccx + int(round(r * math.cos(th)))
                ey = ccy + int(round(ry_ * math.sin(th)))
                tx = rx0 + int(round((Lr - 1) * j / N))
                kk = max(0.0, min(1.0, ku * 1.9 - (j / N) * 0.9))
                if kk <= 0.02:
                    cv.put(ex, ey, "•", ac2(P["ice"], 0.9))
                    continue
                moved += 1
                if kk >= 0.98:
                    cv.put(tx, rrow, "─", ac2(P["cyan"], 0.8))
                else:
                    px_ = int(ex + (tx - ex) * kk)
                    py_ = int(ey + (rrow - ey) * kk)
                    cv.put(px_, py_, "·", ac2(P["ice"], 0.7))
            # ticks + the length of me
            if ku > 0.10:
                reach = rx0 + int((Lr - 1) * min(1.0, ku * 1.05))
                for q in range(5):
                    xq = rx0 + (Lr - 1) * q // 4
                    if xq > reach:
                        break
                    cv.put(xq, rrow, "┼", ac2(P["cyan"], 0.6))
                    if rrow + 1 < h - 2:
                        lab = ("0", "πr/2", "πr", "3πr/2", "2πr")[q]
                        cv.text(xq - sw(lab) // 2, rrow + 1, lab,
                                ac2(P["soft"], 0.6))
            # ---- the answer, typed ---------------------------------
            if rrow - 1 >= 4 and ku > 0.05:
                sh, _ = fx.typewriter("C = 2πr = %.1f" % (2 * math.pi * r),
                                      t - (t_cf + 0.35), 20.0)
                cv.rtext(rrow - 1, sh, ac2(P["cyan"], 0.95), right=rx1)
            # ---- you walk along the circumference ----------------
            km = ramp(t, t_cf + 0.95, t_cf + 1.85)
            if km > 0:
                xm = rx0 + int((Lr - 1) * km)
                cv.put(xm, rrow, "◆", ac2(P["pink"], 0.95))
                if km >= 1.0 and rrow + 2 < h - 3:
                    cv.text(max(2, rx1 - 17), rrow + 2, "given to you: C",
                            ac2(P["pink"], 0.8))
            # ---- the spec sheet: what a circle actually is -----------
            sy = rrow + 3
            if w >= 70 and h >= 15 and sy < h - 4:
                cv.text(rx0, sy, "○  C : a circle of radius r",
                        ac2(P["cyan"], 0.7))
                if sy + 1 < h - 4 and t >= t_cf + 0.5:
                    s1, _ = fx.typewriter(
                        "   centre = ( 0 , 0 )     π = 3.14159…",
                        t - (t_cf + 0.5), 30.0)
                    cv.text(rx0, sy + 1, s1, ac2(P["soft"], 0.75))
                if sy + 2 < h - 4 and t >= t_cf + 1.0:
                    s2, _ = fx.typewriter(
                        "   outline = 2πr = %.1f   → you" % (2 * math.pi * r),
                        t - (t_cf + 1.0), 26.0)
                    cv.text(rx0, sy + 2, s2, ac2(P["pink"], 0.85))
            # ---- what is left of me --------------------------------
            if ku >= 0.99:
                fx.circle(cv, ccx, ccy, r, ac2(P["ice"], 0.16), "∘", ry=ry_)
                mc = ccy + ry_ + 2
                if not (w >= 70 and h >= 15):
                    mc = ccy + ry_ + 2
                else:
                    mc = h - 3
                if mc < h - 2:
                    cv.text(2, mc, "me: just the centre now", ac2(P["grey"], 0.7))

        # ================= sine wave & tangents =====================
        a = fade_window(t, t_sine - 0.3, t_inf + 0.3, 0.4, 0.45)
        if a > 0.01:
            def sine(cv2):
                amp = int(min(h * 0.16, 5))
                freq = 0.12
                phase = -t * 1.5
                cv2.hline(0, cy, w, "─", shade(P["cyan"], 0.18))
                fx.filled_wave(cv2, cy, amp, freq, phase,
                               shade(P["ice"], 1.0), shade(P["cyan"], 0.22))
                if t >= t_tan - 0.2:
                    nb = int((t - t_tan) / 0.4615)
                    for b in range(max(0, nb - 3), nb + 1):
                        tb = t_tan + b * 0.4615
                        if tb > t:
                            continue
                        bx = int((0.12 + h01(b, 31) * 0.7) * w)
                        by = cy + int(round(amp * math.sin(freq * bx + phase)))
                        slope = amp * freq * math.cos(freq * bx + phase)
                        x0, x1 = bx - 7, bx + 7
                        y0 = by - int(round(slope * (x0 - bx)))
                        y1 = by - int(round(slope * (x1 - bx)))
                        age = 1.0 - (t - tb) / 2.4
                        c = shade(P["pink"], max(0.15, 0.85 * age))
                        fx.line(cv2, x0, y0, x1, y1, c)
                        cv2.put(bx, by, "◆", mix(P["pink"], P["white"], 0.3))
                        cv2.put(bx, by - 2, "◆", shade(P["pink"], 0.7))
                cv2.ctext(h - 4, "y = sin x        dy/dx = cos x",
                          shade(P["cyan"], 0.85))
            stamp(cv, sine, a)

        # ================= infinity & limitations ===================
        a = fade_window(t, t_inf + 0.2, t_lim + 2.1, 0.45, 0.8)
        if a > 0.01:
            def inf(cv2):
                r = max(2, min(5, h // 7))
                ry0 = max(2, r)
                inf_cy = 1 + ry0 + 1
                if h >= 20:
                    axis_y = int(h * 0.60) + 1
                    amp0 = max(2, min(7, h - axis_y - 3))
                else:
                    axis_y = h - 3
                    amp0 = 2
                axis_y = max(inf_cy + ry0 + 3, min(axis_y, h - 2))

                # the infinity sign: a lemniscate, plotted like the other
                # curves in this chapter (dots, bright drawing head, labels)
                kk = ramp(t, t_inf, t_inf + 1.1)
                ry = max(2, r)
                rx = max(8, min(int(w * 0.16), ry * 6))
                if kk > 0:
                    steps = 120
                    npts = max(8, int(steps * kk))
                    for i in range(npts + 1):
                        u = i * 2.0 * math.pi / steps
                        d = 1.0 + math.sin(u) ** 2
                        x = cx + int(round(rx * math.cos(u) / d))
                        y = inf_cy + int(round(3.0 * ry * math.sin(u) * math.cos(u) / d))
                        if i == npts:
                            cv2.put(x, y, "●", P["white"])
                        else:
                            cv2.put(x, y, "•",
                                    shade(mix(P["violet"], P["ice"],
                                              i / float(steps)), 0.9))
                    if kk >= 0.999:              # bright marker orbits the curve
                        ang = t * 2.6
                        d = 1.0 + math.sin(ang) ** 2
                        cv2.put(cx + int(round(rx * math.cos(ang) / d)),
                                inf_cy + int(round(3.0 * ry * math.sin(ang)
                                                   * math.cos(ang) / d)),
                                "●", shade(P["white"], 0.95))
                    if kk > 0.55 and w >= 34:
                        cv2.text(max(1, cx - rx - 4), inf_cy, "-∞",
                                 shade(P["violet"], 0.55 * kk))
                        cv2.text(min(w - 4, cx + rx + 2), inf_cy, "+∞",
                                 shade(P["violet"], 0.55 * kk))
                    if kk > 0.7 and w >= 58:
                        cv2.text(min(w - 8, cx + rx + 9), inf_cy, "x → ∞",
                                 shade(P["ice"], 0.7 * kk))

                # ---------- the sequence walks in towards the axis --------
                ak = ramp(t, t_inf + 0.1, t_inf + 0.9)
                if ak <= 0:
                    return
                L = max(6, min(int(w * 0.34), 40))
                fx.line(cv2, cx - L - 2, axis_y, cx + L + 2, axis_y,
                        shade(P["violet"], 0.30 * ak), "─")
                cv2.put(cx - L - 2, axis_y, "├", shade(P["violet"], 0.55 * ak))
                cv2.put(cx + L + 2, axis_y, "▶", shade(P["violet"], 0.7 * ak))
                if w >= 58:
                    ly = axis_y + (2 if amp0 > 2 else 1)
                    cv2.text(cx - L - 2, ly, "n=1", shade(P["grey"], 0.5))
                    cv2.text(cx + L - 3, ly, "n→∞", shade(P["grey"], 0.5))

                # dot column: distance to the axis shrinks to nothing as it is
                # drawn in, so the point set converges on the limit line
                N = 40
                prog = ramp(t, t_inf + 0.25, t_lim + 1.1)
                nvis = max(1, int(prog * N)) if prog > 0 else 0
                for i in range(min(N, nvis)):
                    u = i / float(N - 1)
                    xx = cx - L + int(2 * L * u)
                    d = int(round(0.4 + amp0 * (1.0 - u) ** 1.75))
                    c = mix(P["violet"], P["ice"], 0.25 + 0.65 * u)
                    fresh = (i >= nvis - 1)
                    col = P["white"] if fresh else shade(c, 0.9)
                    ch = "●" if fresh else "•"
                    cv2.put(xx, axis_y - d, ch, col)
                    cv2.put(xx, axis_y + d, ch, col)
                    if d > 2 and i % 5 == 0:      # faint ladder tick
                        cv2.put(xx, axis_y - 1, "┊", shade(c, 0.30))
                        cv2.put(xx, axis_y + 1, "┊", shade(c, 0.30))
                    if w >= 64 and i < 6 and i % 2 == 0:
                        lab = "1/%d" % (i + 1)
                        yy = axis_y - d - 1 if (i // 2) % 2 == 0 else axis_y + d + 1
                        cv2.text(xx, yy, lab, shade(P["grey"], 0.45))

                # the limit it can never touch
                if nvis >= N:
                    cv2.text(cx + L + 3, axis_y - 1, "lim", shade(P["rose"], 0.85))
                if t >= t_lim - 0.2:
                    kb = ramp(t, t_lim - 0.2, t_lim + 0.9)
                    if kb > 0.55 and h >= 14:
                        cv2.ctext(min(h - 1, axis_y + amp0 + 2),
                                  "you = my limitation", P["rose"])
            stamp(cv, inf, a)

        fx.scanlines(cv, 0.86)


# ==========================================================================
# 3 · PRE-CHORUS 1 — AC/DC, time travel, unity
# ==========================================================================

class Pre1Scene(Scene):
    key = "pre1"
    accent = "blue"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_ac = cue("Switch my current")
        t_dc = cue("To AC to DC")
        t_blind = cue("And then blind my vision")
        t_dizzy = cue("So dizzy so dizzy")
        t_travel = cue("Oh we can travel")
        t_bc = cue("To A.D. to B.C.")
        t_unite = cue("And we can unite")
        t_deep = cue("So deeply so deeply")
        cx, cy = w // 2, h // 2 - 1

        # ---------- oscilloscope: AC -> DC ---------------------------
        a = fade_window(t, t_ac - 0.2, t_blind + 0.9, 0.4, 0.6)
        if a > 0.01:
            def osc(cv2):
                px, py = max(1, int(w * 0.08)), max(2, int(h * 0.10))
                pw, phh = w - 2 * px, int(h * 0.62)
                fx.panel(cv2, px, py, pw, phh, shade(P["blue"], 0.9),
                         title="OSC-1  CH1  5ms/div")
                # graticule
                for gx in range(px + 4, px + pw - 2, 6):
                    for gy in range(py + 2, py + phh - 2, 2):
                        cv2.put(gx, gy, "·", shade(P["blue"], 0.18))
                # waveform
                midy = py + phh // 2
                morph = ramp(t, t_dc - 0.3, t_dc + 1.7)   # 0 AC -> 1 DC
                amp = (phh // 2 - 2) * (1.0 - morph * 0.92)
                ph = -t * 7.0
                for x in range(px + 1, px + pw - 1):
                    v = math.sin((x - px) * 0.22 + ph)
                    y = midy - int(round(amp * v))
                    c = mix(P["cyan"], P["amber"], morph)
                    cv2.put(x, y, "•", c)
                    if amp > 1:
                        cv2.put(x, y - 1, "·", shade(c, 0.4))
                # labels
                lab = "AC ~" if morph < 0.5 else "DC ─"
                cv2.text(px + 2, py + phh + 1, lab, mix(P["cyan"], P["amber"], morph))
                if morph > 0.5:
                    cv2.text(px + 9, py + phh + 1, "rectified", shade(P["amber"], 0.7))
                cv2.rtext(py + phh + 1, "Vpp %.1fV" % (2 * abs(amp) / 3.0 + 0.1),
                          shade(P["soft"], 0.8), right=px + pw - 1)
            stamp(cv, osc, a)

        # ---------- blind vision / dizzy spiral ---------------------
        a = fade_window(t, t_blind - 0.3, t_unite + 0.2, 0.4, 0.5)
        if a > 0.01:
            def dizzy(cv2):
                # closing eyelid
                k = ramp(t, t_blind, t_blind + 1.0)
                if k < 1.0:
                    ex = art.ART["eye"]
                    ew = max(sw(l) for l in ex)
                    x = cx - ew // 2
                    y = cy - len(ex) // 2
                    for j, line_ in enumerate(ex):
                        lim = j / len(ex)
                        if lim < k:
                            continue
                        cv2.text(x, y + j, line_, shade(P["ice"], 0.9))
                    # lid
                    lid = int(k * len(ex))
                    for j in range(lid):
                        cv2.text(x, y + j, ex[j].replace("█", "▄"), shade(P["blue"], 0.6))
                # spiral
                sk = ramp(t, t_dizzy - 0.1, t_dizzy + 0.5)
                if sk > 0:
                    spin = t * (2.2 + 3.0 * ramp(t, t_dizzy, t_bc))
                    for i in range(46):
                        ang = spin + i * 0.42
                        rr = 1.4 * i ** 0.82
                        x = cx + int(math.cos(ang) * rr * 1.7)
                        y = cy + int(math.sin(ang) * rr / 1.5)
                        c = shade(mix(P["violet"], P["ice"], (i % 7) / 7.0), 0.35)
                        cv2.put(x, y, "·×*"[i % 3], c)
                    if t > t_dizzy + 0.6:
                        cv2.ctext(cy + 2, "so dizzy . . .", shade(P["violet"], 0.75))
            stamp(cv, dizzy, a)

        # ---------- time travel: every age runs backwards -----------
        a = fade_window(t, t_travel - 0.25, t_unite + 0.10, 0.4, 0.30)
        if a > 0.01:
            def clock(cv2):
                k = ramp(t, t_travel, t_bc + 1.2)      # 0 -> 1 as time rewinds
                dcy = cy - (2 if h >= 22 else 0)
                r = max(5, min(w // 9, h - 10 if h >= 20 else h - 7))
                pairs = [
                    (["  ▄█▄   ", "  █▓█   ", " ▄█▓█▄  "],
                     ["   ╱╲   ", "  ╱▀▀╲  ", " ╱▀▀▀▀╲ "],
                     "tower", "tomb"),
                    ([" ▀▀▀▀▀  ", "▐█▣█▌   ", " ▄▄▄▄▄  "],
                     [" ┌┬┬┐   ", " ├┼┼┤   ", " └┴┴┘   "],
                     "chip", "abacus"),
                    (["  ▄▄▄▄  ", " ██▀▀██ ", " ○    ○ "],
                     [" ▄▄▄▄▄▄ ", " █▀▀▀▀█ ", " ○    ○ "],
                     "car", "cart"),
                    (["  ,▄▄,  ", " ▐▓▓▓▌  ", "  ▀▀▀   "],
                     ["  ,▲,   ", "  ▐█▌   ", " ▀▀▀▀▀  "],
                     "bulb", "lamp"),
                    (["   ▄▄   ", "  ▐██▌  ", "   ▼▼   "],
                     ["  ▄ ▄   ", " ██ ██  ", " ▀▀▀▀▀  "],
                     "dish", "stone"),
                ]
                n = len(pairs)
                newc = mix(P["ice"], P["cyan"], 0.35)
                oldc = mix(P["amber"], P["gold"], 0.35)

                # ---- every age streams past, through the background ----
                #   nothing sits still: the century itself is flying by, and
                #   each thing sheds its present form for the one before it.
                if h >= 16:
                    lanes = [y for y in range(4, h - 4, 3)] or [4]
                    span = w + 16
                    nobj = 8 if w < 100 else 12
                    for oi in range(nobj):
                        ma, oa, lm, lo = pairs[oi % n]
                        li = (oi * 3 + 1) % len(lanes)
                        ly = lanes[li]
                        spd = 3.0 + 1.35 * oi + 0.35 * li
                        xx = int((h01(oi, 61) * span
                                  + spd * t * (1.0 + 1.1 * k)) % span) - 8
                        ki = max(0.0, min(1.0,
                                          (k * 1.30 - 0.30 * h01(oi, 62)) / 0.62))
                        edge = min(1.0, min(xx + 8, span - 8 - xx) / 7.0)
                        depth = 0.35 + 0.65 * (li + 1) / len(lanes)
                        al = 0.40 * depth * max(0.0, edge)
                        if al <= 0.02:
                            continue
                        for j, ln in enumerate(ma):
                            for ii, ch in enumerate(ln):
                                if ch == " ":
                                    continue
                                o_ch = (oa[j][ii]
                                        if j < len(oa) and ii < len(oa[j])
                                        else " ")
                                v = h01(oi, ii, j)
                                if o_ch != " " and v < ki:
                                    cv2.put(xx + ii, ly + j, o_ch,
                                            shade(oldc, al))
                                elif abs(v - ki) < 0.10 and h01(ii, j, oi) < 0.6:
                                    cv2.put(xx + ii, ly + j,
                                            "▒" if h01(ii, j) < 0.5 else "░",
                                            shade(P["white"], al * 0.9))
                                else:
                                    cv2.put(xx + ii, ly + j, ch,
                                            shade(newc, al))
                        for u in range(1, 3):
                            if h01(oi, u) < 0.55:
                                cv2.put(xx - u * 2, ly + 1 + (u % 2 - 1) // 2,
                                        "·", shade(P["soft"], al * (0.6 - 0.2 * u)))

                # ---- the dial is opaque: ages vanish behind the clock ---
                for yy in range(dcy - r // 2 - 1, dcy + r // 2 + 2):
                    if yy < 2 or yy >= h - 2:
                        continue
                    dyy = (yy - dcy) * 2.0
                    if abs(dyy) >= r:
                        continue
                    hw = int(math.sqrt(max(0.0, r * r - dyy * dyy)))
                    cv2.fill(cx - hw, yy, 2 * hw + 1, 1, " ")

                # dial: a dim bezel of shaded cells, then the face
                for yy in range(dcy - r // 2 - 1, dcy + r // 2 + 2):
                    if yy < 2 or yy >= h - 1:
                        continue
                    dyv = (yy - dcy) * 2.0
                    if abs(dyv) > r:
                        continue
                    hw = int(math.sqrt(max(0.0, r * r - dyv * dyv)))
                    rimc = shade(P["violet"], 0.30)
                    if abs(dyv) > r * 0.72:
                        for xx in range(max(1, cx - hw), min(w - 1, cx + hw + 1)):
                            cv2.put(xx, yy, "░", rimc)
                    else:
                        cv2.put(cx - hw, yy, "░", rimc)
                        cv2.put(cx + hw, yy, "░", rimc)
                fx.circle(cv2, cx, dcy, r, shade(P["violet"], 0.9), "·",
                          ry=r / 2, a0=0.0, a1=2 * math.pi)
                fx.circle(cv2, cx, dcy, r * 0.80, shade(P["violet"], 0.55),
                          "·", ry=r * 0.40)
                for i in range(12):
                    ang = i * math.pi / 6 - math.pi / 2
                    x = cx + int((r + 1) * math.cos(ang))
                    y = dcy + int((r / 2 + 1) * math.sin(ang))
                    cv2.put(x, y, "·" if i % 3 else "✦", shade(P["violet"], 0.7))
                # hands spin backwards, faster as the era gives way
                spin = -t * (3.0 + 9.0 * k)
                for m, ln in ((0, 0.55), (1, 0.8)):
                    ang = spin * (1 if m == 0 else 2.4)
                    x = cx + int(r * ln * math.cos(ang))
                    y = dcy + int(r / 2 * ln * math.sin(ang))
                    fx.line(cv2, cx, dcy, x, y,
                            P["rose"] if m == 0 else P["amber"])
                cv2.put(cx, dcy, "◉", shade(P["white"], 0.8))
                # hour numerals, so the face reads as a face
                for hh, hx, hy in ((12, 0, -0.30), (3, 0.34, 0.0),
                                   (6, 0.0, 0.26), (9, -0.34, 0.0)):
                    nx = cx + int(r * hx)
                    ny = dcy + int(r * hy)
                    cv2.text(nx - 1, ny, "%2d" % hh, shade(P["violet"], 0.75))
                cv2.put(cx, dcy - r // 2 + 1, "✦", shade(P["amber"], 0.85))


                # the year rolls backwards through zero
                year = int(2016 - k * 4016)
                ys = ("%d A.D." % max(1, year)) if year >= 0 else ("%d B.C." % -year)
                era = "A.D." if year >= 0 else "B.C."
                if h >= 18:
                    cv2.ctext(dcy + 2, era, mix(P["amber"], P["cyan"], k))

                if h < 18:
                    return
                # ---- timeline: A.D. ─────────▶ ◀───────── B.C. -----------
                ty = dcy + r // 2 + 4
                if ty + 5 > h:
                    ty = h - 6
                half = min(int(w * 0.40), 46)
                x0, x1 = cx - half, cx + half
                cv2.text(max(1, x0 - 5), ty, "A.D.", shade(P["amber"], 0.85))
                cv2.text(min(w - 5, x1 + 2), ty, "B.C.", shade(P["cyan"], 0.85))
                fx.line(cv2, x0, ty, x1, ty, shade(P["soft"], 0.35), "─")
                for i in range(9):
                    cv2.put(x0 + int((x1 - x0) * i / 8.0), ty, "┼",
                            shade(P["soft"], 0.45))
                cxp = x1 - int((x1 - x0) * k)             # cursor runs left
                cv2.put(cxp, ty, "▼", P["rose"])
                if w >= 66:
                    cv2.rtext(ty - 1, ys, shade(P["rose"], 0.95), right=x1)
                    cv2.text(x0 + 1, ty - 1, "◀◀ rewind",
                             shade(P["violet"], 0.7))
                elif w >= 40:
                    cv2.ctext(ty - 1, ys, shade(P["rose"], 0.9))
                # ---- the names of the five ages, running backwards -------
                if w >= 74 and h >= 16:
                    leg = "   ".join("%s→%s" % (p[2], p[3]) for p in pairs)
                    cv2.ctext(h - 3, leg, shade(P["soft"], 0.5))
            stamp(cv, clock, a)

        # ---------- unite -------------------------------------------
        a = fade_window(t, t_unite + 0.06, self.t1 + 0.1, 0.30, 0.35)
        if a > 0.01:
            def unite(cv2):
                k = ramp(t, t_unite + 0.2, t_deep + 0.9)
                amp = int(min(h * 0.12, 4))
                for x in range(w):
                    off = int((1 - k) * (w * 0.5 - abs(x - cx)) * 0.12)
                    y1 = cy - off + int(amp * math.sin(x * 0.16 + t * 2.2))
                    y2 = cy + off + int(amp * math.sin(x * 0.16 + t * 2.2 + math.pi))
                    cv2.put(x, y1, "·", shade(P["cyan"], 0.9))
                    cv2.put(x, y2, "·", shade(P["pink"], 0.9))
                if k > 0.75:
                    c = mix(P["cyan"], P["pink"], 0.5)
                    for x in range(w):
                        y = cy + int(amp * math.sin(x * 0.16 + t * 2.2))
                        cv2.put(x, y, "─", mix(c, P["white"], ramp(k, 0.75, 1.0)))
                # two diamonds approach
                kk = ramp(t, t_unite + 0.4, t_deep + 0.8)
                gap = int((1 - kk) * w * 0.22) + 2
                for sgn, c in ((-1, P["phos"]), (1, P["pink"])):
                    x = cx + sgn * gap
                    cv2.put(x, cy - 5, "◆", c)
                if kk > 0.92:
                    fx.sparkle(cv2, cx, cy - 5, t, P["white"], seed=int(t * 7), n=12, rad=7)
                    cv2.ctext(cy - 7, "so deeply", P["pink"])
            stamp(cv, unite, a)

        fx.scanlines(cv, 0.8)


# ==========================================================================
# 4 · CHORUS 1 — stimulation / satisfaction / execution
# ==========================================================================

class Chorus1Scene(Scene):
    key = "chorus1"
    accent = "pink"

    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        t_stim = cue("If I can")
        t_sat = cue("Then I can")
        t_happy = cue("If I can make you happy")
        t_exec = cue("I will run the execution")
        t_trap = cue("Though we are trapped")
        t_ssim = cue("In this strange strange simulation")
        cx = int(w * 0.5)

        beatp = max(0.0, 1.0 - ctx.beat) ** 2.2     # 1 on beat
        loud = ctx.e_at(t)

        # ---------- background: rings + rain ------------------------
        fx.matrix_rain(cv, t * 0.7, shade(P["rose"], 0.16), density=0.16,
                       seed=5, tail=3)
        for i in range(3):
            age = (t * 0.55 + i / 3.0) % 1.0
            r = int(age * min(w, h) * 0.75)
            if r < 2:
                continue
            c = shade(P["rose"], 0.45 * (1 - age))
            fx.circle(cv, cx, h // 2, r, c, "·", ry=r / 2, steps=max(20, r * 3))

        # ---------- the heart is simulated on a full-frame monitor ---
        if t >= t_stim - 0.3 and t < t_trap + 1.0:
            def ecg_full(cv2):
                scr = ramp(t, t_stim - 0.3, t_stim + 0.55)
                mid = h // 2
                amp = max(3, int(h * 0.33))
                # monitor paper: fine grid + heavier time lines
                for gx in range(2, w - 2, 6):
                    for gy in range(2, h - 3, 3):
                        cv2.put(gx, gy, "·", shade(P["pink"], 0.09 * scr))
                for gx in range(2, w - 2, 18):
                    cv2.vline(gx, 2, h - 6, ":", shade(P["pink"], 0.15 * scr))
                cv2.hline(2, mid, w - 4, "·", shade(P["pink"], 0.22))
                # the sweep head runs left -> right, over and over
                per = 2.6
                ph = ((t - t_stim) % per) / per
                span = max(12, w - 6)
                head = 3 + int(ph * span)
                phase = (t - t_stim) * 1.15
                for xx in range(3, w - 3):
                    u = (xx - 3) / 22.0 + phase
                    v = fx.ecg(u)
                    yy = mid - int(round(amp * v))
                    ahead = xx > head
                    col = shade(mix(P["pink"], P["white"], 0.15 if ahead else 0.5),
                                0.32 if ahead else 0.95)
                    cv2.put(xx, yy, "·" if ahead else "•", col)
                    if abs(v) > 0.45:          # stems make it fill the frame
                        for y2 in range(min(mid, yy) + 1, max(mid, yy)):
                            cv2.put(xx, y2, "│",
                                    shade(P["pink"], 0.12 if ahead else 0.30))
                for yy in range(max(1, mid - amp - 2), min(h - 1, mid + amp + 3)):
                    if h01(head, yy, int(t * 8)) < 0.72:
                        cv2.put(head, yy, "▌", shade(P["white"], 0.28))
                # second channel: the pulse wave
                for xx in range(3, w - 3):
                    u = (xx - 3) / 40.0 - phase * 0.7
                    v = math.sin(u * 6.283) * 0.55 + math.sin(u * 12.566) * 0.22
                    cv2.put(xx, int(h * 0.79) - int(amp * 0.5 * v), "·",
                            shade(P["ice"], 0.28))
                hr = 68 + int(14 * math.sin(t * 1.3))
                ry = max(2, mid - amp - 2)
                if w >= 62:
                    cv2.text(3, ry, "HR %03d BPM · SINUS" % hr, shade(P["pink"], 0.9))
                    cv2.rtext(ry, "SpO₂ 98% · SIM 1/1", shade(P["ice"], 0.8),
                              right=w - 4)
                elif w >= 36:
                    cv2.text(3, ry, "HR %03d" % hr, shade(P["pink"], 0.9))
                    cv2.rtext(ry, "SpO₂ 98%", shade(P["ice"], 0.8), right=w - 4)
            stamp(cv, ecg_full, fade_window(t, t_stim - 0.3, t_trap + 1.0, 0.5, 0.5))

        # ---------- heart --------------------------------------------
        grow = ramp(t, t_stim, t_stim + 2.0) * 0.4 + 0.6
        grow = min(1.35, grow + 0.5 * ramp(t, t_sat, t_sat + 1.5))
        heart = art.ART["heart_big"]
        hy = h // 2 - len(heart) // 2 - 1
        dx = int(w * 0.30) if t >= t_exec - 0.2 else cx
        k = ramp(t, t_exec - 0.25, t_exec + 0.35) if t >= t_exec - 0.25 else 0.0
        hx = int(cx + (w * 0.30 - cx) * k)
        if t >= t_trap - 0.25:                 # dragged into the box
            kk2 = ramp(t, t_trap - 0.25, t_ssim + 0.8)
            hx = int(round(hx + (cx - hx) * kk2))
        color = mix(P["rose"], P["pink"], 0.5 + 0.5 * math.sin(t * 0.8))
        color = shade(color, 0.72 + 0.45 * beatp + 0.25 * (loud - 0.4))

        hw = max(sw(l) for l in heart)
        for j, line_ in enumerate(heart):
            for i, ch in enumerate(line_):
                if ch == " ":
                    continue
                cv.put(hx - hw // 2 + i, hy + j - int(beatp * 1), ch, color)

        # halo
        if t > t_sat - 0.2:
            for i in range(10):
                ang = t * 0.8 + i * 0.63
                r = hw * 0.62
                x = hx + int(math.cos(ang) * r * 1.1)
                y = hy + 4 + int(math.sin(ang) * r / 2.2)
                cv.put(x, y, "♥", shade(P["pink"], 0.5))

        # ---------- equalizer ---------------------------------------
        if t < t_sat - 0.1:
            n = 18
            bw = max(1, w // (n + 6))
            for i in range(n):
                e = ctx.e_at(t - 0.05 + h01(i, 61) * 0.06)
                hgt = int((0.4 + 2.8 * e) * (0.5 + 0.5 * h01(i, 62)))
                x = 4 + i * (bw + 1) * 2
                if x >= w - 2:
                    break
                for j in range(hgt):
                    y = h - 3 - j
                    c = shade(mix(P["rose"], P["amber"], j / max(1, hgt)), 0.75)
                    cv.put(x, y, "▐", c)

        # ---------- satisfaction bar --------------------------------
        if t >= t_sat - 0.1:
            def sat(cv2):
                bw = min(34, w - 12)
                x = cx - bw // 2
                y = h - 5
                kk = ramp(t, t_sat - 0.1, t_sat + 2.4)
                cv2.ctext(y - 2, "SATISFACTION", P["pink"])
                fx.bar(cv2, x, y, bw, kk, P["rose"], None)
                cv2.ctext(y + 1, "%3d%%" % int(kk * 100), P["white"])
                if kk >= 0.999:
                    cv2.ctext(y - 4, "only yours ♥", P["rose"])
            stamp(cv, sat, fade_window(t, t_sat - 0.1, t_exec + 1.4, 0.4, 0.6))

        # ---------- make you happy ----------------------------------
        if t >= t_happy - 0.15:
            def happy(cv2):
                kk = ramp(t, t_happy - 0.15, t_happy + 0.9)
                hcx, hcy = hx, hy + len(heart) // 2
                # balloons drifting up
                for i in range(3):
                    ph = ((t - t_happy) * 0.30 + i * 0.33) % 1.0
                    bx = hcx + (i - 1) * (hw // 2 + 7) + int(math.sin(t * 1.3 + i) * 2)
                    by = hcy - 3 - int(ph * (hcy + 1))
                    if by < 2 or bx < 2 or bx > w - 3:
                        continue
                    c = (P["rose"], P["gold"], P["pink"])[i]
                    cv2.put(bx, by - 1, "▄", shade(c, 0.9))
                    cv2.put(bx - 1, by, "(", shade(c, 0.9))
                    cv2.put(bx + 1, by, ")", shade(c, 0.9))
                    cv2.put(bx, by + 1, "▀", shade(c, 0.9))
                    cv2.vline(bx, by + 2, max(0, min(3, h - by - 3)), "|",
                              shade(P["soft"], 0.35))
                # confetti
                for i in range(28):
                    ph = ((t - t_happy) * (0.45 + 0.5 * h01(i, 101)) + h01(i, 102)) % 1.0
                    px = hcx + int(math.sin(ph * 5.5 + i) * (hw * 0.95))
                    py = hcy + 4 - int(ph * (hcy + 3))
                    if py < 1 or px < 1 or px > w - 2:
                        continue
                    ch = "✦" if h01(i, int(t * 5)) < 0.3 else ("*" if i % 3 else "+")
                    cv2.put(px, py, ch,
                            shade(mix(P["gold"], P["pink"], h01(i, 103)), 0.9))
                # bouncing kaomoji
                for i, sgn in enumerate((-1, 1)):
                    fx0 = hcx + sgn * (hw // 4 + 2)
                    fy0 = hcy + 5 - int(abs(math.sin(t * 3.2 + i * 1.7)) * 2)
                    face = "^_^" if int(t * 4 + i) % 2 == 0 else "^-^"
                    if 1 < fx0 < w - 3 and fy0 < h - 6:
                        cv2.text(fx0 - 1, fy0, face, shade(P["gold"], 0.95))
                if kk > 0.55:
                    cv2.ctext(max(1, hy - 3), "H A P P Y",
                              shade(mix(P["pink"], P["white"],
                                        0.15 + 0.55 * beatp), 0.95))
            stamp(cv, happy, fade_window(t, t_happy - 0.15, t_trap + 0.6, 0.4, 0.5))

        # ---------- terminal: run the execution ---------------------
        if t >= t_exec - 0.2:
            def term(cv2):
                px = int(w * 0.55)
                pw = min(34, w - px - 2)
                py = max(2, h // 2 - 6)
                phh = 9
                fx.panel(cv2, px, py, pw, phh, P["phos_dim"], title="bash")
                rows = [
                    ("$ world.execute(me);", P["white"]),
                    ("running ...", shade(P["soft"], 0.9)),
                ]
                for i, (s, c) in enumerate(rows):
                    at = t_exec + i * 0.45
                    if t < at:
                        continue
                    shown, _ = fx.typewriter(s, t - at, 40.0)
                    cv2.text(px + 2, py + 1 + i, shown, c)
                kk = ramp(t, t_exec + 0.6, t_exec + 2.2)
                fx.bar(cv2, px + 2, py + 3, pw - 4, kk, P["phos"], None,
                       full="▓", rest="░")
                spin = "-\\|/"[int(t * 10) % 4]
                cv2.text(px + 2, py + 4, "%s %3d%%" % (spin, int(kk * 100)),
                         P["phos"])
                if kk >= 1.0:
                    cv2.text(px + 2, py + 5, "execution complete ✓", P["phos"])
                    if int(t * 3) % 2 == 0:
                        cv2.text(px + 2, py + 6, "status: executed", P["grey"])
            stamp(cv, term, fade_window(t, t_exec - 0.2, t_trap + 0.25, 0.3, 0.45))

        # ---------- trapped in the simulation -----------------------
        if t >= t_trap - 0.2:
            def trap(cv2):
                kk = ramp(t, t_trap - 0.2, t_ssim + 0.9)
                bw = int((w - 6) - (w - 6 - min(26, w - 6)) * kk)
                bh = int((h - 4) - (h - 4 - min(13, h - 4)) * kk)
                x = cx - bw // 2
                y = h // 2 - bh // 2
                fx.bracket(cv2, x, y, bw, bh, mix(P["pink"], P["white"], 0.3),
                           style="<>")
                if kk > 0.85:
                    cv2.ctext(max(1, y - 2), "STRANGE SIMULATION", P["pink"])
                    cv2.put(x, y + bh // 2, "╬", P["white"])
                    cv2.put(x + bw - 1, y + bh // 2, "╬", P["white"])
                    cv2.ctext(min(h - 1, y + bh), "isolation box · you", shade(P["pink"], 0.85))
                # scan wipe
                sy = int((t * 22) % h)
                cv2.hline(0, sy, w, "─", shade(P["pink"], 0.25))
            stamp(cv, trap, fade_window(t, t_trap - 0.2, self.t1 + 0.2, 0.3, 0.2))

        fx.scanlines(cv, 0.85)
        fx.vignette(cv, 0.28)
