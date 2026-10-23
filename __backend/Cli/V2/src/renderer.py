"""ASCII canvas renderer: colors, wide-char aware drawing, ANSI output.

Design notes
------------
* Every cell stores a character plus fg/bg colors given as (r, g, b) tuples.
  The output layer converts to truecolor or 256-color depending on the mode.
* Coordinates are terminal *display columns*.  CJK / fullwidth characters
  occupy two columns; the second column is stored as CONTINUATION and skipped
  when emitting.
* Output is emitted with absolute cursor positioning per row, so wrapping never
  corrupts the frame.
"""

import os
import unicodedata

CONT = "\x00"          # continuation cell for a double-width character


# --------------------------------------------------------------------------
# display width helpers
# --------------------------------------------------------------------------

def cw(ch):
    """Display width of one character."""
    if ch == CONT:
        return 0
    o = ord(ch)
    if o < 0x1100:
        return 1
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def sw(s):
    """Display width of a string."""
    return sum(cw(c) for c in s)


# --------------------------------------------------------------------------
# color helpers
# --------------------------------------------------------------------------

def mix(a, b, k):
    """Linear blend between two RGB colors (k=0 -> a, 1 -> b)."""
    if a is None:
        a = (200, 200, 200)
    if b is None:
        b = (200, 200, 200)
    k = 0.0 if k < 0 else (1.0 if k > 1 else k)
    return (
        int(a[0] + (b[0] - a[0]) * k),
        int(a[1] + (b[1] - a[1]) * k),
        int(a[2] + (b[2] - a[2]) * k),
    )


def shade(c, k):
    """Multiply brightness."""
    return (max(0, min(255, int(c[0] * k))),
            max(0, min(255, int(c[1] * k))),
            max(0, min(255, int(c[2] * k))))


