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

        # ================= points & dimension ========================
        a = fade_window(t, t_pts - 0.2, t_dim + 2.3, 0.5, 0.7)
        if a > 0.01:
            def pts(cv2):
                rot = t * 0.55
                k = ramp(t, t_dim - 0.2, t_dim + 1.4)
                sc = min((w - 24) // 7, (h - 16) // 3)
                sc = max(3, sc)
                verts = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                         (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
                edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6),
                         (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
                proj = []
                for (x, y, z) in verts:
                    x1 = x * math.cos(rot) - z * math.sin(rot)
                    z1 = x * math.sin(rot) + z * math.cos(rot)
                    y1 = y * math.cos(rot * 0.7) - z1 * math.sin(rot * 0.7)
                    z2 = y * math.sin(rot * 0.7) + z1 * math.cos(rot * 0.7)
                    proj.append((cx + int(x1 * sc * 1.7),
                                 cy - int(y1 * sc * 0.85) - int(z2 * sc * 0.3)))
                for (i0, i1) in edges:
                    fx.line(cv2, *proj[i0], *proj[i1], shade(P["cyan"], 0.5))
                for i, (px, py) in enumerate(proj):
                    cv2.put(px, py, "•", P["ice"])
                # a cloud of points that snaps into the cube
                for i in range(30):
                    ang = h01(i, 81) * 6.283
                    rad = 2 + h01(i, 82) * sc * 2.4
                    qx = cx + int(math.cos(ang + t * 0.3) * rad * 1.6)
                    qy = cy + int(math.sin(ang * 1.3 + t * 0.4) * rad * 0.7)
                    if h01(i, 83) < 0.35 + 0.65 * (1 - k):
                        cv2.put(qx, qy, "·", shade(P["ice"], 0.45))
                # axes (drawn once the dimension is offered)
                if k > 0:
                    L = int(min(w * 0.3, 20) * min(1.0, k))
                    fx.line(cv2, cx - L, cy, cx + L, cy, shade(P["cyan"], 0.4), "─")
                    fx.line(cv2, cx, cy + L // 2, cx, cy - L, shade(P["cyan"], 0.4))
                    cv2.text(cx + L + 2, cy, "X", shade(P["ice"], 0.7))
                    cv2.text(cx, cy - L - 1, "Y", shade(P["ice"], 0.7))
                cv2.ctext(h - 4, "dim(P) = 3", shade(P["cyan"], 0.9))
                if t >= t_dim:
                    dk = ramp(t, t_dim, t_dim + 0.9)
                    px, py = proj[6]
                    art_you = art.YOU["diamond"]
                    for j, ln in enumerate(art_you):
                        cv2.text(px + 3, py - 3 + j, ln, shade(P["pink"], dk))
                    cv2.text(px + 9, py - 1, '"you"', shade(P["pink"], 0.8 * dk))
            stamp(cv, pts, a)

        # ================= circle ===================================
        a = fade_window(t, t_circ - 0.35, t_cf + 1.8, 0.45, 0.7)
        if a > 0.01:
            def circ(cv2):
                r = max(4, min(w // 4, h - 10))
                trace = ramp(t, t_circ + 0.15, t_circ + 1.4)
                full = trace >= 1.0
                a1 = 2 * math.pi * trace
                fx.circle(cv2, cx, cy, r, shade(P["ice"], 1.0), "•",
                          a0=-math.pi / 2, a1=a1 - math.pi / 2)
                ang = a1 - math.pi / 2
                lx = cx + int(r * math.cos(ang))
                ly = cy + int(r / 2 * math.sin(ang))
                cv2.put(lx, ly, "●", P["white"])
                if trace > 0.05:
                    fx.line(cv2, cx, cy, lx, ly, shade(P["cyan"], 0.35))
                cv2.put(cx, cy, "+", shade(P["cyan"], 0.6))
                if full:
                    ff = ramp(t, t_cf - 0.4, t_cf + 1.2)
                    cv2.text(cx + 2, cy + 2, "r", shade(P["ice"], 0.8))
                    cv2.ctext(h - 4, "C = 2πr", mix(P["cyan"], P["white"], 0.3))
                    # you rides the circumference
                    if ff > 0:
                        an = t * 1.5
                        px = cx + int(r * math.cos(an))
                        py = cy + int(r / 2 * math.sin(an))
                        cv2.put(px, py, "◆", P["pink"])
            stamp(cv, circ, a)

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
                inf_cy = 1 + r + 1
                if h >= 20:
                    axis_y = int(h * 0.60) + 1
                    amp0 = max(2, min(7, h - axis_y - 3))
                else:
                    axis_y = h - 3
                    amp0 = 2
                axis_y = max(inf_cy + r + 1, min(axis_y, h - 2))

                # the infinity sign fades in above the axis
                kk = ramp(t, t_inf, t_inf + 0.9)
                off = r + 2
                for sgn in (-1, 1):
                    fx.circle(cv2, cx + sgn * off, inf_cy, r,
                              shade(P["violet"], kk), "•", ry=max(1, r // 2))
                if kk > 0.4:
                    cv2.ctext(inf_cy + r + 1, "x → ∞", shade(P["violet"], 0.75 * kk))

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
        a = fade_window(t, t_travel - 0.25, t_unite + 0.3, 0.4, 0.4)
        if a > 0.01:
            def clock(cv2):
                k = ramp(t, t_travel, t_bc + 1.2)      # 0 -> 1 as time rewinds
                dcy = cy - (2 if h >= 22 else 0)
                r = max(5, min(w // 9, h - 10 if h >= 20 else h - 7))

                # dial
                fx.circle(cv2, cx, dcy, r, shade(P["violet"], 0.85), "·", ry=r / 2)
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
                    cv2.text(min(w - 10, cxp + 2), ty - 1, ys, shade(P["rose"], 0.95))
                    cv2.text(x0 + 2, ty - 1, "◀◀ rewind", shade(P["violet"], 0.7))

                # ---- the tools of each age revert to the ones before -----
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
                slot = min(12, max(8, (w - 4) // n))
                total = slot * n
                sx0 = (w - total) // 2
                iy = ty + 2
                if iy + 3 > h:
                    return
                newc = mix(P["ice"], P["cyan"], 0.35)
                oldc = mix(P["amber"], P["gold"], 0.35)
                for i, (ma, oa, lm, lo) in enumerate(pairs):
                    ki = max(0.0, min(1.0, (k * (n + 0.6) - i) * 1.3))
                    sx = sx0 + i * slot + max(0, (slot - 9) // 2)
                    na, nl = max(0.0, 1.0 - ki * 1.1), max(0.0, (ki - 0.12) * 1.1)
                    if na > 0.05:
                        for j, ln in enumerate(ma):
                            for ii, ch in enumerate(ln):
                                if ch != " ":
                                    cv2.put(sx + ii, iy + j, ch,
                                            shade(newc, na))
                    if nl > 0.05:
                        for j, ln in enumerate(oa):
                            for ii, ch in enumerate(ln):
                                if ch != " ":
                                    cv2.put(sx + ii, iy + j, ch,
                                            shade(oldc, nl))
                    if 0.30 < ki < 0.76:
                        for ii in range(9):
                            if h01(i, ii, int(t * 7)) < 0.28:
                                cv2.put(sx + ii, iy + (ii % 3),
                                        "▒" if h01(ii, i) < 0.5 else "░",
                                        shade(P["white"], 0.32))
                    if w >= 66:
                        cv2.text(sx - 1, iy + 3, "%s→%s" % (lm, lo),
                                 shade(mix(newc, oldc, ki), 0.9))
            stamp(cv, clock, a)

        # ---------- unite -------------------------------------------
        a = fade_window(t, t_unite - 0.15, self.t1 + 0.1, 0.3, 0.35)
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
                for gx in range(2, w - 2, 4):
                    for gy in range(2, h - 3, 2):
                        cv2.put(gx, gy, "·", shade(P["pink"], 0.10 * scr))
                for gx in range(2, w - 2, 16):
                    cv2.vline(gx, 2, h - 5, ":", shade(P["pink"], 0.14 * scr))
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
                cv2.text(3, h - 3, "HR %03d BPM" % hr, shade(P["pink"], 0.9))
                cv2.text(3, h - 2, "SIMULATED HEART · 1/1",
                         shade(P["pink"], 0.7))
                if w >= 40:
                    cv2.rtext(h - 3, "SpO₂ 98%", shade(P["ice"], 0.85), right=w - 4)
                    cv2.rtext(h - 2, "sinus rhythm", shade(P["ice"], 0.58),
                              right=w - 4)
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
