"""Scenes: intro, verse 1, verse 2, pre-chorus 1, chorus 1."""

import math

import anim
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


_TEXT_CACHE = [None]


def _corpus_text():
    """The same bytes, flat, for readouts that stream them."""
    if _TEXT_CACHE[0] is None:
        _TEXT_CACHE[0] = (_corpus().decode("ascii", "ignore")
                          .replace("\n", " "))
    return _TEXT_CACHE[0]


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


def _rows(cv):
    """The rows the chrome does not own: 4 .. h-3."""
    return 4, max(4, cv.h - 3)


YOU_OFFS = tuple(i for i in range(len(DATA)) if DATA[i:i + 3] == b"you")


def draw_dump(cv, t, a, head_rows, y0=1, y1=None, width=None, base=0,
              seek_row=None):
    """Memory dump written top-to-bottom to `head_rows` rows, then scrolled
    by `base` bytes.  Row `seek_row` is kept at full ink."""
    w, h = cv.w, cv.h
    if width is None or width > w:
        width = w
    if y1 is None:
        y1 = h - 1
    nb = dump_nb(width)
    for y in range(y0, min(h, y1 + 1)):
        ry = y - y0
        if ry > head_rows:
            break
        part = 1.0
        if ry > head_rows - 1:
            part = head_rows - int(head_rows)
            if part <= 0.02:
                continue
        xmax = 2 + int((width - 4) * part)
        if xmax < 12:
            continue
        _dump_line(cv, y, 0, xmax, base + ry * nb, nb,
                   a * (1.0 if (seek_row is not None and y == seek_row)
                        else 0.75))
        if ry > head_rows - 1 and xmax < width - 3:
            cv.put(xmax + 1, y, "▌", shade(P["white"], 0.9 * a))