def grey(c, k=1.0):
    """Desaturate: k=0 full color, k=1 fully grey."""
    y = int(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    return mix(c, (y, y, y), k)


# -- palette ---------------------------------------------------------------

NO = None          # "default terminal color"

P = {
    "phos":     (0x6f, 0xff, 0x9c),   # phosphor green
    "phos_dim": (0x2e, 0x8b, 0x57),
    "phos_dk":  (0x16, 0x45, 0x2c),
    "cyan":     (0x5e, 0xd7, 0xff),
    "blue":     (0x5f, 0x87, 0xff),
    "ice":      (0xb8, 0xe8, 0xff),
    "violet":   (0xb0, 0x8c, 0xff),
    "magenta":  (0xff, 0x6f, 0xd9),
    "pink":     (0xff, 0x9a, 0xc4),
    "rose":     (0xff, 0x5e, 0x82),
    "red":      (0xff, 0x33, 0x44),
    "blood":    (0xa8, 0x12, 0x22),
    "amber":    (0xff, 0xc4, 0x66),
    "gold":     (0xff, 0xdc, 0x7a),
    "white":    (0xee, 0xf3, 0xf8),
    "soft":     (0xc2, 0xcc, 0xd8),
    "grey":     (0x8c, 0x97, 0xa3),
    "grey_dim": (0x55, 0x5e, 0x69),
    "grey_dk":  (0x2a, 0x30, 0x38),
    "black":    (0x00, 0x00, 0x00),
}


# --------------------------------------------------------------------------
# deterministic hashing (seek-safe "randomness")
# --------------------------------------------------------------------------

def h01(*vals):
    """Deterministic pseudo random in [0,1) from integers."""
    h = 2166136261
    for v in vals:
        h ^= int(v) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


def hsign(*vals):
    return 1 if h01(*vals) < 0.5 else -1


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------

class Canvas:
    __slots__ = ("w", "h", "ch", "fg", "bg")

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ch = [[" "] * w for _ in range(h)]
        self.fg = [[None] * w for _ in range(h)]
        self.bg = [[None] * w for _ in range(h)]

    # -- basic ------------------------------------------------------------
    def clear(self):
        w, h = self.w, self.h
        self.ch = [[" "] * w for _ in range(h)]
        self.fg = [[None] * w for _ in range(h)]
        self.bg = [[None] * w for _ in range(h)]

    def put(self, x, y, ch, fg=None, bg=None):
        if x < 0 or y < 0 or y >= self.h or x >= self.w:
            return
        self.ch[y][x] = ch
        self.fg[y][x] = fg
        self.bg[y][x] = bg

    def put_ch(self, x, y, ch):
        """Put character keeping whatever is there (colors untouched)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            self.ch[y][x] = ch

    def text(self, x, y, s, fg=None, bg=None):
        """Draw a string; x is the left display column.  Returns end x."""
        if y < 0 or y >= self.h:
            return x
        cx = x
        for c in s:
            w = cw(c)
            if w == 0:
                continue
            if cx >= self.w:
                break
            if cx >= 0:
                self.ch[y][cx] = c
                self.fg[y][cx] = fg
                self.bg[y][cx] = bg
                if w == 2 and cx + 1 < self.w:
                    self.ch[y][cx + 1] = CONT
                    self.fg[y][cx + 1] = fg
                    self.bg[y][cx + 1] = bg
            cx += w
        return cx

    def ctext(self, y, s, fg=None, bg=None, cx=None):
        """Draw centered string (whole canvas or around cx)."""
        mid = self.w // 2 if cx is None else cx
        return self.text(mid - sw(s) // 2, y, s, fg, bg)

    def rtext(self, y, s, fg=None, bg=None, right=None):
        r = self.w - 1 if right is None else right
        return self.text(r - sw(s) + 1, y, s, fg, bg)

    def hline(self, x, y, w, c="-", fg=None, bg=None):
        for i in range(w):
            self.put(x + i, y, c, fg, bg)

    def vline(self, x, y, h, c="|", fg=None, bg=None):
        for i in range(h):
            self.put(x, y + i, c, fg, bg)

    def fill(self, x, y, w, h, c=" ", fg=None, bg=None):
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, c, fg, bg)

    def paint(self, x, y, w, h, fg=None, bg=None):
        """Recolor region, keeping characters."""
        for j in range(max(0, y), min(self.h, y + h)):
            for i in range(max(0, x), min(self.w, x + w)):
                if fg is not None:
                    self.fg[j][i] = fg
                if bg is not None:
                    self.bg[j][i] = bg

    def box(self, x, y, w, h, fg=None, bg=None, corner="+", hc="-", vc="|"):
        if w < 2 or h < 2:
            return
        self.hline(x + 1, y, w - 2, hc, fg, bg)
        self.hline(x + 1, y + h - 1, w - 2, hc, fg, bg)
        self.vline(x, y + 1, h - 2, vc, fg, bg)
        self.vline(x + w - 1, y + 1, h - 2, vc, fg, bg)
        self.put(x, y, corner, fg, bg)
        self.put(x + w - 1, y, corner, fg, bg)
        self.put(x, y + h - 1, corner, fg, bg)
        self.put(x + w - 1, y + h - 1, corner, fg, bg)

    def frame(self, x, y, w, h, fg=None, bg=None, title=None, style="thin"):
        """Unicode frame with optional title."""
        if w < 2 or h < 2:
            return
        if style == "thin":
            tl, tr, bl, br, hz, vt = "┌", "┐", "└", "┘", "─", "│"
        elif style == "double":
            tl, tr, bl, br, hz, vt = "╔", "╗", "╚", "╝", "═", "║"
        else:
            tl, tr, bl, br, hz, vt = "▛", "▜", "▙", "▟", "▀", "▌"
        self.hline(x + 1, y, w - 2, hz, fg, bg)
        self.hline(x + 1, y + h - 1, w - 2, hz, fg, bg)
        self.vline(x, y + 1, h - 2, vt, fg, bg)
        self.vline(x + w - 1, y + 1, h - 2, vt, fg, bg)
        self.put(x, y, tl, fg, bg)
        self.put(x + w - 1, y, tr, fg, bg)
        self.put(x, y + h - 1, bl, fg, bg)
        self.put(x + w - 1, y + h - 1, br, fg, bg)
        if title:
            t = " %s " % title
            self.text(x + 2, y, t, fg, bg)

    def blit(self, art, x, y, fg=None, bg=None, map_fg=None):
        """Draw a block of text lines.  map_fg(ch) may return per-char color."""
        for j, line in enumerate(art):
            yy = y + j
            if yy < 0 or yy >= self.h:
                continue
            cx = x
            for c in line:
                w = cw(c)
                if w == 0:
                    continue
                if c != " ":
                    cf = map_fg(c, cx - x, j) if map_fg else fg
                    if cx >= 0 and cx < self.w:
                        self.ch[yy][cx] = c
                        self.fg[yy][cx] = cf
                        self.bg[yy][cx] = bg
                        if w == 2 and cx + 1 < self.w:
                            self.ch[yy][cx + 1] = CONT
                            self.fg[yy][cx + 1] = cf
                cx += w
        return x + (sw(art[0]) if art else 0)

    # -- compositing ------------------------------------------------------
    def blend_into(self, other, k, seed=0):
        """Move own cells into `other` with probability k (dissolve)."""
        n = 0
        for y in range(self.h):
            for x in range(self.w):
                c = self.ch[y][x]
                if c == " " or c == CONT:
                    continue
                if h01(x * 7 + 13, y * 11 + 5, seed) < k:
                    other.ch[y][x] = c
                    other.fg[y][x] = self.fg[y][x]
                    other.bg[y][x] = self.bg[y][x]
                    n += 1
        return n

    def overlay(self, other, x=0, y=0):
        """Copy non-blank cells from `other` onto self."""
        self.composite(other, alpha=1.0, ox=x, oy=y)

    # -- wide-char safe cell copying --------------------------------------
    def _place(self, y, x, c, fg, bg):
        """Write one cell, repairing any split double-width neighbours."""
        row = self.ch[y]
        if c == CONT:
            if 0 < x < self.w:
                row[x] = CONT
                self.fg[y][x] = fg
                self.bg[y][x] = bg
            return
        frow = self.fg[y]
        brow = self.bg[y]
        # destination cell is the continuation of a wide char -> free its lead
        if row[x] == CONT and x > 0:
            row[x - 1] = " "
            frow[x - 1] = None
            brow[x - 1] = None
        # destination cell currently leads a wide char -> free its continuation
        if cw(row[x]) == 2 and x + 1 < self.w:
            row[x + 1] = " "
            frow[x + 1] = None
            brow[x + 1] = None
        row[x] = c
        frow[x] = fg
        brow[x] = bg
        if cw(c) == 2 and x + 1 < self.w:
            if cw(row[x + 1]) == 2 and x + 2 < self.w:
                row[x + 2] = " "
                frow[x + 2] = None
                brow[x + 2] = None
            row[x + 1] = CONT
            frow[x + 1] = fg
            brow[x + 1] = bg

    def copy_from(self, src):
        """Exact cell copy (keeps blank cells, so nothing ghosts through)."""
        w = min(self.w, src.w)
        h = min(self.h, src.h)
        for y in range(h):
            self.ch[y][:w] = src.ch[y][:w]
            self.fg[y][:w] = src.fg[y][:w]
            self.bg[y][:w] = src.bg[y][:w]
        for y in range(h, self.h):
            for x in range(self.w):
                self.ch[y][x] = " "
                self.fg[y][x] = None
                self.bg[y][x] = None

    def composite(self, src, alpha=1.0, seed=0, clip=None, ox=0, oy=0):
        """Copy `src` onto self; alpha<1 dissolves cells deterministically."""
        w = min(self.w, src.w + ox)
        h = min(self.h, src.h + oy)
        x0, y0, x1, y1 = clip if clip else (0, 0, w, h)
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(w, x1)
        y1 = min(h, y1)
        for y in range(y0, y1):
            sy = y - oy
            srow = src.ch[sy]
            sfg = src.fg[sy]
            sbg = src.bg[sy]
            dec_prev = False
            for x in range(x0, x1):
                sx = x - ox
                c = srow[sx]
                if c == CONT:
                    # already written together with its lead
                    continue
                if c == " ":
                    dec_prev = False
                    continue
                take = True
                if alpha < 0.995:
                    take = h01(x * 3 + 1, y * 5 + 7, seed) < alpha
                dec_prev = take
                if take:
                    self._place(y, x, c, sfg[sx], sbg[sx])

    def dim(self, k=0.55, grey_k=0.0):
        for y in range(self.h):
            frow = self.fg[y]
            for x in range(self.w):
                c = frow[x]
                if c is not None:
                    c = shade(c, k)
                    if grey_k:
                        c = grey(c, grey_k)
                    frow[x] = c

    def to_text(self):
        out = []
        for y in range(self.h):
            row = []
            for c in self.ch[y]:
                if c == CONT:
                    continue
                row.append(c)
            out.append("".join(row).rstrip())
        return "\n".join(out)


# --------------------------------------------------------------------------
# ANSI output
# --------------------------------------------------------------------------

class Emitter:
    """Converts canvases to ANSI strings for a given color mode."""

    def __init__(self, mode="256"):
        self.mode = mode
        self._q = {}

    def _quant(self, c):
        v = self._q.get(c)
        if v is None:
            r, g, b = c
            if max(r, g, b) - min(r, g, b) < 12:
                # grey ramp
                y = (r + g + b) // 3
                if y < 8:
                    idx = 16
                elif y > 238:
                    idx = 231
                else:
                    idx = 232 + int((y - 8) * 23 / 230)
            else:
                def q(x):
                    if x < 48:
                        return 0
                    if x < 115:
                        return 1
                    return min(5, (x - 35) // 40)
                idx = 16 + 36 * q(r) + 6 * q(g) + q(b)
            v = idx
            self._q[c] = v
        return v

    def _fg(self, c):
        if c is None:
            return "\x1b[39m"
        if self.mode == "rgb":
            return "\x1b[38;2;%d;%d;%dm" % c
        if self.mode == "256":
            return "\x1b[38;5;%dm" % self._quant(c)
        return ""

    def _bg(self, c):
        if c is None:
            return "\x1b[49m"
        if self.mode == "rgb":
            return "\x1b[48;2;%d;%d;%dm" % c
        if self.mode == "256":
            return "\x1b[48;5;%dm" % self._quant(c)
        return ""

    def frame(self, cv, full=False):
        if self.mode == "mono":
            lines = []
            for y in range(cv.h):
                row = []
                for c in cv.ch[y]:
                    if c == CONT:
                        continue
                    row.append(c)
                lines.append("".join(row).rstrip())
            return "\x1b[H" + "\n".join(lines)

        parts = []
        last_fg = object()
        last_bg = object()
        for y in range(cv.h):
            parts.append("\x1b[%d;1H" % (y + 1))
            chrow = cv.ch[y]
            frow = cv.fg[y]
            brow = cv.bg[y]
            fg_run = last_fg
            bg_run = last_bg
            # local cache per row
            q = self._quant if self.mode == "256" else None
            for x in range(cv.w):
                c = chrow[x]
                if c == CONT:
                    continue
                f = frow[x]
                b = brow[x]
                if f is not fg_run or b is not bg_run:
                    # colors are tuples (hashable) or None
                    if f is not fg_run:
                        parts.append("\x1b[39m" if f is None else
                                     ("\x1b[38;2;%d;%d;%dm" % f if self.mode == "rgb"
                                      else "\x1b[38;5;%dm" % q(f)))
                        fg_run = f
                    if b is not bg_run:
                        parts.append("\x1b[49m" if b is None else
                                     ("\x1b[48;2;%d;%d;%dm" % b if self.mode == "rgb"
                                      else "\x1b[48;5;%dm" % q(b)))
                        bg_run = b
                parts.append(c)
        parts.append("\x1b[0m")
        return "\x1b[H" + "".join(parts)


def pick_color_mode(requested="auto"):
    if requested in ("rgb", "256", "mono"):
        return requested
    if os.environ.get("NO_COLOR"):
        return "mono"
    ct = os.environ.get("COLORTERM", "").lower()
    if "truecolor" in ct or "24bit" in ct:
        return "rgb"
    term = os.environ.get("TERM", "")
    if "256" in term or term in ("xterm", "screen", "tmux", "konsole", "alacritty",
                                  "kitty", "wezterm", "xterm-kitty"):
        return "256"
    return "256"