class IntroScene(Scene):
    """0 - 15 · POWER ON.

    The machine boots the old-fashioned way, one instrument at a time:

      dead   a dead tube, dust, and a cursor blinking at the world;
      rail   the mains line draws itself across, joints sparking, the
             voltage meter climbing 0 -> 220 V;
      post   the BIOS checklist types line by line, each check lands a
             tiny ripple, the insulation meter climbs on the right;
      grid   a memory test fills cell by cell with a % and address
             counter -- and the panel writes 0x4000 while it happens;
      dump   the lyric bytes scroll past 0x4000 while a read-head hunts
             for the word "you" (79 6F 75) and flashes every hit;
      warm   the title shreds itself, reassembles and locks while SYNC
             climbs to 100% and the tube's brightness ramps up;
      go     the command line asks for the simulation and the raster
             collapses into verse 1.
    """

    key = "intro"
    accent = "phos"

    T_CMD = 11.80

    TITLE = "world.execute(me);"
    GARB = "▓▒░█@#%&$?*+=/\\<>{}[]~^;:"
    BLOCKS = "▓▒░█▚▞◣◢  "

    # ------------------------------------------------------------------
    # phase A -- the dead screen
    # ------------------------------------------------------------------
    def _dead(self, cv, t, a, cy, top, bot):
        if a <= 0.01:
            return
        w = cv.w
        # dead-channel dust, rescattered at 11 Hz
        n = int(w * (bot - top) * 0.045) + 8
        for i in range(n):
            x = 1 + int(h01(i, 91, int(t * 11)) * (w - 2))
            y = top + int(h01(i, 92, int(t * 11)) * (bot - top + 1))
            if h01(i, int(t * 11), 93) < 0.74:
                cv.put(x, y, "·", shade(P["phos_dim"], 0.45 * a))
        # the raster tries to hold a line
        if int(t * 17) % 3:
            cv.hline(2, cy, w - 4, "·", shade(P["phos"], 0.10 * a))
        # the cursor: the machine is about to say something
        if int(t * 9) % 2 == 0:
            cv.put(3, cy, "▮", shade(P["phos"], 0.85 * a))
        if t > 0.28:
            cv.ctext(min(bot, cy + 2), "no signal · standby",
                     shade(P["grey_dim"], 0.9 * a))

    # ------------------------------------------------------------------
    # phase B -- the power rail draws itself, 0 -> 220 V
    # ------------------------------------------------------------------
    def _rail(self, cv, t, a, tr0, tr1, cy, top, bot):
        if a <= 0.01:
            return
        w = cv.w
        x0, x1 = 3, w - 4
        kr = ramp(t, tr0, tr0 + 0.95)
        if kr <= 0.0:
            return
        end = x0 + int((x1 - x0) * kr)
        # the mains line, with a joint every 9 cells
        for x in range(x0, end + 1):
            if x0 + 4 <= x < x1 and (x - x0 - 4) % 9 == 0:
                continue
            cv.put(x, cy, "═", shade(P["amber"], 0.9 * a))
        for jx in range(x0 + 4, min(x1, end), 9):
            tj = tr0 + 0.95 * (jx - x0) / float(x1 - x0)
            if t - tj < 0.28 and int(t * 36) % 3 != 0:
                for s in range(7):          # contact sparks at the joints
                    dx = int((h01(jx, s, int(t * 36)) - 0.5) * 5)
                    dy = int((h01(jx, s, int(t * 36) + 7) - 0.5) * 3)
                    cv.put(jx + dx, cy + dy,
                           ("*", "+", "·", "✶", "·", "+", "*")[s],
                           mix(P["amber"], P["white"], h01(jx, s, 3)))
            else:
                cv.put(jx, cy, "╪", shade(P["amber"], 0.55 * a))
        if kr < 1.0:                       # the drawing head
            cv.put(min(x1, end), cy, "◉", P["white"])
            cv.put(max(x0, end - 1), cy, "▓", shade(P["amber"], 0.8 * a))
            if w >= 56 and cy + 1 <= bot:
                cv.text(max(x0 + 1, end - 4), cy + 1, "laying mains",
                        shade(P["amber"], 0.5 * a))
        else:
            cv.put(x0 - 1, cy, "⊣", shade(P["amber"], 0.9 * a))
            cv.text(x0 - 1, cy - 1 if cy - 1 >= top + 1 else cy + 1, "MAINS",
                    shade(P["amber"], 0.5 * a))
            # locked: the hum rides the line
            if cy + 1 <= bot:
                for k_ in range(3):
                    hx_ = 6 + int((t * 14.0 + k_ * 11.0) % max(1, w - 10))
                    if x0 + 4 < hx_ < x1 - 1 and (hx_ - x0 - 4) % 9:
                        cv.put(hx_, cy + 1, "∿", shade(P["amber"], 0.5 * a))
        # the voltage meter
        V = 220.0 * ramp(t, tr0 + 0.08, tr1)
        if kr < 0.999:
            V *= 0.94 + 0.06 * math.sin(t * 34.0)
        y_v = top
        bw = max(8, min(18, w - 26))
        cv.text(3, y_v, "MAINS %3d V" % int(V), shade(P["amber"], 0.95 * a))
        fx.bar(cv, 3, y_v + 1, bw, V / 220.0, P["amber"], None)
        cv.text(3 + bw + 2, y_v + 1, "50 Hz" if V > 205 else ". . .",
                shade(P["soft"], 0.7 * a))
        if kr >= 1.0 and V > 219.5:
            cv.rtext(y_v, "AC 220 V ✓", shade(P["amber"], 0.95 * a), right=w - 2)
            if t - tr1 < 0.55:
                fx.ripple(cv, x0 + 2, cy, t - tr1, shade(P["amber"], 0.6 * a),
                          n=2, speed=7.0, period=0.55)

    # ------------------------------------------------------------------
    # phase C -- POST: the checklist types, every check lands a ripple
    # ------------------------------------------------------------------
    def _post(self, cv, t, a, t0, top, bot, panel_px):
        if a <= 0.01:
            return
        w = cv.w
        n = len(INIT)
        big = bot - top >= 9
        y_list0 = top + 2 if big else top
        list_rows = max(1, min(n, bot - y_list0 + 1 - (0 if big else 1)))
        right = (panel_px - 1) if (panel_px and w >= 96) else (w - 2)
        if big and t >= t0 + 0.62:
            txt = "DSH/BIOS v1.30"
            if right - 4 > 3 + sw(txt) + 24:
                txt = "DSH/BIOS v1.30  ·  world.execute(me);"
            cv.text(3, top, txt, shade(P["soft"], 0.9 * a))
            cv.hline(3, top + 1, max(10, right - 6), "─",
                     shade(P["phos"], 0.25 * a))
        step = 0.140 if big else 0.128
        shown = min(n, int((t - t0) / step) + 1)
        if shown < 1:
            return
        i0 = max(0, shown - list_rows)
        # ripples first, under everything, so no ✓ is ever eaten by one
        for i in range(i0, shown):
            _tag, _msg, st, _note = INIT[i]
            age = (t - (t0 + i * step)) - 0.14
            if 0.0 <= age < 0.30 and st != "warn":
                fx.ripple(cv, 3, y_list0 + (i - i0), age,
                          shade(P["phos"], 0.7 * a), n=1, speed=9.0,
                          period=0.42)
        for i in range(i0, shown):
            tag, msg, st, note = INIT[i]
            at = t0 + i * step
            row = y_list0 + (i - i0)
            s, typing = fx.typewriter(msg, t - at, 230.0)
            s = s[:max(6, w - 24)]
            landed = (t - at) >= 0.14
            if not landed:
                mark, mc = "·", shade(P["grey_dim"], 0.9 * a)
            elif st == "warn":
                mark, mc = "!", shade(P["amber"], 0.95 * a)
            else:
                mark, mc = "✓", shade(P["phos"], 0.95 * a)
            age = (t - at) - 0.14
            cv.text(3, row, mark, mc)
            cv.text(5, row, tag.ljust(5), shade(P["phos_dim"], 0.9 * a))
            cv.text(11, row, s,
                    shade(P["soft"] if landed else P["white"], 0.85 * a))
            if typing and int(t * 12) % 2 == 0:
                cv.put(min(w - 2, 11 + sw(s)), row, "▮", P["white"])
            if note and landed and (not panel_px or w >= 96):
                cv.rtext(row, note, shade(P["amber"], 0.6 * a), right=right)
        # the pending checks wait below, dim and dotted, like a real BIOS
        for i in range(shown, min(n + 0, i0 + list_rows)):
            tag, msg, _st, _note = INIT[i]
            row = y_list0 + (i - i0)
            cv.text(5, row, tag.ljust(5), shade(P["grey_dk"], 0.9 * a))
            for x in range(11, min(right - 6, 11 + sw(msg)), 3):
                cv.put(x, row, "·", shade(P["grey_dk"], 0.9 * a))
        y_bar = y_list0 + list_rows
        if y_bar <= bot:
            kk = shown / float(n)
            cv.text(3, y_bar, "progress", shade(P["grey_dim"], 0.8 * a))
            fx.bar(cv, 12, y_bar, max(8, min(24, right - 16)), kk,
                   P["phos"], None)
            cv.rtext(y_bar, "%2d/%d %s" % (shown, n,
                                           "PASS" if shown >= n else ""),
                     shade(P["phos"] if shown >= n else P["grey"], 0.9 * a),
                     right=right)
            # the data bus never stops while the machine checks itself
            if right >= 58:
                anim.hexrow(cv, min(right - 26, w - 28), y_bar + 1, 8, t,
                            shade(P["phos_dim"], 0.85 * a), seed=7, hz=9)
        # a boot log scrolls underneath: the machine narrating itself
        if y_list0 + list_rows + 2 <= bot:
            anim.ticker(cv, y_list0 + list_rows + 2,
                        "AC 220 V ✓  ·  mem 0x4000  ·  love.ko loaded  ·  "
                        "refs: you  ·  PROT 2.0 GΩ  ·  CPU 1 heart @ 130 BPM"
                        "  ·  FS /world/mili mounted  ·  clock locked  ·  ",
                        t, speed=16.0, fg=shade(P["grey_dim"], 0.85 * a),
                        x0=3, x1=right)

    def _insul(self, cv, t, a, t0, top, px):
        """The protection lyric, instrumented: insulation resistance."""
        if a <= 0.01:
            return
        w = cv.w
        x = px + 1
        r_ = 2.0 * ramp(t, t0 + 0.25, t0 + 2.05)
        cv.text(x, top + 2, "INSULATION", shade(P["cyan"], 0.8 * a))
        cv.text(x, top + 3, "R %4.2f GΩ" % r_, shade(P["cyan"], 0.95 * a))
        fx.bar(cv, x, top + 4, min(20, w - x - 4), r_ / 2.0, P["cyan"], None)
        cv.text(x, top + 5, "dielectric", shade(P["grey_dim"], 0.8 * a))
        if r_ >= 1.99:
            cv.text(x + 12, top + 3, "✓", shade(P["cyan"], a))

    # ------------------------------------------------------------------
    # phase D -- the memory test grid
    # ------------------------------------------------------------------
    def _memgrid(self, cv, t, a, k_g, top, bot, x1):
        if a <= 0.01 or k_g <= 0.0:
            return
        w = cv.w
        big = bot - top >= 9
        y_st = top + 2 if big else top
        x0 = 3
        x1 = min(x1, w - 3)
        if x1 - x0 < 8:
            return
        cols = max(3, (x1 - x0 + 1) // 2)
        rows = max(1, bot - y_st)
        total = cols * rows
        nn = int(k_g * total)
        addr = int(k_g * 0x4000)
        # a couple of bad cells get found and remapped, like 1985 intended
        bad1, bad2 = int(total * 0.31), int(total * 0.57)
        if k_g < 0.999:
            lab = "MEMORY TEST  %3d%%   0x%04X / 0x4000" % (int(k_g * 100),
                                                             addr)
            if bad1 <= nn < bad1 + 60 or bad2 <= nn < bad2 + 60:
                lab += "   remap ✕"
            cv.text(3, y_st, lab, shade(P["phos"], 0.95 * a))
        else:
            cv.text(3, y_st, "MEMORY TEST  640K OK ✓  ·  1 bad block remapped",
                    shade(P["phos"], 0.95 * a))
            cv.rtext(y_st, "EDO · 70ns", shade(P["grey_dim"], 0.8 * a),
                     right=w - 2)
        for r_i in range(rows):
            y = y_st + 1 + r_i
            if y > bot:
                break
            for c_i in range(cols):
                idx = r_i * cols + c_i
                x = x0 + c_i * 2
                if idx == bad1 and bad1 <= nn < bad1 + 60:
                    cv.put(x, y, "✕" if int(t * 9) % 2 else "▓", P["red"])
                elif idx == bad2 and bad2 <= nn < bad2 + 60:
                    cv.put(x, y, "✕" if int(t * 9) % 2 else "▓", P["red"])
                elif idx < nn - 2:
                    cv.put(x, y, "█", shade(P["phos"], 0.5))
                elif idx < nn:
                    cv.put(x, y, "▓" if int(t * 20) % 2 else "▒", P["phos"])
                else:
                    cv.put(x, y, "░", shade(P["phos_dim"], 0.45 * a))
        if k_g >= 0.999:
            fx.ripple(cv, x0 + cols - 1, y_st + 1 + (rows - 1) // 2,
                      (t * 0.9) % 1.0, shade(P["phos"], 0.4 * a),
                      n=1, speed=8.0, period=1.0)

    # ------------------------------------------------------------------
    # the memory panel: writes to 0x4000, then reads back forever
    # ------------------------------------------------------------------
    def _panel(self, cv, t, a, t_w0, t_w1, top, bot, px):
        if a <= 0.01:
            return
        w = cv.w
        pw = w - 2 - px
        phh = min(bot - top, 17)
        if phh < 6 or pw < 24:
            return
        bgp = mix(P["black"], P["phos"], 0.06)
        fx.panel(cv, px, top, pw, phh, shade(P["phos_dim"], 0.8), bgp,
                 title=" memory ", title_fg=shade(P["white"], 0.8 * a))
        x = px + 2
        rrows = phh - 2
        nb2 = max(1, min(4, (pw - 6) // 3))
        kk = ramp(t, t_w0, t_w1)
        if kk < 0.999:
            wr = int(kk * 0x4000)
            cv.text(x, top + 1, ("writing memory .... %3d%%"
                                 % int(kk * 100))[:pw - 4],
                    shade(P["phos"], 0.9 * a), bgp)
            for i in range(rrows - 1):
                ad = max(0, wr - (rrows - 1 - i) * 12)
                base_ = ad * 4
                s = "%04X " % (ad & 0xFFFF)
                for k_ in range(nb2):
                    s += "%02X " % DATA[(base_ + k_) % len(DATA)]
                cv.text(x, top + 2 + i, s[:pw - 4],
                        shade(P["phos_dim"], 1.05 * a), bgp)
            cv.rtext(top + phh - 1, "read %05d" % wr,
                     shade(P["phos"], 0.8 * a), bg=bgp, right=px + pw - 2)
        else:
            sc = int((t - t_w1) * 190.0)
            for i in range(rrows - 1):
                ad = (sc + i * 12) & 0xFFFF
                base_ = ad * 4
                s = "%04X " % ad
                for k_ in range(nb2):
                    s += "%02X " % DATA[(base_ + k_) % len(DATA)]
                cv.text(x, top + 2 + i, s[:pw - 4],
                        shade(P["phos_dim"], 0.75 * a), bgp)
            cv.rtext(top + phh - 1, "read %05X" % ((sc * 12 + 0x4000) & 0xFFFF),
                     shade(P["phos"], 0.8 * a), bg=bgp, right=px + pw - 2)

    # ------------------------------------------------------------------
    # phase F -- the title: shredded, reassembled, locked
    # ------------------------------------------------------------------
    def _title_sig(self, cv, t, u, ty):
        w, h = cv.w, cv.h
        title = self.TITLE
        n = len(title)
        x0 = (w - n) // 2
        bandw = min(w - 2, n + 10)
        bx = (w - bandw) // 2
        step = int((u + 20.0) * 22)

        # identity confidence: how much of the title is currently itself
        if u < 0.15:
            ident = ramp(u, 0.02, 0.15) * 0.58
            scat = 0.22 * ramp(u, 0.08, 0.15)
        elif u < 0.55:
            uu = ramp(u, 0.15, 0.55)
            ident = 0.58 * (1.0 - uu)
            scat = 0.22 + 0.78 * fx.ease_out(uu)
        else:
            v = ramp(u, 0.52, 1.20)
            ident = v
            scat = (1.0 - fx.ease_out(v)) ** 1.6

        # a strip of dead signal so the fragments read over the dump
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
                if not (4 <= yy < h - 1):
                    continue
                for xx in range(bxx, min(w, bxx + bw)):
                    cv.put(xx, yy,
                           self.BLOCKS[int(h01(xx, yy, step, 105)
                                           * len(self.BLOCKS))],
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
                if not (4 <= int(py) < h - 1):
                    continue
                gl = self.GARB[int(h01(i, j, step, 31) * len(self.GARB))]
                a_ = (0.16 + 0.5 * ident) * (0.45 + 0.55 * h01(i, j, 33))
                cv.put(int(px), int(py), gl,
                       mix(P["black"], mix(P["phos"], P["red"], 0.3), a_))

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
            a_ = 0.55 + 0.45 * min(1.0, ident * 1.3 + 0.15)
            if locked:
                glyph = ch
                c = mix(P["white"], P["phos"], 0.12 * h01(i, 13))
                if ident - need < 0.07:
                    glyph, c = "█", P["white"]
            else:
                glyph = self.GARB[int(h01(i, step, 15) * len(self.GARB))]
                c = mix(P["phos"], P["red"], 0.3 + 0.5 * h01(i, step, 17))
            if not (4 <= y < h):
                continue
            cv.put(x, y, glyph, mix(P["black"], c, a_))
            if scat > 0.12:
                sx = -1 if jx > 0 else 1
                if 0 <= x + sx < w:
                    cv.put(x + sx, y, glyph, mix(P["black"], c, a_ * 0.32))
                if x > 0:
                    cv.put(x - 1, y, "·", mix(P["black"], (255, 62, 84), a_ * 0.5))
                if x + 1 < w:
                    cv.put(x + 1, y, "·", mix(P["black"], (86, 208, 255), a_ * 0.5))

        # SYNC meter: the program's own account of the lock
        if u >= 0.40:
            mw = max(6, min(20, bandw - 18))
            lab = "SYNC" if nlock < n else "LOCK"
            cv.text(bx + 2, ty + 2, lab, mix(P["phos"], P["black"], 0.30))
            cv.put(bx + 6, ty + 2, "▕", mix(P["phos"], P["black"], 0.5))
            fx.bar(cv, bx + 7, ty + 2, mw, nlock / float(n),
                   mix(P["phos"], P["white"], 0.25), None)
            cv.text(bx + 8 + mw, ty + 2, "%3d%%" % (100 * nlock // n),
                    mix(P["phos"], P["white"], 0.45))
            if nlock >= n:
                cv.text(bx + 14 + mw, ty + 2, "40ms",
                        mix(P["grey"], P["black"], 0.3))

        if ident > 0.965:
            cv.frame(bx, ty - 1, bandw, 3, mix(P["phos"], P["black"], 0.22),
                     style="thin")

    # ------------------------------------------------------------------
    def draw(self, cv, ctx):
        t = ctx.t
        w, h = cv.w, cv.h
        top, bot = _rows(cv)
        cy = max(top + 2, (top + bot) // 2)
        panel_on = w >= 78 and bot - top >= 7
        px = (w - 36) if panel_on else w
        t_pwr = cue("Switch on the power line")
        t_prot = cue("Remember to put on protection")
        t_piece = cue("Lay down your pieces")
        t_data = cue("Fill in my data parameters initialisation")
        t_world = cue("Setup our new world")

        T_RAIL0 = t_pwr + 0.45            # 0.55  the rail starts drawing
        T_RAIL1 = T_RAIL0 + 1.30          # 1.85  220 V locked
        T_POST0 = t_prot                  # 1.74  the lyric: protection
        T_LIST0 = t_prot + 0.31           # 2.05  checklist (rail is gone)
        T_MEM0, T_MEM1 = t_piece + 0.43, t_data + 0.05   # 4.30 .. 7.50
        T_DUMP0 = T_MEM1                  # 7.50  the lyric dump
        T_FILL1 = T_DUMP0 + 0.85          # 8.35  fill done, scroll starts
        T_WARM0 = t_world - 0.05          # 11.05 tube warm-up + title
        y_ct = top + 2 if bot - top >= 12 else top

        # ---- A · dead screen ------------------------------------------
        a_dead = fade_window(t, 0.0, T_RAIL0 + 0.30, 0.0, 0.20)
        if a_dead > 0.01:
            self._dead(cv, t, a_dead, cy, top, bot)

        # ---- B · power rail -------------------------------------------
        a_rail = fade_window(t, T_RAIL0 - 0.05, 2.40, 0.05, 0.30)
        if a_rail > 0.01:
            self._rail(cv, t, a_rail, T_RAIL0, T_RAIL1, cy, top, bot)

        # ---- C · POST -------------------------------------------------
        a_post = fade_window(t, T_LIST0 - 0.02, 4.10, 0.03, 0.18)
        if a_post > 0.01:
            self._post(cv, t, a_post, T_LIST0, top, bot,
                       px if panel_on else None)
        if panel_on:
            self._insul(cv, t, fade_window(t, T_POST0, 3.90, 0.12, 0.25),
                        T_POST0, top, px)

        # ---- D · memory grid + the panel writing 0x4000 ---------------
        a_grid = fade_window(t, T_MEM0, T_MEM1 + 0.55, 0.30, 0.35)
        if a_grid > 0.01:
            self._memgrid(cv, t, a_grid, ramp(t, T_MEM0, T_MEM1), top, bot,
                          (px - 2) if panel_on else (w - 3))
        if panel_on:
            self._panel(cv, t, fade_window(t, T_MEM0 - 0.20, self.t1,
                                           0.30, 0.0),
                        T_MEM0, T_MEM1, top, bot, px)

        # ---- E · the lyric dump, hunted for "you" ---------------------
        dump_end = t_world + (0.10 if bot - top >= 12 else -0.45)
        a_dump = fade_window(t, T_DUMP0 - 0.35, dump_end, 0.55, 0.45)
        if a_dump > 0.01 and h >= 8:
            y_d0, y_d1 = y_ct, h - 5
            dwid = (px - 1) if panel_on else (w - 1)
            nb = dump_nb(dwid)
            rows_vis = y_d1 - y_d0 + 1
            seek = y_d1
            fill = ramp(t, T_DUMP0, T_FILL1)
            scroll = 3.0 if nb >= 10 else 3.8
            base = int(max(0.0, t - T_FILL1) * scroll) * nb
            draw_dump(cv, t, a_dump, fill * (rows_vis + 0.9), y0=y_d0,
                      y1=y_d1, width=dwid, base=base, seek_row=seek)
            lenD = len(DATA)
            sb = (base + (seek - y_d0) * nb) % lenD
            # a "you" on the seek row right now -- or just leaving it
            flash = None
            for o in YOU_OFFS:
                d0 = (o - sb) % lenD
                if d0 < nb - 2:
                    flash = (o, d0, 1.0)
                    break
            if flash is None:
                for o in YOU_OFFS:
                    d1 = (o - sb + nb) % lenD
                    if d1 < nb - 2:
                        frac = ((t - T_FILL1) * scroll) % 1.0
                        flash = (o, d1, max(0.25, 1.0 - 0.75 * frac))
                        break
            # the read head
            if flash is not None:
                hx_ = 6 + flash[1] * 3
            else:
                hx_ = 6 + int(nb * abs(math.sin((t - T_DUMP0) * 2.3))) * 3
            if hx_ + 1 < dwid:
                cv.put(hx_, seek, "◉", shade(P["white"], 0.95 * a_dump))
            if flash is not None and fill >= 1.0:
                o, d0, kk = flash
                bga = mix(P["black"], P["amber"], 0.30 * kk)
                blink = int(t * 14) % 2 == 0
                cc = P["white"] if blink else P["amber"]
                m_ = min(3, nb - d0)
                sby = "".join("%02X " % DATA[(o + i) % lenD]
                              for i in range(max(1, m_)))
                cv.text(6 + d0 * 3, seek, sby, shade(cc, kk * a_dump), bga)
                acol = 7 + nb * 3
                av = "".join(chr(DATA[(o + i) % lenD])
                             if 32 <= DATA[(o + i) % lenD] < 127 else "·"
                             for i in range(max(1, m_)))
                cv.text(acol + d0, seek, av,
                        shade(P["pink"] if blink else P["rose"], kk * a_dump),
                        bga)
                fx.ripple(cv, 6 + d0 * 3, seek, (t * 1.4) % 1.0,
                          shade(P["amber"], 0.5 * kk), n=1, speed=6.0,
                          period=1.4)
                cv.text(3, h - 4, "» 0x%04X  79 6F 75  \"you\"  FOUND %s"
                        % (o, "✓" if blink else " "),
                        shade(P["amber"], 0.95 * a_dump))
            elif fill >= 1.0:
                cv.text(3, h - 4, "seek 79 6F 75 \"you\"  ·  @0x%04X" % sb,
                        shade(P["grey_dim"], 0.9 * a_dump))

        # ---- F · the music, as a spectrum -----------------------------
        if t > 4.4:
            yb = h - 2
            e = ctx.e_at(t)
            for x in range(0, w, 2):
                v = abs(math.sin(x * 0.055 + t * 1.7)) * (0.35 + 0.9 * e)
                v *= 0.55 + 0.45 * abs(math.sin(x * 0.013 + t * 0.6))
                lvl = min(1, int(v * 2.2))
                for kk in range(min(2, lvl + 1)):
                    cv.put(x, yb - kk,
                           "▁▃"[min(1, kk + (1 if lvl else 0))],
                           shade(P["phos_dim"], 0.7 - kk * 0.15))

            # ---- E2 · one parameter, doubted and corrected ----------
            # the machine fills in its own line of the dump: devotion,
            # typed once, wiped out, then retyped with the decimals it
            # decided you deserve -- the number has to be exactly right
            # before it can bring itself to mean it.  Drawn over the
            # spectrum: the line sits inside the music, not behind it
            if a_dump > 0.01 and h >= 9 and w >= 26:
                t_d0 = T_DUMP0 + 0.30
                t_d1 = t_d0 + 1.30
                v1, _k1, p1 = anim.type_loop(
                    t, t_d0, "devotion = 1", cycles=1, cps=16.0,
                    hold=0.25, wipe=0.20, gap=0.10, del_last=True)
                v2, _k2, p2 = anim.type_loop(
                    t, t_d1, "devotion = 1.00", cycles=1, cps=16.0,
                    hold=0.25)
                line, ph = (v1, p1) if v1 else (v2, p2)
                if line:
                    ok_ = line == "devotion = 1.00"
                    cv.text(3, h - 3, line,
                            shade(mix(P["phos"], P["white"],
                                      0.4 if ok_ else 0.0),
                                  0.95 * a_dump))
                    if ph in ("type", "wipe") and int(t * 5) % 2 == 0:
                        cv.put(3 + sw(line), h - 3, "▮",
                               shade(P["phos"], 0.55 * a_dump))

        # ---- G · tube warm-up + the title ------------------------------
        if t >= T_WARM0 - 0.20:
            kb = 0.55 + 0.45 * ramp(t, T_WARM0, T_WARM0 + 1.05)
            if kb < 0.995:
                cv.dim(kb)
        if t >= T_WARM0:
            u = t - T_WARM0
            ty = (top + 1) if bot - top < 12 else (top + (bot - top) // 2 - 1)
            if h >= 11:
                self._title_sig(cv, t, u, ty)
            else:
                shown, typing = fx.typewriter(self.TITLE, max(0.0, u - 0.10),
                                              30.0)
                cv.ctext(top, shown, P["white"])
                if typing and int(t * 12) % 2 == 0:
                    cxm = cv.w // 2
                    cv.put(min(w - 2, cxm - sw(shown) // 2 + sw(shown)),
                           top, "▮", P["white"])
                cv.ctext(min(bot, top + 1), "SYNC %3d%%"
                         % int(100 * ramp(u, 0.10, 1.20)),
                         shade(P["phos"], 0.85))
            lines = (
                "—  Mili  ·  Miracle Milk (2016)  —",
                "a terminal music video · 终端 ASCII MV",
                "中英双语字幕 · 与歌同步 · ♥",
                "NTSC 525/60 · 60Hz · PHOSPHOR P1",
            )
            for j, line in enumerate(lines):
                at = 0.95 + j * 0.30
                if u < at:
                    break
                if ty + 3 + j > bot - 3:
                    break
                shown, _tp = fx.typewriter(line, u - at, 46.0)
                cv.ctext(ty + 3 + j, shown,
                         shade(P["phos"] if j < 2 else P["phos_dim"], 0.85))
            if h >= 30 and w >= 60:
                rrows = ("boot ok · %d/%d checks ✓" % (len(INIT), len(INIT)),
                         "640K · love.ko · refs \"you\" @ 0x%04X" % YOU_OFFS[0],
                         "AC 220 V · 50 Hz · sim armed")
                for j, s_ in enumerate(rrows):
                    at = 1.55 + j * 0.22
                    if u < at or ty + 8 + j > bot - 3:
                        break
                    s2, _tp = fx.typewriter(s_, u - at, 90.0)
                    cv.ctext(ty + 8 + j, s2, shade(P["phos_dim"], 0.8))

        # ---- H · the command line --------------------------------------
        if t >= self.T_CMD:
            yc = (bot - 2) if h >= 13 else bot
            shown, typing = fx.typewriter("$ exec --start simulation · arg=me",
                                          t - self.T_CMD, 36.0)
            cv.text(3, yc, shown[:max(8, w - 6)], P["white"])
            if typing and int(t * 10) % 2 == 0:
                cv.put(min(w - 2, 3 + sw(shown)), yc, "▮", P["white"])
            if yc + 1 <= bot:
                if t >= self.T_CMD + 0.75:
                    k2 = ramp(t, self.T_CMD + 0.75, self.T_CMD + 1.25)
                    cv.text(3, yc + 1, "start" + "." * (1 + int(t * 4) % 3),
                            shade(P["phos"], k2))
                if t >= self.T_CMD + 1.25:
                    left = 3 - int((t - self.T_CMD - 1.25) / 0.42)
                    if left > 0:
                        cv.text(w // 2 - 10, yc + 1, "simulation starts in",
                                shade(P["grey"], 0.9))
                        for i in range(left):
                            cv.put(w // 2 + 13 + i * 3, yc + 1, "▓", P["white"])

        # ---- I · the raster collapses into verse 1 ---------------------
        if t > 14.15:
            k = ramp(t, 14.15, 15.0)
            for y in range(4, h - 1):
                d = abs(y - cy) / max(1, cy)
                if d < k * 1.15:
                    ch = "█" if d < k * 0.9 else "▄"
                    c = mix(P["white"], P["phos"], min(1.0, d * 1.4))
                    cv.hline(0, y, w, ch, shade(c, 0.35 + 0.65 * k))


# ==========================================================================
# 1 · VERSE 1 — object creation
# ==========================================================================
#
# Nothing in this beat is allowed to be a finished picture: the world is
# assembled in front of the viewer and keeps running afterwards, in four moves.
#
#   build  the floor unrolls out of the horizon, the power line draws itself
#          left to right, a survey box measures out where the object will go,
#          the pieces drop, the robot is pulled together out of scattered
#          phosphor, the dome is traced arc by arc and a city stands up;
#   morph  the bare cable turns insulated through a cell-wise dissolve, the
#          target value resolves out of random hex, `// immutable` locks;
#   track  a build ledger, a love counter, a star count, an allocation address
#          and a memory pointer: every change is instrumented as it happens;
#   hand   the finished tableau breaks into speckle so verse 2's grid can
#          build through the holes instead of fading in after it.

_V1_BEAT = 60.0 / 130.0
_V1_STEPS = ("PWR", "PROT", "PIECE", "OBJ", "DATA", "WORLD", "SIM")
_V1_POSE_NAMES = ("idle", "reach", "reach2", "sad")
_V1_MICRO3 = (" ▄▄▄▄▄ ", " █ ◉◉ █ ", " ▀▀▀▀▀ ")
_V1_MICRO2 = (" ▄▄▄▄▄ ", " █ ◉◉ █ ")


class _V1Clip(object):
    """A canvas view that refuses rows outside the content band.

    Used when handing the canvas to a primitive (assemble) that scatters cells
    around a sprite: the scatter must never land on the tube's telemetry rows.
    """

    __slots__ = ("cv", "lo", "hi", "w", "h")

    def __init__(self, cv, lo, hi):
        self.cv, self.lo, self.hi = cv, lo, hi
        self.w, self.h = cv.w, cv.h

    def put(self, x, y, ch, fg=None, bg=None):
        if self.lo <= y <= self.hi:
            self.cv.put(x, y, ch, fg, bg)


def _v1_pad(rows):
    """Pad a sprite to one width so poses / bobs never shift the box."""
    mw = max(sw(r) for r in rows)
    return tuple(r + " " * (mw - sw(r)) for r in rows), mw


def _v1_poses(big):
    """Every pose padded to one common width, so nothing jumps sideways."""
    names = _V1_POSE_NAMES if big else ("idle", "reach", "sad")
    raw = [(art.scale2(art.ME[n]) if big else list(art.ME[n])) for n in names]
    mw = max(sw(r) for rows in raw for r in rows)
    return tuple(tuple(r + " " * (mw - sw(r)) for r in rows) for rows in raw)


_V1_BIG = _v1_poses(True)            # 14 rows each, 20 wide
_V1_MID = _v1_poses(False)           #  7 rows each, 10 wide


def _v1_eyes(poses):
    """Where each pose keeps its eyes (sad has closed eyes: nothing to poke)."""
    out = []
    for rows in poses:
        out.append(tuple((j, x) for j, line in enumerate(rows)
                         for x, c in enumerate(line) if c == "◉"))
    return tuple(out)


_V1_EYES_BIG = _v1_eyes(_V1_BIG)
_V1_EYES_MID = _v1_eyes(_V1_MID)


def _v1_layout(w, h):
    """All the geometry of the beat, recomputed from (w, h) every frame.

    Content lives in rows 4 .. h-3: rows 0..3 are the tube's telemetry, the
    bottom two rows are the AGC line and the progress bar, so nothing here may
    ever touch them.
    """
    y0, y1 = 4, h - 3
    D = max(1, y1 - y0 + 1)
    two = D >= 11                      # one spare row for label + cable
    lab_y = y0
    cab_y = y0 + 1 if two else y0
    sky_top = cab_y + 1
    grid_max = 4 if D >= 18 else (3 if D >= 12 else
                                  (2 if D >= 7 else (1 if D >= 5 else 0)))
    grid_min = 0 if D < 5 else 1
    cands = ((_V1_BIG[0], "big"), (_V1_MID[0], "mid"),
             (art.ME["tiny"], "small"), (_V1_MICRO3, "small"),
             (_V1_MICRO2, "small"))
    rows, gr, horizon, tier = None, 0, y1 + 1, "small"
    for art_rows, tier_name in cands:
        mw = max(sw(r) for r in art_rows)
        if w < mw + 12 and art_rows is not _V1_MICRO2:
            continue
        for g in range(grid_max, grid_min - 1, -1):
            hor = y1 - g
            if len(art_rows) <= hor - sky_top:
                rows, gr, horizon, tier = art_rows, g, hor, tier_name
                break
        if rows is not None:
            break
    if rows is None:
        rows, gr, horizon, tier = _V1_MICRO2, 0, y1 + 1, "small"
    mh = len(rows)
    mw = max(sw(r) for r in rows)
    rx = max(1, w // 2 - mw // 2)
    top = max(sky_top, horizon - mh)
    right_x = rx + mw + 3
    right_w = w - 2 - right_x
    panel = None
    if D >= 10 and right_w >= 20:
        ph = min(9, horizon - sky_top)
        if ph >= 6:
            pw = min(30, right_w)
            panel = (w - 2 - pw, sky_top, pw, ph)
    compact = None
    if panel is None and right_w >= 13 and D >= 6:
        compact = (right_x, sky_top, right_w)
    sky_x = 0
    if w >= 70:
        sky_x = max(rx + mw + 4, w - 30)
        if sky_x > w - 10:
            sky_x = 0
    orbit_rx = min(mw // 2 + 5, max(3, (w - 8) // 2 - 2))
    return dict(w=w, h=h, y0=y0, y1=y1, D=D, two=two, lab_y=lab_y, cab_y=cab_y,
                sky_top=sky_top, grid_rows=gr, horizon=horizon, rows=rows,
                mh=mh, mw=mw, rx=rx, top=top, tier=tier, right_x=right_x,
                right_w=right_w, panel=panel, compact=compact, sky_x=sky_x,
                orbit_rx=orbit_rx)


def _v1_floor(cv, L, t, k, dim, hot):
    """The floor unrolls out of the horizon, then keeps refreshing itself."""
    w = cv.w
    hor, y1 = L["horizon"], L["y1"]
    gr = L["grid_rows"]
    if gr <= 0 or hor > y1:
        return
    cxm = w // 2
    hk = min(1.0, k * 1.8)
    half = int(cxm * hk)
    cv.hline(cxm - half, hor, 2 * half + 1, "─", dim)
    if hk >= 1.0:
        for x in range(int(t * 9) % 9, w, 9):
            cv.put(x, hor, "┬", mix(dim, hot, 0.4))
    # depth rules: each row appears as the world's edge is pushed outwards
    for j in range(1, gr + 1):
        at = (j - 1) * 0.15
        rk = ramp(k, at, at + 0.55)
        if rk <= 0.0:
            continue
        ww = max(1, int(w * rk))
        ph = (t * 0.85 + j * 0.31) % 1.0
        if j == gr:
            ch = "═" if ph < 0.26 else ("┄" if ph < 0.44 else "─")
        else:
            ch = "┄" if ph < 0.26 else "─"
        col = hot if ph < 0.26 else dim
        cv.hline(0, hor + j, ww, ch, col)
        for x in range((int(t * 8) + j * 4) % 6, ww, 6):
            if (t * 0.75 + h01(x, hor + j, 3) * 2.0) % 1.0 < 0.2:
                cv.put(x, hor + j, "┼", hot)
    # the fan of floor lines: they run away from the viewer, one cell per row,
    # and their cells flip over as the field keeps being recomputed
    side = min(11, max(2, w // 9))
    xo = int(round(math.sin(t * 0.5) * 1.2))
    for j in range(1, gr + 1):
        f = (j / float(gr)) ** 1.4
        seen = set()
        for i in range(-side, side + 1):
            u = i / float(side)
            if k * 1.45 - abs(u) * 0.72 <= 0.0:
                continue
            x = int(round(cxm + u * (w * 0.66) * f)) + xo
            if x < 1 or x >= w - 1 or x in seen:
                continue
            seen.add(x)
            slope = "╱" if u < -0.06 else ("╲" if u > 0.06 else "│")
            p = (t * 0.8 + h01(i, j, 5) * 2.0 + j * 0.27) % 1.0
            if p < 0.14:
                cv.put(x, hor + j, "┼", hot)
            elif p < 0.30:
                cv.put(x, hor + j, "·", mix(dim, hot, 0.55))
            else:
                cv.put(x, hor + j, slope, dim)


def _v1_trace(cv, L, t, a):
    """The AC construction signal: the world's own waveform, still empty."""
    if a <= 0.03:
        return
    w = cv.w
    st, hor = L["sky_top"], L["horizon"]
    if hor - st < 2:
        return
    cy = min(st + 2, hor - 1)
    x0, x1 = 2, w - 3
    dim = shade(P["amber"], 0.24 * a)
    hot = shade(P["amber"], 0.85 * a)
    ph = t * 6.2
    cv.hline(x0, cy, x1 - x0 + 1, "·", dim)
    for x in range(x0, x1 + 1):
        v = math.sin((x - x0) * 0.17 - ph)
        yv = cy - int(round(v))
        if st <= yv <= hor - 1:
            cv.put(x, yv, "▄" if v > 0 else "▀", mix(hot, P["white"], 0.25))
        if abs(v) > 0.86:
            cv.put(x, cy, "·", shade(hot, 0.5))
    hx = x0 + int((t * 23.0) % max(1, x1 - x0))
    cv.put(hx, cy, "◉", mix(hot, P["white"], 0.6))


def _v1_stars(cv, L, t, k, blocked):
    """Stars switch on in a ripple from the centre, then keep twinkling."""
    if k <= 0.0:
        return
    w = cv.w
    st, hor = L["sky_top"], L["horizon"]
    span = max(1, hor - st)
    cxm = w / 2.0
    for i in range(30):
        sx = 2 + int(h01(i, 41) * (w - 4))
        sy = st + int(h01(i, 42) * span)
        if blocked(sx, sy):
            continue
        d = math.hypot((sx - cxm) / max(1.0, cxm),
                       (hor - sy) / float(span)) * 0.7
        if k < d:
            continue
        tw = (t * (0.8 + 0.9 * h01(i, 43)) + h01(i, 44) * 2.0) % 1.0
        if tw < 0.10:
            cv.put(sx, sy, "✦", P["white"])
        elif tw < 0.5:
            cv.put(sx, sy, "+", shade(P["ice"], 0.55 + 0.4 * tw))
        else:
            cv.put(sx, sy, "·", shade(P["ice"], 0.75))


def _v1_dome(cv, L, t, k, t0, blocked):
    """The horizon dome is drawn arc by arc; a planet rolls along it."""
    if k <= 0.0:
        return
    w = cv.w
    st = L["sky_top"]
    hor = min(L["horizon"], L["y1"])
    rad = min(int(w * 0.46), 62)
    ry = max(2, min(7, int((hor - st) * 0.35) + 1))
    cxm = w // 2
    n = max(24, min(rad, 64))
    drawn = int((n - 1) * k)
    for i in range(n):
        ang = math.pi + math.pi * i / float(n - 1)
        x = int(round(cxm + rad * math.cos(ang)))
        y = int(round(hor + ry * math.sin(ang)))
        if not (1 <= x < w - 1) or not (st <= y <= hor) or blocked(x, y):
            continue
        g = i / float(n - 1)
        if i < drawn:
            if (g * 2.4 - t * 0.6) % 1.0 < 0.06:
                cv.put(x, y, "✦", mix(P["ice"], P["white"], 0.5))
            elif (g * 5.1 - t * 0.9) % 1.0 < 0.12:
                cv.put(x, y, "+", shade(P["ice"], 0.7))
            else:
                cv.put(x, y, "·", shade(P["ice"], 0.8))
        elif i == drawn:
            cv.put(x, y, "◍", mix(P["ice"], P["white"], 0.7))
    if k >= 1.0:
        a = math.pi + ((t - t0) * 0.5) % math.pi
        px = int(round(cxm + rad * math.cos(a)))
        py = int(round(hor + ry * math.sin(a)))
        if 1 <= px < w - 1 and st <= py <= hor and not blocked(px, py):
            cv.put(px, py, "◍", mix(P["violet"], P["white"], 0.6))
            if py - 1 >= st:
                cv.put(px, py - 1, "·", P["violet"])


def _v1_city_geom(L):
    """Shared geometry of the skyline: (base, x0, n, heights)."""
    if L["sky_x"] <= 0:
        return None
    w = L["w"]
    hor = min(L["horizon"], L["y1"] + 1)
    base = hor - 1
    x0 = L["sky_x"]
    n = max(1, min(7, (w - 3 - x0) // 3))
    span = max(2, hor - L["sky_top"])
    hgts = [2 + int(h01(i, 61) * max(2, span * 0.5)) for i in range(n)]
    return base, x0, n, hgts


def _v1_city(cv, L, t, t0, blocked):
    """The new world gets a skyline; its windows light in a wave."""
    g = _v1_city_geom(L)
    if g is None:
        return
    base, x0, n, hgts = g
    for i in range(n):
        bx = x0 + i * 3
        hgt = hgts[i]
        gr = ramp(t - t0, i * 0.06, i * 0.06 + 0.55)
        if gr <= 0.0:
            continue
        grow = int(round(hgt * gr))
        col = shade(P["blue"], 0.45 + 0.3 * h01(i, 62))
        for j in range(grow):
            y = base - j
            if y < L["sky_top"]:
                break
            for q in (0, 1):
                if not blocked(bx + q, y):
                    cv.put(bx + q, y, "█", col)
        if gr >= 1.0 and base - hgt >= L["sky_top"] and not blocked(bx + 1, base - hgt):
            cv.put(bx + 1, base - hgt, "▄", col)
        for j in range(1, max(2, hgt - 1)):
            y = base - j
            if y < L["sky_top"]:
                break
            for q in (0, 1):
                if blocked(bx + q, y):
                    continue
                tw = t0 + 0.5 + i * 0.12 + j * 0.08 + q * 0.05
                lk = ramp(t, tw, tw + 0.22)
                if lk <= 0.0:
                    cv.put(bx + q, y, "▓", shade(col, 0.6))
                elif lk < 0.5:
                    cv.put(bx + q, y, "▣", mix(P["amber"], P["white"],
                                                0.5 * (1.0 - lk * 2.0)))
                else:
                    fl = (t * (0.45 + 0.4 * h01(i, j, 63)) + h01(i, j, 64)) % 1.0
                    cv.put(bx + q, y, "▪" if fl < 0.75 else "▫",
                           shade(P["amber"], 0.45 + 0.35 * (fl < 0.75)))


def _v1_city_hud(cv, L, t, t0):
    """The skyline's ledger: windows counted as they come on."""
    g = _v1_city_geom(L)
    if g is None:
        return
    base, x0, n, hgts = g
    hor = base + 1
    if hor > L["y1"] or t < t0 + 0.5:
        return
    lit = total = 0
    for i in range(n):
        for j in range(1, max(2, hgts[i] - 1)):
            for q in (0, 1):
                total += 1
                if t >= t0 + 0.5 + i * 0.12 + j * 0.08 + q * 0.05 + 0.22:
                    lit += 1
    k = ramp(t, t0 + 0.5, t0 + 1.4)
    lab = "windows %3d/%3d" % (lit, total)
    if k >= 1.0 and lit >= total:
        lab += " ✓"
    cv.rtext(hor, lab, shade(P["amber"], 0.85 * max(0.3, k)),
             right=L["w"] - 2)


def _v1_pylons(cv, L, t, t_world, blocked):
    """The mains reach the new city: pylons, sagging catenary, live current."""
    if L["sky_x"] <= 0:
        return
    w = cv.w
    base = min(L["horizon"], L["y1"] + 1) - 1
    x_lo = 2 + 3 * min(6, max(0, (L["rx"] - 3) // 3)) + 2
    x_hi = L["rx"] - 3
    if x_hi - x_lo < 10:
        return
    top = max(L["sky_top"] + 1, base - 6)
    kp = ramp(t, t_world + 0.8, t_world + 1.5)
    if kp <= 0.0:
        return
    band = x_hi - x_lo
    nt = 3 if band >= 26 else 2
    xs = [x_lo + 2 + j * (band - 5) // max(1, nt - 1) for j in range(nt)]
    for j, xt in enumerate(xs):
        gr = ramp(t, t_world + 0.8 + j * 0.25, t_world + 1.5 + j * 0.25)
        if gr <= 0.0:
            continue
        grow = int(round((base - top) * gr))
        for y in range(base - grow + 1, base + 1):
            if blocked(xt, y):
                continue
            arm = (y - top) % 2 == 0 and y < base
            cv.put(xt, y, "╫" if arm else "║", shade(P["grey"], 0.75))
            if arm:
                for dx in (-1, 1):
                    if 1 <= xt + dx < w - 1 and not blocked(xt + dx, y):
                        cv.put(xt + dx, y, "─", shade(P["grey"], 0.45))
        if not blocked(xt, base - grow) and base - grow >= top:
            cv.put(xt, base - grow, "╥", shade(P["grey"], 0.9))
        # the feed: a dotted riser up to the mains line itself
        if gr >= 1.0:
            for y in range(L["cab_y"] + 1, top, 2):
                if not blocked(xt, y):
                    cv.put(xt, y, "┊", shade(P["grey_dim"], 0.8))
    # the catenary: from tower to tower, sagging, marching cityward
    kw = ramp(t, t_world + 1.2, t_world + 1.9)
    if kw <= 0.0:
        return
    g = _v1_city_geom(L)
    segs = [(xs[j], xs[j + 1], top, top) for j in range(nt - 1)]
    if g is not None:
        cbase, cx0, _cn, chg = g
        segs.append((xs[-1], cx0 + 1, top,
                     max(L["sky_top"], cbase - chg[0])))
    sag = 2
    for (xa, xb, ya, yb) in segs:
        if xb <= xa:
            continue
        for q in range(int((xb - xa) * kw) + 1):
            u = q / float(xb - xa)
            x = xa + q
            yy = int(round(ya + (yb - ya) * u + sag * 4.0 * u * (1.0 - u)))
            if blocked(x, yy) or not (L["sky_top"] <= yy <= base):
                continue
            cv.put(x, yy, "·", shade(P["grey_dim"], 0.95))
    if kw < 1.0:
        return
    # current runs the whole line toward the city
    for (xa, xb, ya, yb) in segs:
        for i in range(3):
            u = (t * 0.30 + i / 3.0) % 1.0
            x = int(round(xa + (xb - xa) * u))
            yy = int(round(ya + (yb - ya) * u + sag * 4.0 * u * (1.0 - u)))
            if blocked(x, yy) or not (L["sky_top"] <= yy <= base):
                continue
            cv.put(x, yy, "●", mix(P["amber"], P["white"], 0.4))
    # and the city tap: power drops from the mains down to the rooftops
    if g is not None:
        cbase, cx0, _cn, chg = g
        tap_x = cx0 - 2
        roof = max(L["sky_top"], cbase - chg[0])
        if 1 <= tap_x < w - 1:
            for y in range(L["cab_y"] + 1, roof + 1):
                if not blocked(tap_x, y):
                    cv.put(tap_x, y, "┊", shade(P["grey_dim"], 0.8))
            u = (t * 0.5) % 1.0
            dy = int(round(L["cab_y"] + 1 + (roof - L["cab_y"] - 1) * u))
            if not blocked(tap_x, dy):
                cv.put(tap_x, dy, "●", mix(P["amber"], P["white"], 0.4))
            if u < 0.12 and not blocked(tap_x + 1, roof):
                cv.put(tap_x + 1, roof, "✶", P["white"])



def _v1_chess(cv, L, t, t0, fg):
    """The pieces slide in from the wing to their squares -- and while the
    world is being wired, the rook takes the knight: the first capture."""
    n = min(6, max(0, (L["rx"] - 3) // 3))
    if n <= 0 or L["horizon"] > L["y1"] or L["horizon"] - 1 < L["sky_top"]:
        return
    w = cv.w
    base = L["horizon"] - 1

    def xof(i):
        return 2 + i * 3

    # the files, burnt dim into the floor under each square
    if base + 1 <= L["y1"]:
        for i in range(n):
            cv.put(xof(i), base + 1, chr(ord("a") + i),
                   shade(P["phos_dk"], 0.85))
    cap = (t0 + 3.0, 3, 1) if n >= 4 else None      # at, mover, victim
    for i in range(n):
        drop = t0 + i * 0.22
        if t < drop:
            continue
        k = ramp(t, drop, drop + 0.34)
        x = int(round(-4 + (xof(i) + 4) * fx.ease_out(k)))
        sliding = False
        if cap is not None and i == cap[1]:
            at, mv, vic = cap
            if t >= at + 0.5:
                x = xof(vic)                 # it has taken the square
            elif t > at:
                sliding = True
                kk = ramp(t, at, at + 0.5)
                x = int(round(xof(i) + (xof(vic) - xof(i)) * kk))
        elif cap is not None and i == cap[2] and t >= cap[0] + 0.5:
            continue                          # the taken piece is gone
        if k >= 1.0 and not sliding:
            x += int(round(math.sin(t * 4.2 + i * 1.9) * 0.9))
        if not (1 <= x < w - 1):
            continue
        if base + 1 <= L["y1"]:
            cv.put(x, base + 1, "▁", shade(P["phos_dk"], 0.9))
        cv.put(x, base, art.CHESS[i], mix(P["white"], P["soft"], 0.3))
        fl = ramp(t, drop + 0.2, drop + 0.5)
        if 0.0 < fl < 1.0:
            cv.put(x - 2, base, "▸", shade(P["ice"], 1.0 - fl))
            cv.put(x + 2, base, "◂", shade(P["ice"], 1.0 - fl))
    if cap is None:
        return
    at, mv, vic = cap
    # the kill flash, then the ghost cross where the knight stood
    if at + 0.42 <= t < at + 1.0:
        if int(t * 18) % 2 == 0:
            cv.put(xof(vic), base, "✷", P["white"])
        else:
            cv.put(xof(vic), base, art.CHESS[vic], shade(P["red"], 0.85))
    elif at + 0.5 <= t < at + 1.15:
        cv.put(xof(vic), base, "×", shade(P["red"], 0.55))
    # the scorer's line, typed right above the board
    ry = base - 2
    if at - 0.15 <= t < at + 2.3 and ry >= L["sky_top"]:
        move = "%s %s1×%s1" % (art.CHESS[mv], chr(ord("a") + mv),
                                     chr(ord("a") + vic))
        shown, typing = fx.typewriter(move, t - (at - 0.15), 14.0)
        cx = xof(vic) + 2
        if cx + sw(shown) + 2 > w - 1:
            cx = max(1, xof(vic) - 2 - sw(shown))
        cv.text(cx, ry, shown, shade(P["ice"], 0.95))
        if not typing and t > at + 0.6:
            cv.put(min(w - 2, cx + sw(shown) + 1), ry, "✓", P["phos"])


def _v1_scaffold(cv, L, t, t_pow, t_obj, fg):
    """The object's box is measured out before there is an object."""
    if L["tier"] == "small":
        return
    a = ramp(t, t_pow + 0.5, t_pow + 1.1) * (1.0 - ramp(t, t_obj + 0.7,
                                                       t_obj + 1.6))
    if a <= 0.03:
        return
    x0 = max(1, L["rx"] - 2)
    x1 = min(cv.w - 2, L["rx"] + L["mw"] + 1)
    y0 = max(L["sky_top"], L["top"] - 1)
    y1 = min(L["horizon"] - 1, L["top"] + L["mh"])
    if x1 <= x0 + 2 or y1 <= y0 + 1:
        return
    off = int(t * 8)
    col = shade(fg, 0.4 * a)
    for x in range(x0, x1 + 1):
        if (x + off) % 4 < 2:
            cv.put(x, y0, "·", col)
        if (x - off) % 4 < 2:
            cv.put(x, y1, "·", col)
    for y in range(y0 + 1, y1):
        if (y + off) % 4 < 2:
            cv.put(x0, y, "·", col)
            cv.put(x1, y, "·", col)
    for (cx_, cy_, ch) in ((x0, y0, "┌"), (x1, y0, "┐"),
                           (x0, y1, "└"), (x1, y1, "┘")):
        cv.put(cx_, cy_, ch, shade(fg, 0.7 * a))
    cv.text(x0 + 3, y1, " w=%d h=%d " % (L["mw"], L["mh"]),
            shade(P["violet"], a))


def _v1_robot(cv, L, t, t_obj, fg, bg_obj, pulse):
    """Pulled together out of scattered cells, then it stays alive."""
    w = cv.w
    rx, top, mw, mh = L["rx"], L["top"], L["mw"], L["mh"]
    tier = L["tier"]
    if tier == "small":
        rows = L["rows"]
        eyes = ()
        pi = 0
        ka = ramp(t, t_obj, t_obj + 1.1)
    else:
        poses = _V1_BIG if tier == "big" else _V1_MID
        eyemap = _V1_EYES_BIG if tier == "big" else _V1_EYES_MID
        pi = int(t / (2 * _V1_BEAT)) % len(poses)
        rows = poses[pi]
        eyes = eyemap[pi]
        ka = ramp(t, t_obj, t_obj + 1.5)
    if ka <= 0.0:
        return
    y = top
    if ka >= 0.45:
        cv.fill(rx - 1, top, mw + 2, mh, " ", None, bg_obj)
    if ka < 1.0:
        anim.assemble(_V1Clip(cv, L["sky_top"], L["y1"]), rx, y, rows, ka, fg,
                      seed=9, spread=max(5, mw // 3), snap=0.5,
                      y_min=L["sky_top"])
        return
    sway = 0
    breathe = math.sin(2 * math.pi * t / (2 * _V1_BEAT))
    if breathe > 0.55:
        sway = 1
    elif breathe < -0.55:
        sway = -1
    ox = rx + sway
    cv.blit(rows, ox, y, fg, bg_obj)
    # eyes: they blink, and they follow whatever is being built
    blink = (t % 3.7) < 0.13
    look = 1 if pi % 3 == 0 else 0
    for (j, ex) in eyes:
        if j >= len(rows):
            continue
        cv.put(ox + ex + look, y + j, "─" if blink else "◉",
               mix(fg, P["white"], 0.35 + 0.45 * pulse), bg_obj)
    # a tiny ECG on the chest band (it must never climb into the face)
    chest = None
    for j, line in enumerate(rows):
        p = line.find("██████")
        if p >= 0:
            chest = (j, p)
            break
    if chest is not None and len(rows) > chest[0] + 1:
        j, p = chest
        for q in range(6):
            v = fx.ecg((q / 6.0) - t * 0.55)
            yy = y + j + 1 if v > 0.45 else y + j
            ch = "█" if v > 0.7 else ("▄" if v > 0.2 else
                                      ("▀" if v < -0.15 else "▪"))
            cv.put(ox + p + q, yy, ch,
                   mix(fg, P["ice"], 0.30 + 0.55 * abs(v)), bg_obj)
    # scan line sweeping down the body, and a rare torn row
    sy = y - 1 + int((((t - t_obj) / 1.9) % 1.0) * (mh + 1))
    if mh >= 5 and L["sky_top"] <= sy <= L["horizon"] - 1:
        for x in range(max(1, rx - 1), min(w - 1, rx + mw + 1)):
            cv.put(x, sy, "▔", mix(fg, P["white"], 0.5), bg_obj)
    # it sheds light onto the floor while the field is being written
    if mh >= 7:
        cy_ = y + mh // 2
        rad = max(2, min(4, mh // 2))
        fx.sparkle(cv, ox + mw // 2, cy_, t, mix(fg, P["white"], 0.4),
                   seed=4, n=8, rad=rad)
        kb = ramp(t, t_obj + 1.5, t_obj + 2.1)
        if 0.0 < kb < 1.0:
            fx.ripple(cv, ox + mw // 2, cy_, (t - t_obj) - 1.5,
                      mix(fg, P["white"], 0.5), n=2, speed=10.0, period=0.6)


def _v1_cable(cv, L, t, t_pow, t_prot, dim, hot):
    """Bare cable draws itself, a charge runs it, then it is insulated."""
    w = cv.w
    y = L["cab_y"]
    k = ramp(t, t_pow, t_pow + 1.3)
    if k <= 0.0:
        return
    end = max(3, int((w - 4) * k) + 1)
    ins = ramp(t, t_prot - 0.2, t_prot + 0.7)
    flow = int(t * 10) % 8
    amber = shade(P["amber"], 0.85)
    cyan = shade(P["cyan"], 0.85)

    def bare(c2):
        for x in range(1, end):
            c2.put(x, y, "═" if (x + flow) % 8 < 5 else "─", amber)
        for x in range(2, end, 7):
            c2.put(x, y, "╪", shade(P["amber"], 0.45))

    def insulated(c2):
        for x in range(1, end):
            c2.put(x, y, "╪" if (x + flow) % 8 < 5 else "╫", cyan)

    if 0.0 < ins < 1.0:
        anim.dissolve(cv, t, t_prot - 0.2, t_prot + 0.7, bare, insulated,
                      seed=5, band=0.12)
    elif ins >= 1.0:
        insulated(cv)
    else:
        bare(cv)
    # two charges running the line at different speeds, field glyphs around
    if end > 12:
        for p, (spd, col, glyph) in enumerate(((t * 25.0, P["white"], "◉"),
                                               (t * 9.0 + 37.0, P["amber"], "●"))):
            px = 1 + int(spd % max(1, end - 1))
            cv.put(px, y, glyph, col)
            cv.put(px - 1, y, "[" if p == 0 else "(", shade(col, 0.45))
            cv.put(px + 1, y, "]" if p == 0 else ")", shade(col, 0.45))
            if L["two"] and y + 1 <= L["y1"] and not (
                    L["rx"] - 1 <= px <= L["rx"] + L["mw"]):
                cv.put(px, y + 1, "⌁" if int(t * 12 + p) % 2 else "∿",
                       shade(col, 0.55))


def _v1_label_row(cv, L, t, t_pow, t_prot):
    """The line's instrument strip (only where a content row can be spared)."""
    if not L["two"]:
        return
    y = L["lab_y"]
    w = cv.w
    a = ramp(t, t_pow - 0.05, t_pow + 0.45)
    if a <= 0.02:
        return
    cv.fill(1, y, max(1, w - 2), 1, " ", None, mix(P["black"], P["phos"], 0.04))
    cv.text(1, y, "AC 220V", shade(P["amber"], 0.9 * a))
    lv = 2 + int(round(2 * abs(math.sin(t * 2.1))))
    for i in range(5):
        on = i < lv
        cv.put(9 + i, y, "▮" if on else "▯",
               shade(P["amber"] if on else P["grey_dk"], 0.85 * a))
    cv.text(15, y, "50Hz", shade(P["amber"], 0.45 * a))
    if t < t_prot:
        lab, lc = "BARE LINE", shade(P["amber"], 0.55 * a)
        st, sc = "!", P["red"]
    else:
        lab, lc = "INSULATED", shade(P["cyan"], 0.8 * a)
        st, sc = "✓", P["cyan"]
    cv.text(21, y, lab, lc)
    cur = 1.2 + 0.4 * math.sin(t * 3.1) + 0.15 * math.sin(t * 11.0)
    cv.rtext(y, "I %4.2fA %s" % (cur, st), shade(sc, 0.85 * a), right=w - 2)


def _v1_panel(cv, L, t, t_data, t_world):
    """Initialisation: rows type, values are computed, then it locks."""
    px, py, pw, ph = L["panel"]
    a = ramp(t, t_data - 0.25, t_data + 0.1) * (
        1.0 - ramp(t, t_world, t_world + 0.7))
    if a <= 0.03:
        return
    k = 0.25 + 0.75 * a
    bgp = mix(P["black"], P["phos"], 0.05 + 0.02 * a)
    rows = ph - 2
    x = px + 2
    inner = pw - 4
    fx.panel(cv, px, py, pw, ph, shade(P["phos_dim"], k), bgp,
             title="initialisation", title_fg=shade(P["white"], 0.85 * a))

    def put_row(i, s, col):
        if i >= rows:
            return
        cv.text(x, py + 1 + i, s[:inner], shade(col, k), bgp)

    def typed_row(i, s, t_start, col):
        if i >= rows:
            return False
        shown, typing = fx.typewriter(s, t - t_start, 46.0)
        put_row(i, shown, col)
        if typing and int(t * 14) % 2 == 0:
            cx = x + sw(shown)
            if cx < px + pw - 1:
                cv.put(cx, py + 1 + i, "▮", shade(col, k), bgp)
        return not typing

    typed_row(0, 'name   : "me"', t_data + 0.05, P["soft"])
    typed_row(1, "type   : lover_object", t_data + 0.45, P["soft"])
    if typed_row(2, "target : ", t_data + 0.95, P["soft"]):
        kr = ramp(t, t_data + 1.7, t_data + 2.9)
        if kr < 1.0:
            put_row(2, "target : 0x%04X" % int(h01(int(t * 13), 7) * 65535),
                    P["violet"])
        else:
            put_row(2, 'target : "you" ✓', P["pink"])
    lv = ramp(t, t_data + 2.1, t_data + 3.8)
    put_row(3, "love   : %4.2f" % lv, P["rose"])
    bw = min(7, inner - 16)
    if bw >= 3 and rows >= 4:
        gx = px + pw - 2 - bw
        for q in range(bw):
            on = q < int(round(bw * lv))
            cv.put(gx + q, py + 4, "█" if on else "·",
                   shade(P["rose"] if on else P["phos_dk"], k), bgp)
    lk = ramp(t, t_data + 3.3, t_data + 4.7)
    if lk >= 1.0:
        put_row(4, "// immutable LOCKED", P["amber"])
    else:
        put_row(4, "// immutable", P["grey_dim"])
        cells = min(8, inner - 15)
        if cells >= 3 and rows >= 5:
            gx = px + pw - 2 - cells
            for q in range(cells):
                on = q < int(round(cells * lk))
                cv.put(gx + q, py + 5, "█" if on else "·",
                       shade(P["amber"] if on else P["phos_dk"], k), bgp)
    put_row(5, "addr   : 0x%04X" % (int(t * 220) % 0x10000), P["phos"])
    put_row(6, "beat   : %3d bpm" % (130 + int(6 * math.sin(t * 3.1))),
            P["phos_dim"])


def _v1_compact(cv, L, t, times):
    """On tubes too small for a panel the same values are squeezed in."""
    x, y, wd = L["compact"]
    t_pow, t_prot, t_chess, t_obj, t_data, t_world, t_sim = times
    if y < 4 or wd < 10:
        return
    n = max(1, min(3, L["horizon"] - y - 1))
    build = ramp(t, t_pow, t_obj + 1.5)
    lv = ramp(t, t_data + 1.0, t_data + 3.4)
    lines = [("build %3d%%" % int(100 * build), P["phos"]),
             ("love  %4.2f" % lv, P["rose"]),
             ("you   %s" % ("----" if t < t_sim else "hi !"), P["pink"])]
    for i in range(n):
        s, c = lines[i]
        cv.text(x, y + i, s[:wd], shade(c, 0.85))


def _v1_ledger(cv, L, t, times):
    """One line of instruments: every step of the build is accounted for."""
    if not L["two"] or L["w"] < 90:
        return
    x, y = 30, L["lab_y"]
    cellw = 8
    avail = L["w"] - 14 - x
    n = min(len(_V1_STEPS), max(1, avail // cellw))
    active = 0
    for i in range(n):
        if t >= times[i]:
            active = i
    for i in range(n):
        x0 = x + i * cellw
        done = t >= times[i]
        cur = i == active
        blink = cur and int(t * 5) % 2 == 0
        col = P["white"] if (cur and blink) else (
            P["phos"] if done else shade(P["phos"], 0.32))
        cv.put(x0, y, "▰" if done else "▱", col)
        cv.text(x0 + 2, y, _V1_STEPS[i], col)
        if i < n - 1:
            cv.put(x0 + 7, y, "·", shade(P["phos"], 0.3))


def _v1_you(cv, L, t, t_sim, blocked):
    """`"you"` arrives and orbits the object it was made for."""
    w = cv.w
    cx = L["rx"] + L["mw"] // 2
    cy = L["top"] + L["mh"] // 2
    rxo = L["orbit_rx"]
    ryo = max(2, min(4, L["mh"] // 4))
    ang = (t - t_sim) * 1.7 - math.pi * 0.5
    for i in range(1, 5):
        a2 = ang - i * 0.12
        tx = int(round(cx + rxo * math.cos(a2)))
        ty = int(round(cy + ryo * math.sin(a2)))
        if 1 <= tx < w - 1 and L["sky_top"] <= ty <= L["horizon"] - 1:
            cv.put(tx, ty, "·", shade(P["rose"], 0.75 - i * 0.13))
    px = int(round(cx + rxo * math.cos(ang)))
    py = int(round(cy + ryo * math.sin(ang)))
    if not (1 <= px < w - 1 and L["sky_top"] <= py <= L["horizon"] - 1):
        return
    cv.put(px, py, "◆", mix(P["rose"], P["white"], 0.55))
    lx, ly = px + 2, py - 1
    if lx + 5 >= w - 2:
        lx = px - 7
    if ly >= L["sky_top"] and 1 <= lx and lx + 5 < w - 1:
        cv.text(lx, ly, '"you"', shade(P["rose"], 0.85))


def _v1_widget(t, times):
    """The instrument for whatever stage is running right now."""
    t_pow, t_prot, t_chess, t_obj, t_data, t_world, t_sim = times
    if t < t_pow:
        return "V standby"
    if t < t_prot:
        return "V %5.1f" % (220.0 + 0.5 * math.sin(t * 3.7))
    if t < t_chess:
        return "R %4.2f GΩ" % (2.0 + 0.03 * math.sin(t * 2.9))
    if t < t_obj:
        return "pieces %d/6" % min(6, int((t - t_chess) / 0.22) + 1)
    if t < t_data:
        return "asm %3d%%" % int(100 * ramp(t, t_obj, t_obj + 1.5))
    if t < t_world:
        return "love %4.2f" % ramp(t, t_data + 2.1, t_data + 3.8)
    if t < t_sim:
        return "sky %3d%%" % int(100 * ramp(t, t_world - 0.1, t_world + 1.8))
    return "you ◆ ✓"


def _v1_hud(cv, L, t, t_sim, t0, bg, times):
    """The build's instruments: stage widget, write counter, ticker."""
    if L["D"] < 6:
        return
    y = L["y1"]
    if t < t_sim:
        s = "T+%06.2fs" % max(0.0, t - t0)
    else:
        s = "MEM 0x%02X/FF" % int(round(255 * min(1.0, (t - t_sim) / 1.7)))
    cv.fill(1, y, sw(s) + 2, 1, " ", None, bg)
    cv.text(2, y, s, shade(P["phos"], 0.95), bg)
    xend = cv.w - 2
    wid = _v1_widget(t, times)
    if wid and L["w"] >= 42:
        cv.rtext(y, wid, shade(P["phos"], 0.9), bg, right=xend)
        xend -= sw(wid) + 3
    msg = "world.execute(me); · "
    n = len(msg)
    off = int(t * 9.0) % n
    x0 = sw(s) + 5
    if x0 < xend - 2:
        tick = "".join(msg[(off + i) % n] for i in range(max(0, xend - x0)))
        cv.text(x0, y, tick, shade(P["phos_dk"], 1.0))
        # the "me)" inside the ticker blushes each time it crosses
        # mid-screen -- the whole scroll is dim, but never that word
        i_me = (14 - off) % n
        for i_m in (i_me, i_me + n):
            if i_m + 2 < len(tick):
                bx = x0 + i_m
                if abs(bx + 1 - cv.w * 0.5) < 5.0:
                    cv.text(bx, y, tick[i_m:i_m + 3],
                            shade(P["phos"], 1.0))


class Verse1Scene(Scene):
    key = "verse1"
    accent = "phos"

    def draw(self, cv, ctx):
        t = ctx.t
        pulse = 0.5 + 0.5 * math.sin(ctx.beat * math.pi * 2.0)
        t0 = self.t0
        t_pow = self.cue("Switch on the power line")
        t_prot = self.cue("Remember to put on protection")
        t_chess = self.cue("Lay down your pieces")
        t_obj = self.cue("And let's begin object creation")
        t_data = self.cue("Fill in my data parameters initialisation")
        t_world = self.cue("Setup our new world")
        t_sim = self.cue("And let's begin the simulation")
        times = (t_pow, t_prot, t_chess, t_obj, t_data, t_world, t_sim)
        L = _v1_layout(cv.w, cv.h)
        bg_obj = mix(P["black"], P["phos"], 0.05)
        fg = P["phos"]
        dim = shade(fg, 0.36)
        hot = mix(fg, P["white"], 0.25)
        rx, top, mw, mh = L["rx"], L["top"], L["mw"], L["mh"]

        def blocked(x, y):
            """The object and its panel are solid: sky must not shine through."""
            if L["panel"] is not None:
                px_, py_, pw_, ph_ = L["panel"]
                if px_ - 1 <= x <= px_ + pw_ and py_ - 1 <= y <= py_ + ph_:
                    return True
            if rx - 1 <= x <= rx + mw and top - 1 <= y <= top + mh:
                return True
            return False

        def world(c2):
            # 1 · sky: the world above the horizon
            _v1_trace(c2, L, t, ramp(t, t_pow + 0.05, t_pow + 0.75) * (
                1.0 - ramp(t, t_data - 0.1, t_data + 0.9)))
            _v1_dome(c2, L, t, ramp(t, t_world - 0.1, t_world + 1.8),
                     t_world, blocked)
            _v1_stars(c2, L, t, ramp(t, t_world - 0.25, t_world + 1.7), blocked)
            _v1_city(c2, L, t, t_world + 0.55, blocked)
            # 2 · the ground unrolls, then its tiles keep flipping
            _v1_floor(c2, L, t, ramp(t, t_pow - 0.05, t_pow + 3.4), dim, hot)
            # 2b · the mains reach the city: pylons, catenary, current
            _v1_pylons(c2, L, t, t_world, blocked)
            _v1_city_hud(c2, L, t, t_world + 0.55)
            # 3 · the power line: bare, charged, then insulated
            _v1_cable(c2, L, t, t_pow, t_prot, dim, hot)
            # 4 · the pieces arrive one by one and never sit still
            _v1_chess(c2, L, t, t_chess, fg)
            # 5 · the object: measured, assembled, alive
            _v1_scaffold(c2, L, t, t_pow, t_obj, fg)
            _v1_robot(c2, L, t, t_obj, fg, bg_obj, pulse)
            # 6 · instruments and the arrival of "you"
            _v1_label_row(c2, L, t, t_pow, t_prot)
            if L["panel"] is not None:
                _v1_panel(c2, L, t, t_data, t_world)
            elif L["compact"] is not None:
                _v1_compact(c2, L, t, times)
            _v1_ledger(c2, L, t, times)
            if t >= t_sim - 0.2:
                _v1_you(c2, L, t, t_sim, blocked)
            _v1_hud(c2, L, t, t_sim, t0, bg_obj, times)

        if t >= 29.02:
            anim.hand_off(cv, t, 29.02, 30.4, world, seed=9)
        else:
            world(cv)
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

        # ---------- the formula tape ---------------------------------
        # a running tape of every quantity this chapter has produced,
        # feeding across the top of the working area.  It runs *under*
        # whatever the current section draws there (panel, formula) --
        # draw it first, sections punch through it.
        tape = ("  |P| = 4096   dim P = 3   x\u2099 \u2192 x : \u2200\u03b5>0 "
                "\u2203N \u2200n\u2265N |x\u2099\u2212x|<\u03b5   C = 2\u03c0r   "
                "dy/dx = cos x   \u0177 = a\u00b7x+b   \u03c3 = \u221a(\u03a3(y\u2212\u0177)\u00b2/n)"
                "   lim 1/n = 0   ")
        anim.ticker(cv, 4, tape, t - t_pts, 11.0,
                    shade(P["cyan"], 0.34), None, 2, w - 3)

        # ================= 1 · a set of points ----------------------
        # "If I'm a set of points / Then I will give you my dimension"
        #   A point set on its own is 0-dimensional: no axes, no distance,
        #   nothing to measure.  Dimension appears only when *you* stand at
        #   the origin and draw the axes -- then ONE number is enough to
        #   name a point (a line), TWO numbers (a plane), THREE (the space).
        #   So the same cloud is shown *being given* 0,1,2,3 numbers, and
        #   the instrument on the left shows what each dimension measures:
        #   a point (0), a length (1), an area (2), a volume (3).
        a = fade_window(t, t_pts - 0.30, t_circ - 0.02, 0.45, 0.40)
        if a > 0.01:
            def ac(c, k=1.0):
                return shade(c, a * k)
            big = h >= 16 and w >= 78
            # the three numbers arrive in the *live* part of the line: the
            # volume used to start forming inside the section's fade-out and
            # so was never seen complete.  0 -> 1 -> 2 -> 3 now finishes a
            # full half-second before the picture lets go.
            k1 = ramp(t, t_dim - 0.06, t_dim + 0.42)     # 0 -> 1: a line
            k2 = ramp(t, t_dim + 0.48, t_dim + 0.88)     # 1 -> 2: a plane
            k3 = ramp(t, t_dim + 0.94, t_dim + 1.34)     # 2 -> 3: a volume
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
            # the far face sits up and to the right of the near face, so the
            # near face has to leave that much room inside the pane -- it was
            # previously drawn hard against the right edge and the depth had
            # nowhere to go but off-panel
            dzx = max(7, min(14, (gx1 - xr0) // 6))
            dzy = max(2, min(5, dzx // 3))
            xr1 = max(xr0 + 10, xr1 - dzx)
            yr0 = max(gy0 + 2 + dzy, min(yr1 - 3, yr0))
            nrow = max(1, min(nrow, (yr1 - yr0) // 2 + 1))
            def lat_x(ci):
                return int(round(xr0 + (xr1 - xr0) * ci / float(max(1, ncol - 1))))

            def lat_y(ri):
                return int(round(yr1 - (yr1 - yr0) * ri / float(max(1, nrow - 1))))
            if k2 > 0.04:
                gc = ac(P["cyan"], 0.11 * k2)
                for ri in range(nrow):
                    yy = lat_y(ri)
                    for xx in range(xr0, xr1 + 1):
                        cv.put(xx, yy, "·", gc)
                for ci in range(ncol):
                    xx = lat_x(ci)
                    for yy in range(yr0, yr1 + 1):
                        cv.put(xx, yy, "·", gc)
            # (the k3 wireframe is drawn AFTER the point cloud, below, so the
            #  frame can never be buried by the bullets -- the volume reads)

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
                fx.line(cv, ox, max(4, oy - 1), ox, ytop, ac(P["soft"], 0.55), "│")
                cv.put(ox, ytop, "▲", ac(P["soft"], 0.9))
                cv.text(ox + 1, ytop, "y", ac(P["soft"], 0.95))
            if k3 > 0.02:
                zax = max(2, dzx)
                zay = max(1, dzy)
                for u in range(1, 4):
                    cv.put(min(gx1, ox + zax * u // 2),
                           max(gy0 + 1, oy - zay * u // 2),
                           "╱", ac(P["violet"], 0.7 * k3))
                cv.text(min(w - 4, ox + zax * 4 // 2 + 1),
                        max(gy0 + 1, oy - zay * 4 // 2 - 1),
                        "z", ac(P["violet"], 0.95))
            cv.put(ox, oy, "+", ac(P["white"], 0.95))

            # ---- you arrive at the origin -------------------------------
            if t >= t_dim - 0.42:
                ky = ramp(t, t_dim - 0.42, t_dim + 0.36)
                if ky >= 1.0:
                    # while the volume is up, "you" steps back from the
                    # spotlight so the wireframe can carry the depth
                    ka = 1.0 - 0.42 * k3
                    cv.put(ox, oy, "◆", ac(P["pink"], ka))
                    if oy + 1 <= h - 5:
                        cv.text(ox + 2, oy + 1, "you = origin",
                                ac(P["pink"], 0.85 - 0.30 * k3))
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
                nx = lat_x(ci)
                ny = lat_y(ri)
                sx, sy = nx, ny
                lx = ox + 3 + int((i / max(1.0, nn - 1.0)) * max(1, gx1 - ox - 6))
                qx = lx + (nx - lx) * k2 + (sx - nx) * k3
                qy = oy + (ny - oy) * k2 + (sy - ny) * k3
                x = int(round(bx + (qx - bx) * k1))
                y = int(round(by + (qy - by) * k1))
                if k1 < 0.02:
                    # waiting to be measured: the cloud trembles
                    x = max(gx0, min(gx1 - 1, x + int(math.sin(t * 0.9 + i * 1.7)
                                                       * 0.55)))
                    y = max(gy0, min(gy1 - 1, y + int(math.sin(t * 1.1 + i * 2.3)
                                                     * 0.45)))
                pts.append((x, y, i))
            # the fill recedes: front bullets cooled + dimmed so the frame
            # (drawn after, on top) is the brightest thing in the box
            cur = mix(mix(P["ice"], P["cyan"], k1), P["phos"], k3 * 0.30)
            for (x, y, i) in pts:
                if k3 > 0.02 and h01(i, 15) >= 0.72:
                    cv.put(x, y, "\u2218", ac(mix(P["violet"], P["ice"], 0.3), 0.55))
                else:
                    cv.put(x, y, "\u2022", ac(cur, 0.66))

            # ---- the wireframe, on top of the cloud: the volume reads ----
            # A solid, not a wire cage: only the three faces turned toward
            # the eye are drawn.  The near face was the plane the points
            # already lie on; as k3 rises the box *extrudes* up and to the
            # right out of it, so the plane itself becomes one face of the
            # solid.  Hidden edges are simply not drawn -- that is what
            # makes it read as a solid and not as two stacked rectangles.
            if k3 > 0.04 and nrow >= 2:
                ex = max(2, int(round(dzx * k3)))
                ey = max(1, int(round(dzy * k3)))
                ftl = (xr0 + ex, yr0 - ey)
                ftr = (xr1 + ex, yr0 - ey)
                fbr = (xr1 + ex, yr1 - ey)

                def _face(o_, a_, b_, col_, nu_, nv_, skip_u, skip_v):
                    """fill a parallelogram with dots, in perspective"""
                    for iu in range(skip_u, nu_ + 1):
                        for iv in range(skip_v, nv_ + 1):
                            u = iu / float(max(1, nu_))
                            v = iv / float(max(1, nv_))
                            xx_ = int(round(o_[0] + a_[0] * u + b_[0] * v))
                            yy_ = int(round(o_[1] + a_[1] * u + b_[1] * v))
                            if gy0 <= yy_ <= gy1 - 1 and gx0 <= xx_ <= gx1 - 1:
                                cv.put(xx_, yy_, "\u00b7", col_)

                # surfaces first (they are under the frame): the top face is
                # lit, the right face turned away from the light is dimmest
                gt = ac(mix(P["ice"], P["violet"], 0.38), 0.62 * k3)
                gr = ac(P["violet"], 0.44 * k3)
                _face((xr0, yr0), (xr1 - xr0, 0), (ex, -ey), gt,
                      max(3, (xr1 - xr0) // 2), max(1, ey), 0, 1)
                _face((xr1, yr1), (0, yr0 - yr1), (ex, -ey), gr,
                      max(2, ex // 2), max(2, (yr1 - yr0) // 2), 1, 0)

                # the silhouette's back edges, then the two visible depth
                # edges: they converge on the vanishing point up and right
                gv = ac(P["violet"], 0.66 * k3)
                for xx in range(ftl[0], ftr[0] + 1):
                    cv.put(min(gx1, xx), max(gy0, ftr[1]), "\u2500", gv)
                for yy in range(ftr[1], fbr[1] + 1):
                    cv.put(min(gx1 - 1, fbr[0]), max(gy0, yy), "\u2502", gv)
                for (nx_, ny_), (fx_, fy_) in (((xr0, yr0), ftl), ((xr1, yr1), fbr)):
                    dx_, dy_ = fx_ - nx_, fy_ - ny_
                    steps = max(1, max(abs(dx_), abs(dy_)))
                    ch_ = "\u2571" if dx_ >= 0 else "\u2572"
                    for st in range(1, steps + 1):
                        ux = nx_ + dx_ * st / float(steps)
                        uy = ny_ + dy_ * st / float(steps)
                        ge = ac(P["violet"], (0.95 - 0.35 * st / float(steps)) * k3)
                        cv.put(int(round(ux)), int(round(uy)), ch_, ge)

                # the near face is the plane: the brightest frame, drawn last
                gf = ac(P["ice"], 0.62 * k3)
                for xx in range(xr0, xr1 + 1):
                    cv.put(xx, yr1, "\u2500", gf)
                    cv.put(xx, yr0, "\u2500", gf)
                for yy in range(yr0, yr1 + 1):
                    cv.put(xr0, yy, "\u2502", gf)
                    cv.put(xr1, yy, "\u2502", gf)
                for (ccx, ccy, ch_) in ((xr0, yr0, "\u250c"), (xr1, yr0, "\u2510"),
                                        (xr0, yr1, "\u2514"), (xr1, yr1, "\u2518")):
                    cv.put(ccx, ccy, ch_, ac(P["ice"], 0.9 * k3))

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

            # ---- the fit: least squares over the plane -----------------
            # before the cloud folds into 3-space, the plane gets its
            # regression: one line standing in for every point, each
            # point's miss ticked off against it, the spread reported.
            # it retires BEFORE the volume starts forming (least squares
            # is a plane's idea; in 3-space it has nothing to say) -- the
            # red ticks must not slice the box while it tries to read as 3D
            a_reg = ramp(t, t_dim + 0.28, t_dim + 0.46) * (
                1.0 - ramp(t, t_dim + 0.82, t_dim + 0.96))
            if a_reg > 0.02 and nrow >= 2 and len(pts) >= 8:
                xs_ = [p[0] for p in pts]
                ys_ = [p[1] for p in pts]
                mx_ = sum(xs_) / len(xs_)
                my_ = sum(ys_) / len(ys_)
                sxx = sum((v - mx_) ** 2 for v in xs_)
                sxy = sum((xs_[i] - mx_) * (ys_[i] - my_)
                          for i in range(len(xs_)))
                a_ = (sxy / sxx) if sxx > 0 else 0.0
                b_ = my_ - a_ * mx_
                # the fit searches: small refits flash past, then settle
                settle = ramp(t, t_dim + 0.60, t_dim + 0.82)
                jit = (h01(int(t * 30.0), 51) - 0.5) * 1.7 * (1.0 - settle)
                for xx in range(xr0, xr1 + 1):
                    yy = int(round(a_ * xx + b_ + jit))
                    if yr0 <= yy <= yr1:
                        cv.put(xx, yy, "━", ac(P["ice"], 0.9 * a_reg))
                res_ = []
                for (xx, yy_, _i) in pts:
                    yh = a_ * xx + b_ + jit
                    res_.append(yy_ - yh)
                    y0r = min(yy_, int(round(yh)))
                    y1r = max(yy_, int(round(yh)))
                    for ty in range(y0r, y1r + 1):
                        if yr0 <= ty <= yr1 and ty != yy_:
                            cv.put(xx, ty, "┆", ac(P["rose"], 0.45 * a_reg))
                sig = math.sqrt(sum(r * r for r in res_) / len(res_))
                if big and yr0 - gy0 >= 1:
                    sh_, _ = fx.typewriter(
                        "least squares  ŷ = %.2f·x%+.2f   σ = %.2f  n = %d"
                        % (a_, b_ + jit, sig, len(pts)),
                        t - (t_dim + 0.22), 60.0)
                    if sh_:
                        cv.fill(gx1 - sw(sh_) - 1, gy0, sw(sh_) + 2, 1,
                                " ", None, P["black"])
                        cv.rtext(gy0, sh_, ac(P["ice"], 0.95 * a_reg),
                                 right=gx1)

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
                for q in range(10):
                    on = q < int(round(10 * cnt / 4096.0))
                    cv.put(px_ + 14 + q, py_ + 5, "▮" if on else "▯",
                           ac(P["cyan"] if on else P["grey_dk"], 0.9), bgp)
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
                # the contract, typed under the instrument -- and rewound:
                # the machine cannot linger on one shape; the promise
                # backspaces itself just before the next form types its own
                cy_ = py_ + phl + 1
                rw = ramp(t, t_circ - 0.50, t_circ - 0.06)
                if cy_ <= h - 5:
                    s1, typ1 = fx.typewriter("if (me is a set of points)",
                                              t - (t_pts + 0.10), 34.0)
                    s1 = s1[:max(0, len(s1) - int(len(s1) * rw + 0.5))]
                    cv.text(px_, cy_, s1, ac(P["ice"], 0.85))
                    if s1 and (typ1 or 0.0 < rw < 1.0) and \
                            int(t * 5) % 2 == 0:
                        cv.put(px_ + sw(s1), cy_, "▮", ac(P["ice"], 0.55))
                if cy_ + 1 <= h - 5:
                    s2, typ2 = fx.typewriter("  return my.dimension;",
                                              t - (t_dim - 0.10), 30.0)
                    s2 = s2[:max(0, len(s2) - int(len(s2) * rw + 0.5))]
                    cv.text(px_, cy_ + 1, s2, ac(P["soft"], 0.8))
                    if s2 and (typ2 or 0.0 < rw < 1.0) and \
                            int(t * 5) % 2 == 0:
                        cv.put(px_ + sw(s2), cy_ + 1, "▮",
                               ac(P["soft"], 0.5))
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
        a = fade_window(t, t_circ - 0.38, t_sine + 0.15, 0.40, 0.5)
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
                ccy = min(h - 4, max(ccy, 5 + ry_))   # keep the top off row 3
                ccx = max(r + 6, int(w * 0.19))
            # ---- pi streams in while the cut unrolls -----------------
            # (drawn before the outline so the figure sits on top of it)
            ku_early = ramp(t, t_cf + 0.10, t_cf + 1.45)
            rx1_ = w - 4
            rrow_ = (ccy if w - 4 - (ccx + r + 5) >= 18
                     else min(h - 3, ccy + ry_ + 3))
            if rrow_ - 2 >= 4 and ku_early < 0.999:
                anim.ticker(cv, rrow_ - 2,
                            "  \u03c0 = 3.14159 26535 89793 23846 26433 "
                            "83279 50288 41971 69399 37510  ",
                            t, 15.0, ac2(P["violet"], 0.5), None, 2, rx1_)

            # ---- the outline draws itself ---------------------------
            tr = ramp(t, t_circ + 0.10, t_circ + 1.10)
            if tr < 0.999:
                fx.circle(cv, ccx, ccy, r, ac2(P["ice"], 0.20), "·",
                          a0=-math.pi / 2, a1=1.5 * math.pi, ry=ry_)
            fx.circle(cv, ccx, ccy, r, ac2(P["ice"], 0.95), "•",
                      a0=-math.pi / 2, a1=2 * math.pi * tr - math.pi / 2,
                      ry=ry_)
            ha = 2 * math.pi * tr - math.pi / 2
            hx = ccx + int(round(r * math.cos(ha)))
            hy = ccy + int(round(ry_ * math.sin(ha)))
            for q in range(1, 20):
                f = q / 20.0
                cv.put(ccx + int((hx - ccx) * f), ccy + int((hy - ccy) * f),
                       "·", ac2(P["cyan"], 0.5 * (0.35 + 0.65 * (1.0 - f))))
            cv.put(hx, hy, "◉", ac2(P["white"], 0.95))
            if tr < 0.999:
                cv.put(hx, max(4, hy - 1), "↻", ac2(P["amber"], 0.8))
                cv.text(max(1, ccx - r), min(h - 4, ccy + ry_ + 1),
                        "θ %03d°" % (int(tr * 360) % 360), ac2(P["cyan"], 0.75))
            cv.vline(ccx, ccy - ry_, ry_, "┊", ac2(P["cyan"], 0.45))
            cv.put(ccx, max(4, ccy - ry_ - 1 + int(round(math.sin(t * 2.6)))),
                   "✂", ac2(P["amber"], 0.9))
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
            # ---- the answer, typed -- then taken back ------------------
            # the circle's whole length gets handed over, and the hand
            # withdraws before the next shape can speak: the gift
            # backspaces itself, right to left, at the cut of the sine
            rwc = ramp(t, t_sine - 0.55, t_sine - 0.08)
            if rrow - 1 >= 4 and ku > 0.05:
                full_c = "C = 2πr = %.1f" % (2 * math.pi * r)
                sh, _ = fx.typewriter(full_c, t - (t_cf + 0.35), 20.0)
                if rwc > 0.0:
                    sh = sh[:max(0, len(sh) - int(len(sh) * rwc + 0.5))]
                    x_fc = rx1 - sw(full_c)
                    cv.text(x_fc, rrow - 1, sh, ac2(P["cyan"], 0.95))
                    if 0.0 < rwc < 1.0 and int(t * 5) % 2 == 0:
                        cv.put(x_fc + sw(sh), rrow - 1, "▮",
                               ac2(P["cyan"], 0.6))
                else:
                    cv.rtext(rrow - 1, sh, ac2(P["cyan"], 0.95), right=rx1)
            # ---- you walk along the circumference ----------------
            km = ramp(t, t_cf + 0.95, t_cf + 1.85)
            if km > 0:
                xm = rx0 + int((Lr - 1) * km)
                cv.put(xm, rrow, "◆", ac2(P["pink"], 0.95))
                if km > 0.5 and rrow + 2 < h - 3:
                    x_g = max(2, rx1 - 17)
                    g_c, _ = fx.typewriter("given to you: C",
                                            t - (t_cf + 1.45), 36.0)
                    g_c = g_c[:max(0, len(g_c) - int(len(g_c) * rwc + 0.5))]
                    if g_c:
                        cv.text(x_g, rrow + 2, g_c, ac2(P["pink"], 0.8))
                        if (len(g_c) < 16 or 0.0 < rwc) and \
                                int(t * 5) % 2 == 0:
                            cv.put(x_g + sw(g_c), rrow + 2, "▮",
                                   ac2(P["pink"], 0.55))
            # ---- the read-head re-measures the ruler, forever ------
            if ku >= 0.999:
                mxc = rx0 + int((Lr - 1) * ((t * 0.5) % 1.0))
                cv.put(mxc, rrow - 1, "▾", ac2(P["cyan"], 0.9))
                cv.put(mxc, rrow, "┼", P["white"])
                if w >= 56 and rrow - 2 >= 4:
                    meas = 2 * math.pi * r * ((t * 0.5) % 1.0)
                    cv.rtext(rrow - 2, "%5.1f / %.1f" % (meas, 2 * math.pi * r),
                             ac2(P["cyan"], 0.75), right=min(rx1, w - 4))
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
                if sy + 2 < h - 4 and t >= t_cf + 0.75:
                    s2, _ = fx.typewriter(
                        "   outline = 2πr = %.1f   → you" % (2 * math.pi * r),
                        t - (t_cf + 0.75), 34.0)
                    s2 = s2[:max(0, len(s2) - int(len(s2) * rwc + 0.5))]
                    if s2:
                        cv.text(rx0, sy + 2, s2, ac2(P["pink"], 0.85))
                        if (len(s2) < 31 or 0.0 < rwc) and \
                                int(t * 5) % 2 == 0:
                            cv.put(rx0 + sw(s2), sy + 2, "▮",
                                   ac2(P["pink"], 0.55))
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
        a = fade_window(t, t_sine - 0.3, t_inf + 0.30, 0.4, 0.42)
        if a > 0.01:
            def sine(cv2):
                amp = int(min(h * 0.16, 5))
                cy_ = max(4, min(max(6, int(h * 0.46)), h - 3 - amp))
                freq = 0.12
                phase = -t * 1.5
                cv2.hline(0, cy_, w, "─", shade(P["cyan"], 0.18))
                fx.filled_wave(cv2, cy_, amp, freq, phase,
                               shade(P["ice"], 1.0), shade(P["cyan"], 0.22))
                if amp >= 1 and cy_ - amp - 1 >= 4:
                    # crest markers ride the peaks as the wave rolls on
                    k0 = math.ceil((math.pi / 2 - phase) / (2 * math.pi * freq))
                    for kk in (k0 - 2, k0 - 1, k0, k0 + 1, k0 + 2):
                        xc = int(round((math.pi / 2 + 2 * math.pi * kk - phase)
                                       / freq))
                        if 0 <= xc < w:
                            cv2.put(xc, cy_ - amp - 1, "△",
                                    shade(P["cyan"], 0.75))
                # the trigger cursor sweeps across, sampling as it goes
                xs_col = int(((t - t_sine) * 17.0) % w)
                y0c, y1c = max(4, cy_ - amp - 1), min(h - 4, cy_ + amp + 1)
                if y1c > y0c:
                    cv2.vline(xs_col, y0c, y1c - y0c + 1, "┊",
                              shade(P["cyan"], 0.45))
                    ysc = cy_ + amp * math.sin(freq * xs_col + phase)
                    cv2.put(xs_col, int(round(ysc)), "◉", P["white"])
                    if w >= 56:
                        cv2.text(min(w - 16, xs_col + 1), y0c,
                                 "(%3d, %+.2f)" % (xs_col, math.sin(
                                     freq * xs_col + phase)),
                                 shade(P["cyan"], 0.7))
                if t >= t_tan - 0.2:
                    nb = int((t - t_tan) / 0.4615)
                    for b in range(max(0, nb - 3), nb + 1):
                        tb = t_tan + b * 0.4615
                        if tb > t:
                            continue
                        bx = int((0.12 + h01(b, 31) * 0.7) * w)
                        by = cy_ + int(round(amp * math.sin(freq * bx + phase)))
                        slope = amp * freq * math.cos(freq * bx + phase)
                        x0, x1 = bx - 7, bx + 7
                        y0 = by - int(round(slope * (x0 - bx)))
                        y1 = by - int(round(slope * (x1 - bx)))
                        age = 1.0 - (t - tb) / 2.4
                        c = shade(P["pink"], max(0.15, 0.85 * age))
                        fx.line(cv2, x0, max(4, y0), x1, max(4, y1), c)
                        cv2.put(bx, by, "◆", mix(P["pink"], P["white"], 0.3))
                        if by - 2 >= 4:
                            cv2.put(bx, by - 2, "◆", shade(P["pink"], 0.7))
                if t >= t_tan:
                    # you ride the wave itself; the tangent turns under you
                    u = ((t - t_tan) / 3.5) % 1.0
                    tri = 1.0 - abs(2.0 * u - 1.0)
                    xr_ = 4 + int((w - 8) * tri)
                    yr_ = cy_ + int(round(amp * math.sin(freq * xr_ + phase)))
                    sl_ = amp * freq * math.cos(freq * xr_ + phase)
                    x0_, x1_ = xr_ - 8, xr_ + 8
                    y0_ = max(4, yr_ - int(round(sl_ * (x0_ - xr_))))
                    y1_ = max(4, yr_ - int(round(sl_ * (x1_ - xr_))))
                    fx.line(cv2, x0_, y0_, x1_, y1_,
                            shade(P["pink"], 0.95), "━")
                    cv2.put(xr_, yr_, "◆", P["white"])
                    cv2.put(xr_, max(4, yr_ - 2), "◆", shade(P["pink"], 0.7))
                    if w >= 56:
                        ang_ = int(round(math.degrees(math.atan(sl_))))
                        cv2.text(min(w - 25, xr_ + 2),
                                 max(4, min(h - 5, yr_ - 3)),
                                 "dy/dx = %+.2f ∠ %3d°" % (sl_, ang_),
                                 shade(P["pink"], 0.9))
                cv2.ctext(h - 4, "y = sin x        dy/dx = cos x",
                          shade(P["cyan"], 0.85))
                # the tangents are handed over -- then taken back the same
                # way the circumference was: typed, held a moment, and
                # backspaced out before the infinity dares to draw itself
                rwt = ramp(t, t_inf - 0.50, t_inf - 0.08)
                if h >= 9 and rwt < 1.0:
                    g_t, _ = fx.typewriter("given to you: tangents",
                                           t - (t_tan + 0.30), 34.0)
                    g_t = g_t[:max(0, len(g_t) - int(len(g_t) * rwt + 0.5))]
                    if g_t:
                        xg = cx - 11
                        cv2.text(xg, h - 3, g_t, shade(P["pink"], 0.8))
                        if (len(g_t) < 22 or 0.0 < rwt) and \
                                int(t * 5) % 2 == 0:
                            cv2.put(xg + sw(g_t), h - 3, "▮",
                                    shade(P["pink"], 0.55))
            stamp(cv, sine, a)

        # ================= infinity & limitations ===================
        a = fade_window(t, t_inf - 0.15, t_lim + 2.1, 0.45, 0.8)
        holes = []
        if a > 0.01:
            def inf(cv2):
                # the sign is one thin continuous stroke: the curve is
                # sampled densely and every cell it crosses takes the
                # glyph that matches its local slope.  a light pulse runs
                # around the closed loop, so the sign loops by itself --
                # there is no stipple of dots and no dot orbiting it.
                if h >= 20:
                    axis_y = int(h * 0.60) + 1
                else:
                    axis_y = h - 3
                hh = max(1, min(5, (axis_y - 9) // 2))
                inf_cy = min(h - 4 - hh, 5 + hh)
                hw = min(int(round(hh / 0.354)), max(3, (w - 16) // 2))
                amp0 = max(2, min(7, axis_y - (inf_cy + hh) - 1))

                kk = ramp(t, t_inf, t_inf + 1.1)
                if kk > 0:
                    # the closed loop: right lobe, then left lobe mirrored
                    NP = 240
                    vfy = hh / 0.3540
                    path = []
                    for lobe in (0, 1):
                        for k in range(NP + 1):
                            th = (-math.pi / 4 + (math.pi / 2) * k / NP
                                  if lobe == 0 else
                                  math.pi / 4 - (math.pi / 2) * k / NP)
                            r_ = math.sqrt(max(0.0, math.cos(2.0 * th)))
                            xx = hw * r_ * math.cos(th)
                            if lobe:
                                xx = -xx
                            path.append((xx, vfy * r_ * math.sin(th)))
                    cells = {}
                    for i in range(len(path) - 1):
                        x0, y0 = path[i]
                        x1, y1 = path[i + 1]
                        dx, dy = x1 - x0, y1 - y0
                        if abs(dx) > 3.0 or abs(dy) > 3.0:
                            continue
                        pp = i / float(len(path) - 1)
                        m = max(1, int(max(abs(dx), abs(dy)) * 3))
                        for s_ in range(m):
                            xf = cx + x0 + dx * s_ / m
                            yf = inf_cy + y0 + dy * s_ / m
                            xi = (int(math.floor(xf + 0.5)) if xf >= 0
                                  else -int(math.floor(-xf + 0.5)))
                            yi = (int(math.floor(yf + 0.5)) if yf >= 0
                                  else -int(math.floor(-yf + 0.5)))
                            if yi < 4 or yi > h - 4:
                                continue
                            c = cells.get((xi, yi))
                            if c is None:
                                cells[(xi, yi)] = [dx, dy, pp, pp]
                            else:
                                c[0] += dx
                                c[1] += dy
                                c[2] = min(c[2], pp)
                                c[3] = max(c[3], pp)
                    glyphs = {}
                    for (xi, yi), (sx_, sy_, p0, p1) in cells.items():
                        if p0 > kk:
                            continue                    # not drawn in yet
                        ax_, ay_ = abs(sx_), abs(sy_)
                        if p1 - p0 > 0.4:
                            ch = "╳"                    # where the lobes cross
                        elif ax_ >= 2.2 * ay_:
                            ch = "─"
                        elif ay_ >= 2.2 * ax_:
                            ch = "│"
                        elif sx_ * sy_ > 0:
                            ch = "╲"
                        else:
                            ch = "╱"
                        glyphs[(xi, yi)] = [ch, p0]
                    # soften the joins: where a run of ─ turns into a
                    # diagonal, put a corner glyph there instead of a blunt
                    # junction -- it is what makes the stroke look drawn
                    for (xi, yi), g in list(glyphs.items()):
                        if g[0] != "─" or hh < 3:
                            continue
                        if ((xi + 1, yi) not in glyphs
                                and (xi + 1, yi + 1) in glyphs):
                            g[0] = "╮"
                        elif ((xi + 1, yi) not in glyphs
                              and (xi + 1, yi - 1) in glyphs):
                            g[0] = "╯"
                        elif ((xi - 1, yi) not in glyphs
                              and (xi - 1, yi + 1) in glyphs):
                            g[0] = "╭"
                        elif ((xi - 1, yi) not in glyphs
                              and (xi - 1, yi - 1) in glyphs):
                            g[0] = "╰"
                    # the two lobes are mirror images by construction:
                    # rebuild the left half from the right, so the stroke
                    # is exactly symmetric and never looks hand-wobbled
                    _mir = {"╱": "╲", "╲": "╱", "╭": "╮", "╮": "╭",
                            "╰": "╯", "╯": "╰", "─": "─", "│": "│",
                            "╳": "╳"}
                    for (xi, yi), g in list(glyphs.items()):
                        if xi <= cx:
                            continue
                        # the mirrored cell keeps its *own* place along the
                        # loop (read off the left lobe); only the glyph comes
                        # from the right one.  otherwise anything travelling
                        # around the sign would show up twice at once
                        key = (2 * cx - xi, yi)
                        # the mirror of a point at p on the right lobe sits
                        # at 1-p on the whole loop (the left lobe is traced
                        # backwards), so a feature walking the loop stays in
                        # one piece instead of appearing on both sides
                        old_p = glyphs[key][1] if key in glyphs else 1.0 - g[1]
                        glyphs[key] = [_mir[g[0]], old_p]
                    # ... and the stroke is *not* complete: a short chunk of
                    # it is missing, and that hole walks around the closed
                    # loop like a bead on a wire.  that is what makes the
                    # sign loop by itself -- no shine, no dot rolling along
                    # it: only a gap in the line.
                    base = shade(mix(P["violet"], P["ice"], 0.30), 0.62)
                    order = sorted(glyphs,
                                   key=lambda q: (glyphs[q][1], q[1], q[0]))
                    ncell = len(order)
                    glen = max(1, min(6, int(round(ncell * 0.075))))
                    if ncell >= 14:
                        glen = max(2, glen)         # a 1-cell speck reads as noise
                    hole = kk > 0.999 and ncell > 4
                    gpos = int(((t * 0.32) % 1.0) * ncell) if hole else 0
                    gpos = min(max(0, gpos), max(0, ncell - 1))
                    for idx, key in enumerate(order):
                        ch, p0 = glyphs[key]
                        rel = (idx - gpos + ncell) % ncell
                        if hole and rel < glen:
                            # this chunk is gone; remembered so the wipe can
                            # be repeated on the layered result below (the
                            # dust lives there, and a gap full of dust reads
                            # as a speck, not as a missing piece)
                            holes.append(key)
                            continue
                        col = base
                        if hole and (rel == glen or rel == ncell - 1):
                            col = shade(base, 0.34)     # the two broken ends
                        if kk < 0.999:                  # the pen drawing it
                            dh = abs(p0 - kk)
                            if dh < 0.06:
                                col = mix(base, P["ice"],
                                          0.62 * (1.0 - dh / 0.06))
                        cv2.put(key[0], key[1], ch, col)
                    if kk > 0.55 and w >= 34:
                        cv2.text(max(1, cx - hw - 4), inf_cy, "-∞",
                                 shade(P["violet"], 0.55 * kk))
                        cv2.text(min(w - 4, cx + hw + 2), inf_cy, "+∞",
                                 shade(P["violet"], 0.55 * kk))
                    if kk > 0.7 and w >= 58:
                        cv2.text(min(w - 8, cx + hw + 9), inf_cy, "x → ∞",
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
                    if ly <= h - 3:
                        cv2.text(cx - L - 2, ly, "n=1", shade(P["grey"], 0.5))
                        cv2.text(cx + L - 3, ly, "n→∞", shade(P["grey"], 0.5))

                # dot column: a conveyor running left.  every dot is born
                # on the axis at the right (n arrives at the limit) and
                # climbs as it drifts away to the left, so the ramp keeps
                # its shape while the stream keeps moving -- and nothing
                # in it bobs up and down any more.
                N = 40
                prog = ramp(t, t_inf + 0.25, t_lim + 1.1)
                nvis = max(1, int(prog * N)) if prog > 0 else 0
                span = 2 * L
                flow = span * 0.42                  # ~2.4 s per crossing
                for xx in range(cx - L, cx + L + 1, 2):
                    pp = (cx + L - xx) / float(span)
                    dd = int(round(0.4 + amp0 * pp ** 1.75))
                    if dd > 2:
                        tick = "┆" if int(xx + t * 6.0) % 7 == 0 else "┊"
                        cv2.put(xx, axis_y - 1, tick,
                                shade(P["violet"], 0.24))
                        if axis_y + 1 <= h - 3:
                            cv2.put(xx, axis_y + 1, tick,
                                    shade(P["violet"], 0.24))
                for i in range(N):
                    if prog < 1.0 and (i / float(N)) > prog:
                        continue                    # the stream fills in
                    p = (i / float(N)
                         + flow * (t - t_inf) / float(span)) % 1.0
                    xx = cx + L - int(round(span * p))
                    d = int(round(0.4 + amp0 * p ** 1.75))
                    c = mix(P["violet"], P["ice"], 0.25 + 0.65 * p)
                    age = p * span / flow
                    fresh = age < 0.30
                    col = P["white"] if fresh else shade(c, 0.9)
                    ch = "●" if fresh else "•"
                    if axis_y - d >= 4:
                        cv2.put(xx, axis_y - d, ch, col)
                    if axis_y + d <= h - 3:
                        cv2.put(xx, axis_y + d, ch, col)
                    if fresh and h >= 14:
                        fx.ripple(cv2, xx, axis_y, age,
                                  shade(P["ice"], 0.42 * (1.0 - age / 0.30)),
                                  n=5, speed=9.0, period=0.3)
                if w >= 64:
                    for jj, (lab, pp) in enumerate((("1/1", 0.92),
                                                    ("1/2", 0.74),
                                                    ("1/3", 0.56))):
                        xx = cx + L - int(round(span * pp))
                        dd = int(round(0.4 + amp0 * pp ** 1.75))
                        yy = (axis_y - dd - 1 if jj % 2 == 0
                              else axis_y + dd + 1)
                        if 4 <= yy <= h - 3:
                            cv2.text(xx, yy, lab, shade(P["grey"], 0.45))

                # the error, falling toward zero but never arriving
                if w >= 52 and axis_y + 2 <= h - 3:
                    err = 0.0400 * (1.0 - prog) ** 2 + 0.0001
                    roll = int(t * 37) % 7
                    cv2.text(cx - L, axis_y + 2,
                             "|x_n - x| = %.6f" % err, shade(P["ice"], 0.7))
                    cv2.text(cx + 6, axis_y + 2, "<<<"[roll % 3],
                             shade(P["violet"], 0.5))
                    if axis_y + 4 <= h - 3 and w >= 60:
                        cv2.rtext(axis_y + 4,
                                  "n = %3d    ε = %.6f" % (nvis, err * 2.5),
                                  shade(P["violet"], 0.7), right=cx + L + 2)
                # the limit it can never touch
                if nvis >= N and axis_y - 1 >= 4:
                    cv2.text(cx + L + 3, axis_y - 1, "lim", shade(P["rose"], 0.85))
                if t >= t_lim + 0.42 and h >= 14:
                    # the last confession of the verse: typed once, then
                    # backspaced out before the chapter closes -- even
                    # this it cannot let itself keep
                    rwl = ramp(t, 43.55, 43.93)
                    s_l, _ = fx.typewriter("you = my limitation",
                                            t - (t_lim + 0.42), 26.0)
                    s_l = s_l[:max(0, len(s_l) - int(len(s_l) * rwl + 0.5))]
                    if s_l:
                        yl_ = min(h - 3, axis_y + amp0 + 2)
                        x0l = cx - 9
                        cv2.text(x0l, yl_, s_l, shade(P["rose"], 0.95))
                        if (len(s_l) < 19 or 0.0 < rwl) and \
                                int(t * 5) % 2 == 0:
                            cv2.put(x0l + sw(s_l), yl_, "▮",
                                    shade(P["rose"], 0.55))
            stamp(cv, inf, a)
            if a > 0.5 and holes and w >= 66 and h >= 20:
                for hx, hy in holes:
                    cv.put(hx, hy, " ", None, None)

        # ---------- the proofs so far, racked one by one ----------------
        # each gift of the verse gets its mark: a point for dimension, a
        # circled dot for the circle, a wave for the tangents, infinity
        # for the limit.  Dim until handed over, lit cyan once proven.
        if h >= 16 and w >= 66:
            items = (("●", "dim", t_dim + 2.0), ("⊙", "2πr", t_cf + 1.5),
                     ("∿", "tan", t_tan + 1.0), ("∞", "lim", t_lim + 1.0))
            ty = h - 5
            pieces = [("proof ┤ ", shade(P["grey"], 0.6))]
            for k_i, (gl, lab_, t_on) in enumerate(items):
                on = t >= t_on
                fresh = on and (t - t_on) < 0.35
                gc = P["white"] if fresh else (
                    P["cyan"] if on else P["grey_dk"])
                lc = shade(P["cyan"], 0.8) if on else shade(
                    P["grey_dk"], 0.9)
                pieces.append((gl + " ", gc))
                pieces.append((lab_, lc))
                pieces.append((" │ " if k_i < len(items) - 1 else " ├",
                               shade(P["grey_dk"], 0.9)))
            total = sum(sw(s) for s, _ in pieces)
            x = w - 2 - total
            for s_, c_ in pieces:
                cv.text(x, ty, s_, c_)
                x += sw(s_)

        # ---------- the function is being sampled, all the time ----------
        # one instrument row only: a scatter of live samples.  No travelling
        # band across the top — while the formula is on screen it has to stay
        # readable.
        if h >= 18:
            row = cv.ch[5]
            for x in range(2, w - 2):
                # only ever overwrite phosphor dust: the drawn figure and its
                # formula must stay readable
                if row[x] not in " ·'`":
                    continue
                q = h01(x, int(t * 13.0), 91)
                if q < 0.40:
                    cv.put(x, 5, "·" if q < 0.20 else ("∙" if q < 0.31 else "▫"),
                           shade(P["ice"], 0.22 + 0.55 * q))
            cv.put(1, 5, "·", shade(P["ice"], 0.5))
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
                px, py = max(1, int(w * 0.08)), 4
                pw = w - 2 * px
                phh = max(2, min(int(h * 0.62), h - 8))
                tiny = phh < 4
                if not tiny:
                    fx.panel(cv2, px, py, pw, phh, shade(P["blue"], 0.9),
                             title="OSC-1  CH1  5ms/div")
                    # graticule
                    for gx in range(px + 4, px + pw - 2, 6):
                        for gy in range(py + 2, py + phh - 2, 2):
                            cv2.put(gx, gy, "·", shade(P["blue"], 0.18))
                midy = py + phh // 2
                morph = ramp(t, t_dc - 0.3, t_dc + 1.7)   # 0 AC -> 1 DC
                amp = max(1, phh // 2 - 2) * (1.0 - morph * 0.92)
                if tiny:
                    amp = 0 if morph > 0.85 else 1
                ph = -t * 7.0
                c = mix(P["cyan"], P["amber"], morph)
                # the signal runs through a diode bridge on its way out
                use_br = w >= 46 and midy - 2 >= 4 and midy + 2 <= h - 3
                bcx = px + pw - 11 if use_br else px + pw - 1
                kbr = ramp(t, t_dc - 0.3, t_dc + 0.1)
                # the trace retracts into the bridge as it materializes
                xend = px + pw - 1 - int(11 * kbr) if use_br else px + pw - 1
                for x in range(px + 1, xend):
                    v = math.sin((x - px) * 0.22 + ph)
                    y = midy - int(round(amp * v))
                    cv2.put(x, y, "•", c)
                    if amp > 1:
                        cv2.put(x, y - 1, "·", shade(c, 0.4))
                if use_br:
                    bcy = midy
                    if kbr > 0.02:
                        bcc = mix(P["soft"], P["amber"], kbr)
                        # west arm: alternating current arrives
                        for i in range(3):
                            cv2.put(bcx - 6 + i, bcy, "~",
                                    shade(bcc, 0.5 + 0.5 * kbr))
                        cv2.put(bcx - 3, bcy, "▷", bcc)
                        # the diamond itself
                        cv2.put(bcx, bcy - 2, "◇", bcc)
                        cv2.put(bcx, bcy + 2, "◇", bcc)
                        cv2.put(bcx - 2, bcy - 1, "╱", shade(bcc, 0.8))
                        cv2.put(bcx - 1, bcy - 2, "╱", shade(bcc, 0.8))
                        cv2.put(bcx + 1, bcy - 2, "╲", shade(bcc, 0.8))
                        cv2.put(bcx + 2, bcy - 1, "╲", shade(bcc, 0.8))
                        cv2.put(bcx - 2, bcy + 1, "╲", shade(bcc, 0.8))
                        cv2.put(bcx - 1, bcy + 2, "╲", shade(bcc, 0.8))
                        cv2.put(bcx + 1, bcy + 2, "╱", shade(bcc, 0.8))
                        cv2.put(bcx + 2, bcy + 1, "╱", shade(bcc, 0.8))
                        cv2.put(bcx, bcy, "◆", bcc)
                        # east arm: direct current leaves
                        cv2.put(bcx + 3, bcy, "▷", bcc)
                        for i in range(3):
                            cv2.put(bcx + 4 + i, bcy, "═",
                                    shade(bcc, 0.5 + 0.5 * kbr))
                        # the rectified trace runs flat to the edge
                        for x in range(bcx + 7, px + pw - 1):
                            cv2.put(x, bcy, "•", mix(c, P["amber"], kbr))
                    # current made visible: charge rides the wave in, ...
                    if xend - px > 6:
                        xq = px + 2 + int(((t * 9.0) % 1.0)
                                          * max(1, xend - px - 3))
                        vq = math.sin((xq - px) * 0.22 + ph)
                        yq = midy - int(round(amp * vq))
                        cv2.put(xq, yq, "◉", P["white"])
                    # ... and leaves as a steady drift of dots
                    if kbr > 0.5 and px + pw - 2 - bcx > 6:
                        xq = bcx + 4 + int(((t * 6.0) % 1.0)
                                           * (px + pw - 2 - bcx - 4))
                        blink = (P["white"] if (t * 13.0) % 1.0 > 0.5
                                 else shade(P["amber"], 0.9))
                        cv2.put(xq, bcy, "◉", blink)
                # labels + meters
                ly_ = min(h - 3, py + phh + 1)
                lab = "AC ~" if morph < 0.5 else "DC ─"
                cv2.text(px + 2, ly_, lab, mix(P["cyan"], P["amber"], morph))
                if morph > 0.5 and not tiny:
                    cv2.text(px + 9, ly_, "rectified", shade(P["amber"], 0.7))
                vpp = 6.2 * (1.0 - morph) + 0.1 * morph
                rip = ("∞" if morph < 0.05
                       else "%.1f%%" % (3.4 * (1.0 - morph) + 0.3))
                if not tiny:
                    cv2.rtext(ly_, "Vpp %.1fV  ripple %s" % (vpp, rip),
                              shade(P["soft"], 0.8), right=px + pw - 1)
                else:
                    cv2.rtext(ly_, "Vpp %.1fV  %s" % (vpp, rip),
                              shade(P["soft"], 0.8), right=px + pw - 1)
            stamp(cv, osc, a)

        # ---------- blind vision / dizzy spiral ---------------------
        a = fade_window(t, t_blind - 0.3, t_unite + 0.2, 0.4, 0.5)
        if a > 0.01:
            def dizzy(cv2):
                # closing eyelid
                k = ramp(t, t_blind, t_blind + 1.0)
                if k < 1.0:
                    if h >= 16:
                        ex = art.ART["eye"]
                        ew = max(sw(l) for l in ex)
                        x = cx - ew // 2
                        y = max(4, cy - len(ex) // 2)
                        for j, line_ in enumerate(ex):
                            lim = j / len(ex)
                            if lim < k:
                                continue
                            cv2.text(x, y + j, line_, shade(P["ice"], 0.9))
                        # lid
                        lid = int(k * len(ex))
                        for j in range(lid):
                            cv2.text(x, y + j, ex[j].replace("█", "▄"),
                                     shade(P["blue"], 0.6))
                    else:
                        # a two-line eye is all the room there is
                        y = max(4, cy - 1)
                        if k < 0.55:
                            cv2.text(cx - 3, y, "  ·◉·  ", shade(P["ice"], 0.9))
                        else:
                            n_l = min(6, int((k - 0.55) / 0.45 * 6) + 1)
                            cv2.text(cx - 3, y, "▄" * n_l,
                                     shade(P["blue"], 0.6))
                        cv2.text(cx - 3, y + 1, " ▀▀▀▀ ", shade(P["ice"], 0.5))
                # blinded: the world degrades into a field of blinking
                # horizontal stripes -- vision itself is losing the picture
                kb = ramp(t, t_blind + 0.55, t_blind + 1.5)
                if kb > 0.02:
                    for y in range(4, min(h - 3, cy + 16)):
                        ph = math.sin(t * 7.0 + y * 0.9)
                        if ph < 0.25:
                            continue
                        near = 1.0 - min(1.0, abs(y - cy) / 11.0)
                        ch = "─" if ph < 0.72 else "━"
                        col = shade(mix(P["blue"], P["ice"],
                                        0.20 + 0.55 * near),
                                    0.28 + 0.34 * kb + 0.22 * near)
                        cv2.hline(1, y, w - 2, ch, col)
                # dizzy: a starburst spinning too fast to hold on to
                sk = ramp(t, t_dizzy - 0.1, t_dizzy + 0.5)
                if sk > 0:
                    spin = t * (7.0 + 6.0 * ramp(t, t_dizzy, t_bc))
                    arms = 6
                    for arm in range(arms):
                        a0 = spin + arm * math.pi * 2.0 / arms
                        ca = math.cos(a0) * 2.1
                        sa = math.sin(a0) * 0.85
                        for i in range(1, 38):        # a solid ray, not dots
                            u = i / 37.0
                            rr = 0.9 + u * 14.5
                            x = cx + int(ca * rr)
                            y = cy + int(sa * rr)
                            if not (0 <= x < w and 4 <= y < h - 3):
                                continue
                            c = shade(mix(P["violet"], P["ice"], u), 0.55)
                            cv2.put(x, y, "·+*×"[min(3, int(u * 3.4))], c)
                    # rings pulsing outward from the centre of the vertigo
                    for r_i in range(3):
                        kk = (t * 0.85 + r_i / 3.0) % 1.0
                        rr = 2 + int(kk * 13)
                        ry_c = min(int(rr * 0.8), cy - 4, h - 3 - cy)
                        if ry_c >= 2:
                            fx.circle(cv2, cx, cy, max(4, int(rr * 1.9)),
                                      shade(P["violet"], 0.5 * (1.0 - kk)),
                                      "·", ry=ry_c)
                    if t > t_dizzy + 0.4:
                        # the lyric doubles itself: the word and its typed
                        # echo, the second copy dimmer, a beat behind
                        anim.echo_row(cv2, 0, cy + 2, "so dizzy", t,
                                      t_dizzy + 0.4, n=2,
                                      fg=shade(P["violet"], 0.85),
                                      sep="  ", decay=0.55, cps=14.0,
                                      cx=w // 2)
                        deg = int((t - t_dizzy) * 720) % 360
                        cv2.text(2, h - 4, "blind 100%%  θ %03d°" % deg,
                                 shade(P["violet"], 0.7), P["black"])
            stamp(cv, dizzy, a)

        # ---------- time travel: every age runs backwards -----------
        a = fade_window(t, t_travel - 0.25, t_unite + 0.10, 0.4, 0.30)
        if a > 0.01:
            def clock(cv2):
                k = ramp(t, t_travel, t_bc + 1.2)      # 0 -> 1 as time rewinds
                dcy = cy - (2 if h >= 22 else 0)
                if h < 16:
                    dcy = (h + 1) // 2
                r = max(5, min(w // 9, h - 10 if h >= 20 else h - 7))
                if h < 16:
                    r = min(w // 9, 2 * min(dcy - 5, h - 4 - dcy))
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

                # the year rolls backwards through zero
                year = int(2016 - k * 4016)
                ys = ("%d A.D." % max(1, year)) if year >= 0 else ("%d B.C." % -year)
                era = "A.D." if year >= 0 else "B.C."

                if r >= 4:
                    # ---- the dial is opaque: ages vanish behind the clock ---
                    for yy in range(dcy - r // 2 - 1, dcy + r // 2 + 2):
                        if yy < 4 or yy >= h - 2:
                            continue
                        dyy = (yy - dcy) * 2.0
                        if abs(dyy) >= r:
                            continue
                        hw = int(math.sqrt(max(0.0, r * r - dyy * dyy)))
                        cv2.fill(cx - hw, yy, 2 * hw + 1, 1, " ")

                    # dial: a dim bezel of shaded cells, then the face
                    for yy in range(dcy - r // 2 - 1, dcy + r // 2 + 2):
                        if yy < 4 or yy >= h - 1:
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
                    if h >= 18:
                        dt = year - 2016
                        lab = era if abs(dt) < 4 else "%s · Δt %+d yr" % (era, dt)
                        cv2.ctext(dcy + 2, lab, mix(P["amber"], P["cyan"], k))
                else:
                    # too little height for a face: a digital clock
                    drow = max(4, dcy - 1)
                    spin_ch = "◷◐◓◑"[int(t * 4) % 4]
                    cv2.put(2, drow, spin_ch, shade(P["amber"], 0.85))
                    cv2.ctext(drow, ys, shade(P["rose"], 0.95), P["black"])
                    ty2 = h - 4
                    if ty2 <= drow + 1:
                        ty2 = h - 3
                    cv2.text(2, ty2, "A.D.", shade(P["amber"], 0.8))
                    cv2.rtext(ty2, "B.C.", shade(P["cyan"], 0.8), right=w - 3)
                    fx.line(cv2, 8, ty2, w - 8, ty2, shade(P["soft"], 0.35), "─")
                    cxp = w - 8 - int((w - 16) * k)
                    cv2.put(cxp, ty2, "▼", P["rose"])

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
                    if 4 <= y1 <= h - 3:
                        cv2.put(x, y1, "·", shade(P["cyan"], 0.9))
                    if 4 <= y2 <= h - 3:
                        cv2.put(x, y2, "·", shade(P["pink"], 0.9))
                if k > 0.75:
                    c = mix(P["cyan"], P["pink"], 0.5)
                    for x in range(w):
                        y = cy + int(amp * math.sin(x * 0.16 + t * 2.2))
                        if 4 <= y <= h - 3:
                            cv2.put(x, y, "─", mix(c, P["white"],
                                                   ramp(k, 0.75, 1.0)))
                # two diamonds approach
                kk = ramp(t, t_unite + 0.4, t_deep + 0.8)
                gap = int((1 - kk) * w * 0.22) + 2
                y_d = max(4, cy - 5)
                for sgn, c in ((-1, P["phos"]), (1, P["pink"])):
                    x = cx + sgn * gap
                    cv2.put(x, y_d, "◆", c)
                # the phase meter: two phases, closing on lock
                deg = int(round(math.degrees((1.0 - kk) * math.pi)))
                if h >= 20 and w >= 56:
                    anim.dial(cv2, cx, cy + 3, 4, kk,
                              mix(P["violet"], P["pink"], kk),
                              label="Δφ %3d°" % deg)
                elif w >= 40:
                    cv2.ctext(min(h - 4, cy + 3), "Δφ %3d°" % deg,
                              mix(P["violet"], P["pink"], kk))
                # "so deeply so deeply" -- the echo types in a beat behind
                # the first, dimmer, like the voice doubling on itself,
                # while the phases are still closing on the lock
                cap_y = cy - 7 if cy - 7 >= 4 else h - 3
                if cap_y >= 4:
                    anim.echo_row(cv2, 0, cap_y, "so deeply", t,
                                  t_deep + 0.15, n=2, fg=P["pink"],
                                  sep="  ", decay=0.55, cps=14.0, cx=w // 2)
                if kk > 0.92:
                    rad_ = min(7, y_d - 4)
                    if rad_ >= 1:
                        fx.sparkle(cv2, cx, y_d, t, P["white"],
                                   seed=int(t * 7), n=12, rad=rad_)
                    cv2.ctext(min(h - 3, cy + 8 if h >= 20 else h - 4),
                              "Δφ 0° · LOCK", P["white"])
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
        # the rain must not stain the telemetry rows or the status bar
        cv.fill(0, 0, w, 4, " ")
        cv.fill(0, h - 2, w, 2, " ")
        for i in range(3):
            age = (t * 0.55 + i / 3.0) % 1.0
            r = int(age * min(w, h) * 0.75)
            if r < 2:
                continue
            ry_ = min(r / 2, h // 2 - 4, h - 3 - h // 2)
            if ry_ < 1:
                continue
            c = shade(P["rose"], 0.45 * (1 - age))
            fx.circle(cv, cx, h // 2, r, c, "·", ry=ry_, steps=max(20, r * 3))

        # ---------- the heart is simulated on a full-frame monitor ---
        if t >= t_stim - 0.3 and t < t_trap + 1.0 and h >= 13:
            def ecg_full(cv2):
                scr = ramp(t, t_stim - 0.3, t_stim + 0.55)
                mid = h // 2
                amp = max(2, min(int(h * 0.33), mid - 4, h - 3 - mid))
                # monitor paper: fine grid + heavier time lines, from row 4
                for gx in range(2, w - 2, 6):
                    for gy in range(4, h - 3, 3):
                        cv2.put(gx, gy, "·", shade(P["pink"], 0.09 * scr))
                for gx in range(2, w - 2, 18):
                    cv2.vline(gx, 4, h - 8, ":", shade(P["pink"], 0.15 * scr))
                cv2.hline(2, mid, w - 4, "·", shade(P["pink"], 0.22))
                # the sweep head runs left -> right, over and over
                per = 2.6
                ph = ((t - t_stim) % per) / per
                span = max(12, w - 6)
                head = 3 + int(ph * span)
                phase = (t - t_stim) * 1.15
                amp_b = min(amp + 1, mid - 4, h - 3 - mid)
                # the beat runs the heart louder
                amp_use = amp_b if beatp > 0.5 else amp
                for echo in range(3):          # ghost passes behind the trace
                    eu = echo * 0.055
                    ed = 1.0 / (echo + 1)
                    for xx in range(3, w - 3):
                        u = (xx - 3) / 22.0 + phase - eu
                        v = fx.ecg(u)
                        yy = mid - int(round(amp_use * v))
                        if not (4 <= yy <= h - 3):
                            yy = max(4, min(h - 3, yy))
                        ahead = xx > head
                        if echo == 0:
                            col = shade(mix(P["pink"], P["white"],
                                            0.15 if ahead else 0.5),
                                        0.32 if ahead else 0.95)
                            cv2.put(xx, yy, "·" if ahead else "•", col)
                            if abs(v) > 0.45:      # stems fill the frame
                                for y2 in range(max(4, min(mid, yy) + 1),
                                                min(h - 3, max(mid, yy))):
                                    cv2.put(xx, y2, "│",
                                            shade(P["pink"],
                                                  0.12 if ahead else 0.30))
                        else:
                            cv2.put(xx, yy, "·", shade(P["rose"], 0.10 * ed))
                # each beat pings a column down the whole frame
                if beatp > 0.30:
                    bxp = min(w - 3, head + 3)
                    for y in range(4, h - 3, 2):
                        cv2.put(bxp, y, "·",
                                shade(P["rose"], 0.26 * beatp))
                for yy in range(4, min(h - 2, mid + amp_use + 3)):
                    if h01(head, yy, int(t * 8)) < 0.72:
                        cv2.put(head, yy, "▌", shade(P["white"], 0.28))
                # second channel: the pulse wave
                p2y = min(h - 4, int(h * 0.79))
                for xx in range(3, w - 3):
                    u = (xx - 3) / 40.0 - phase * 0.7
                    v = math.sin(u * 6.283) * 0.55 + math.sin(u * 12.566) * 0.22
                    y2 = p2y - int(amp * 0.5 * v)
                    if 4 <= y2 <= h - 3:
                        cv2.put(xx, y2, "·", shade(P["ice"], 0.28))
                hr = 68 + int(62 * ramp(t, t_stim, t_stim + 3.0))                     + int(3 * beatp)
                ry = max(4, mid - amp - 2)
                if w >= 62:
                    cv2.text(3, ry, "HR %03d BPM · SINUS" % hr,
                             shade(P["pink"], 0.9))
                    cv2.rtext(ry, "SpO₂ 98% · SIM 1/1",
                              shade(P["ice"], 0.8), right=w - 4)
                elif w >= 36:
                    cv2.text(3, ry, "HR %03d" % hr, shade(P["pink"], 0.9))
                    cv2.rtext(ry, "SpO₂ 98%", shade(P["ice"], 0.8),
                              right=w - 4)
            stamp(cv, ecg_full, fade_window(t, t_stim - 0.3, t_trap + 1.0, 0.5, 0.5))

        # ---------- heart --------------------------------------------
        grow = ramp(t, t_stim, t_stim + 2.0) * 0.4 + 0.6
        grow = min(1.35, grow + 0.5 * ramp(t, t_sat, t_sat + 1.5))
        if h >= 21:
            heart = art.ART["heart_big"]
        elif h >= 12:
            heart = art.ART["heart_mid"]
        else:
            heart = art.ART["heart_small"]
        hy = max(4, h // 2 - len(heart) // 2 - 1)
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
                yh = hy + j - (1 if beatp > 0.6 and hy > 4 else 0)
                cv.put(hx - hw // 2 + i, yh, ch, color)

        # halo
        if t > t_sat - 0.2:
            for i in range(10):
                ang = t * 0.8 + i * 0.63
                r = hw * 0.62
                x = hx + int(math.cos(ang) * r * 1.1)
                y = hy + len(heart) // 2 + int(math.sin(ang) * r / 2.2)
                if 4 <= y <= h - 3:
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
                if bw < 8:
                    return
                x = cx - bw // 2
                y = h - 5
                kk = ramp(t, t_sat - 0.1, t_sat + 2.4)
                if y - 2 >= 4:
                    cv2.ctext(y - 2, "SATISFACTION", P["pink"])
                # "then I can -- then I can" -- the answer stutters too,
                # just above the label, clear of the heart at every size
                # that can afford the row
                if h >= 18 and w >= 52 and y - 3 >= 6:
                    anim.echo_row(cv2, 0, y - 3, "then I can", t, t_sat,
                                  n=2, fg=shade(P["rose"], 0.75),
                                  sep="  ", decay=0.55, cps=16.0, cx=cx)
                fx.bar(cv2, x, y, bw, kk, P["rose"], None)
                cv2.ctext(min(h - 3, y + 1), "%3d%%" % int(kk * 100), P["white"])
                # once the bar is full the claim is made in the lyric's
                # own words: "your only satisfaction" -- the one word it
                # has been circling around, bracketed in the scene accent
                # and beating with the track once it has said it
                if kk >= 0.999 and y - 4 >= 4:
                    kc = ramp(t, t_sat + 2.4, t_sat + 2.9)
                    x0o = cx - 12
                    cv2.text(x0o, y - 4, "your", shade(P["soft"], 0.85 * kc))
                    cv2.text(x0o + 5, y - 4, "[only]",
                             shade(mix(P["pink"], P["white"],
                                       0.15 + 0.45 * beatp), kc))
                    cv2.text(x0o + 12, y - 4, "satisfaction",
                             shade(P["soft"], 0.85 * kc))
            stamp(cv, sat, fade_window(t, t_sat - 0.1, t_exec + 1.4,
                                       0.4, 0.6))

        # ---------- make you happy ----------------------------------
        if t >= t_happy - 0.15:
            def happy(cv2):
                kk = ramp(t, t_happy - 0.15, t_happy + 0.9)
                hcx, hcy = hx, hy + len(heart) // 2
                # balloons drifting up
                for i in range(3):
                    ph = ((t - t_happy) * 0.30 + i * 0.33) % 1.0
                    bx = hcx + (i - 1) * (hw // 2 + 7) + int(math.sin(t * 1.3 + i) * 2)
                    b_top = max(4, hcy - 3)
                    by = b_top - int(ph * (b_top - 4))
                    if by < 4 or bx < 2 or bx > w - 3:
                        continue
                    c = (P["rose"], P["gold"], P["pink"])[i]
                    if by - 1 >= 4:
                        cv2.put(bx, by - 1, "▄", shade(c, 0.9))
                    cv2.put(bx - 1, by, "(", shade(c, 0.9))
                    cv2.put(bx + 1, by, ")", shade(c, 0.9))
                    cv2.put(bx, by + 1, "▀", shade(c, 0.9))
                    cv2.vline(bx, by + 2,
                              max(0, min(3, h - 3 - by - 2)), "|",
                              shade(P["soft"], 0.35))
                # confetti
                c0 = min(h - 3, hcy + 4)
                for i in range(28):
                    ph = ((t - t_happy) * (0.45 + 0.5 * h01(i, 101)) + h01(i, 102)) % 1.0
                    px = hcx + int(math.sin(ph * 5.5 + i) * (hw * 0.95))
                    py = c0 - int(ph * (c0 - 4))
                    if py < 4 or px < 1 or px > w - 2:
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
                    if hy - 3 >= 4:
                        cap_y = hy - 3
                    elif hy + len(heart) <= h - 4:
                        cap_y = hy + len(heart)
                    else:
                        cap_y = None
                    if cap_y is not None:
                        cv2.ctext(cap_y, "H A P P Y",
                                  shade(mix(P["pink"], P["white"],
                                            0.15 + 0.55 * beatp), 0.95))
            stamp(cv, happy, fade_window(t, t_happy - 0.15, t_trap + 0.6, 0.4, 0.5))

        # ---------- terminal: run the execution ---------------------
        if t >= t_exec - 0.2:
            def term(cv2):
                px = int(w * 0.55)
                pw = min(34, w - px - 2)
                py = max(4, h // 2 - 6)
                phh = min(11, h - 3 - py)
                if phh < 4 or pw < 14:
                    # a one-line console is all that fits
                    if h >= 9 and w >= 30:
                        y1 = max(4, h - 5)
                        shown, _ = fx.typewriter("world.execute(me);",
                                                 t - t_exec, 26.0)
                        if shown:
                            cv2.text(2, y1, "$ ", shade(P["phos"], 0.9))
                            i_me = shown.find("me")
                            if i_me >= 0 and t >= t_exec + 0.98:
                                c_me = mix(mix(P["phos"], P["pink"], 0.55),
                                           P["white"], 0.35 + 0.65 * beatp)
                            else:
                                c_me = P["white"]
                            if i_me < 0:
                                cv2.text(4, y1, shown, P["white"])
                            else:
                                cv2.text(4, y1, shown[:i_me], P["white"])
                                cv2.text(4 + i_me, y1, shown[i_me:i_me + 2],
                                         c_me)
                                cv2.text(6 + i_me, y1, shown[i_me + 2:],
                                         P["white"])
                        if t >= t_exec + 1.9:
                            cv2.rtext(y1, "exit 0 ✓", P["phos"], right=w - 2)
                    return
                fx.panel(cv2, px, py, pw, phh, P["phos_dim"], title="bash")
                # the command types itself
                shown, _ = fx.typewriter("world.execute(me);",
                                         t - t_exec, 26.0)
                cv2.text(px + 2, py + 1, "$ " + shown, P["white"])
                # ...then assembles from real tokens, chip by chip
                yy = py + 2
                xx = px + 2
                for ci, chp in enumerate(["world", ".", "execute",
                                           "(", "me", ")", ";"]):
                    if t < t_exec + 0.5 + ci * 0.12:
                        break
                    if xx + sw(chp) + 1 > px + pw - 1:
                        break
                    tok_c = mix(P["phos"], P["white"], 0.25 * (ci % 2))
                    if chp == "me" and t >= t_exec + 0.98:
                        # the argument is alive: the moment the parser
                        # reaches it, it beats with the track, going
                        # rose-pink at the peak of every systole
                        tok_c = mix(mix(P["phos"], P["pink"], 0.55),
                                    P["white"], 0.35 + 0.65 * beatp)
                    cv2.text(xx, yy, chp, tok_c)
                    xx += sw(chp) + 1
                # a two-level parse tree under the tokens
                if t >= t_exec + 0.75 and phh >= 6:
                    t_k = ramp(t, t_exec + 0.75, t_exec + 1.35)
                    cv2.text(px + 2, py + 3, "call", shade(P["soft"], 0.9))
                    cv2.text(px + 7, py + 3, "·" * max(1, int(4 * t_k)),
                             shade(P["soft"], 0.5))
                    if t_k > 0.4:
                        cv2.text(px + 12, py + 3, "world.exe",
                                 shade(P["ice"], 0.9))
                    if t_k > 0.75 and py + 4 <= h - 4:
                        cv2.text(px + 12, py + 4, "arg: me",
                                 shade(P["ice"], 0.8))
                # ▶ RUN + a progress bar that actually fills (timed to
                # complete just as the trap closes over the machine)
                row_r = py + 5 if phh >= 6 else py + 3
                if t >= t_exec + 1.3 and row_r <= h - 4:
                    cv2.text(px + 2, row_r, "▶ RUN", P["phos"])
                    kk = ramp(t, t_exec + 1.3, t_exec + 1.7)
                    if pw >= 12:
                        fx.bar(cv2, px + 8, row_r, pw - 10, kk, P["phos"],
                               None, full="▓", rest="░")
                    spin = "-\\|/"[int(t * 10) % 4]
                    if row_r + 1 <= h - 4:
                        cv2.text(px + 2, row_r + 1,
                                 "%s %3d%%" % (spin, int(kk * 100)), P["phos"])
                    if kk >= 1.0 and row_r + 2 <= h - 4:
                        cv2.text(px + 2, row_r + 2, "exit 0 ✓", P["phos"])
                # the register bus underneath never stops (full panel only)
                yr = py + phh - 2
                if phh >= 11 and 4 <= yr <= h - 4:
                    anim.hexrow(cv2, px + 2, yr, max(1, (pw - 4) // 3), t,
                                shade(P["phos_dim"], 0.8), seed=7, hz=10)
            stamp(cv, term, fade_window(t, t_exec - 0.2, t_trap + 0.25, 0.3, 0.45))

        # ---------- trapped in the simulation -----------------------
        if t >= t_trap - 0.2:
            def trap(cv2):
                kk = ramp(t, t_trap - 0.2, t_ssim + 0.9)
                bw = int((w - 6) - (w - 6 - min(26, w - 6)) * kk)
                bh_top = h - 6
                bh_min = min(13, bh_top)
                bh = int(bh_top - (bh_top - max(2, bh_min)) * kk)
                x = cx - bw // 2
                y = max(4, h // 2 - bh // 2)
                fx.bracket(cv2, x, y, bw, bh, mix(P["pink"], P["white"], 0.3),
                           style="<>")
                if kk > 0.55 and w >= 40:
                    # the caption row is measured against the box's
                    # FINAL size (frozen reference), so it never rides
                    # the shrink -- and at short heights it falls back
                    # to the floor row, under the isolation label
                    bh_ref = min(13, h - 6)
                    y_ref = max(4, h // 2 - bh_ref // 2)
                    if y_ref - 3 >= 4:
                        row_s = y_ref - 3
                    elif h >= 21:
                        row_s = h - 3
                    else:
                        row_s = None
                    if row_s is not None:
                        # the lyric stutters into being: "strange --
                        # strange strange -- simulation", each word
                        # racing the one before it, the noun arriving
                        # last, once, and staying
                        t0s = t_ssim - 0.30
                        anim.echo_row(cv2, 0, row_s, "strange", t, t0s,
                                      n=2, fg=P["pink"], sep="  ",
                                      decay=0.5, cps=16.0, cx=cx - 6)
                        age3 = t - (t0s + 1.15)
                        s3 = "simulation"[:max(0, int(age3 * 16))]
                        if s3:
                            cv2.text(cx + 6, row_s, s3,
                                     shade(P["pink"], 0.85))
                        if age3 < 11.0 / 16.0 and int(t * 5) % 2 == 0:
                            cv2.put(cx + 6 + sw(s3), row_s, "▮",
                                    shade(P["pink"], 0.55))
                    cv2.put(x, y + bh // 2, "╬", P["white"])
                    cv2.put(x + bw - 1, y + bh // 2, "╬", P["white"])
                    if y + bh <= h - 4:
                        cv2.ctext(y + bh, "isolation box · you",
                                  shade(P["pink"], 0.85))
                # scan wipe, sweeping only the live band
                sy = 4 + int((t * 22) % max(1, h - 7))
                cv2.hline(0, sy, w, "─", shade(P["pink"], 0.25))
            stamp(cv, trap, fade_window(t, t_trap - 0.2, self.t1 + 0.2, 0.3, 0.2))

        # ---------- STIMULATION meter ---------------------------------
        if t >= t_stim - 0.1 and t < t_sat:
            def stim(cv2):
                if h < 12:
                    return
                bw2 = max(8, min(30, w - 12))
                x2 = max(2, cx - bw2 // 2)
                y2 = h - 7
                if y2 < 4:
                    return
                lvl = min(1.0, 0.35 + 0.5 * loud + 0.25 * beatp)
                cv2.ctext(y2 - 1, "STIMULATION", shade(P["rose"], 0.8))
                fx.bar(cv2, x2, y2, bw2, lvl, P["rose"], None,
                       full="▓", rest="·")
                cv2.ctext(min(h - 3, y2 + 1), "%3d%%" % int(lvl * 100),
                          P["white"])
                # the vocal stutters its own opening: "if I can --
                # if I can" -- the echo types in a beat behind, dimmer.
                # It rides the top content row: below it sit the monitor
                # and the heart, and no lower row is ever clear of both
                if h >= 18 and w >= 52:
                    anim.echo_row(cv2, 0, 4, "if I can", t, t_stim,
                                  n=2, fg=shade(P["rose"], 0.75),
                                  sep="  ", decay=0.55, cps=16.0, cx=cx)
            stamp(cv, stim, fade_window(t, t_stim - 0.1, t_sat, 0.5, 0.4))

        fx.scanlines(cv, 0.85)
        fx.vignette(cv, 0.28)
