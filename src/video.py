#!/usr/bin/env python3
"""Render the MV to a 16:9 MP4.

The player draws to a character grid (see ``mv.compose``); this module turns
that grid into pixels -- one bitmap per character cell -- and pipes raw RGB
frames into ffmpeg, so the video is exactly what the terminal shows.

Grid and geometry
-----------------
``COLS x ROWS`` cells at ``CW x CH`` pixels.  With the Maple Mono NF CN face at
25 px the advance is exactly 15 px and the line box is 34 px, so a cell is
15x34 and the glyphs are neither stretched nor squashed.  128 x 31 cells is
1920 x 1054; the frame is 1920 x 1080 (16:9), the remaining 26 px are split
evenly above and below (black, so invisible on the dark picture).

By default the film is English-only: the Chinese line lives *below* the
frame, and the 31 visible rows are what fits in 16:9.  ``--zh`` adds it: the
grid becomes 32 rows (one scene row traded for the Chinese line,
``h_canvas = ROWS - 1``) and the 34 px of extra height are trimmed from the
black padding top and bottom -- still exactly 1920x1080, cells still 15x34,
and the intro card then says ``中英双语字幕`` instead of ``英文字幕``.

    python3 src/video.py --preview 42,120,155     # a few PNG frames
    python3 src/video.py                          # the whole film
    python3 src/video.py --zh --out out/zh.mp4    # + the Chinese subtitle line
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import mv                                             # noqa: E402
import opts                                           # noqa: E402
from renderer import cw, CONT                         # noqa: E402
from PIL import Image, ImageDraw, ImageFont           # noqa: E402

COLS, ROWS = 128, 31          # visible content rows (canvas is ROWS+1, last blank)
CW, CH = 15, 34               # cell box == Maple Mono's natural cell at 25 px
FONT_SIZE = 25
PAD = 4                       # glyph canvases are padded so overhang isn't cut
FPS = 30
OUT_W, OUT_H = 1920, 1080
DURATION = mv.DURATION
CACHE = os.path.join(ROOT, ".cache")

# ---------------------------------------------------------------- fonts ----
# First font that actually has the glyph wins.  Maple Mono is a monospace face
# with Nerd Font icons *and* CJK, so it carries almost everything and the grid
# stays uniform; the rest are only for stray symbols.
CANDIDATES = [
    ("/usr/share/fonts/maple/MapleMono-NF-CN-Regular.ttf", 0),
    ("/usr/share/fonts/TTF/JetBrainsMonoNLNerdFontMono-Regular.ttf", 0),
    ("/usr/share/fonts/TTF/DejaVuSansMono.ttf", 0),
    ("/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc", 1),
    ("/usr/share/fonts/TTF/DejaVuSans.ttf", 0),
]
CANDIDATES = [c for c in CANDIDATES if os.path.exists(c[0])]

_fonts = {}


def _font(path, index, size=FONT_SIZE):
    key = (path, index, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size, index=index)
    return _fonts[key]


def _raster(font, ch, box):
    im = Image.new("L", box, 0)
    d = ImageDraw.Draw(im)
    d.text((PAD, PAD + font.getmetrics()[0]), ch, font=font, fill=255,
           anchor="ls")
    return im


def _has_glyph(font, ch, tofu, blank):
    b = _raster(font, ch, (FONT_SIZE * 3, FONT_SIZE * 2)).tobytes()
    return b != tofu and b != blank


def build_fontmap(chars, path=os.path.join(CACHE, "fontmap.json")):
    """char -> [font path, index] ; cached on disk because it is slow-ish."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if all(c in data for c in chars):
            return data
    except (OSError, ValueError):
        data = {}
    for p, i in CANDIDATES:
        f = _font(p, i)
        data.setdefault("\0tofu:" + p, None)
        data["\0tofu:" + p] = _raster(f, "\U0010fffd",
                                      (FONT_SIZE * 3, FONT_SIZE * 2)).tobytes().hex()
        data["\0blank:" + p] = _raster(f, "\u0378",
                                       (FONT_SIZE * 3, FONT_SIZE * 2)).tobytes().hex()
    for ch in chars:
        if ch in data and data[ch]:
            continue
        for p, i in CANDIDATES:
            f = _font(p, i)
            tofu = bytes.fromhex(data["\0tofu:" + p])
            blank = bytes.fromhex(data["\0blank:" + p])
            if _has_glyph(f, ch, tofu, blank):
                data[ch] = [p, i]
                break
        else:
            data[ch] = [CANDIDATES[0][0], CANDIDATES[0][1]]
    out = {k: v for k, v in data.items() if not k.startswith("\0")}
    try:
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f)
    except OSError:
        pass
    return out


# ------------------------------------------------------- glyph painting ----
class Painter:
    def __init__(self, fontmap):
        self.fontmap = fontmap
        self.masks = {}       # ch -> L image (padded)
        self.solids = {}      # (rgb, width) -> RGB image

    def resolve(self, ch):
        """Font for a glyph the sampling pass did not see: test the chain."""
        box = (FONT_SIZE * 3, FONT_SIZE * 2)
        for path, index in CANDIDATES:
            font = _font(path, index)
            tofu = _raster(font, "\U0010fffd", box).tobytes()
            blank = _raster(font, "\u0378", box).tobytes()
            if _has_glyph(font, ch, tofu, blank):
                self.fontmap[ch] = [path, index]
                return self.fontmap[ch]
        self.fontmap[ch] = list(CANDIDATES[0])
        return self.fontmap[ch]

    def mask(self, ch):
        m = self.masks.get(ch)
        if m is None:
            if ch not in self.fontmap:
                self.resolve(ch)
            path, index = self.fontmap[ch]
            font = _font(path, index)
            wide = cw(ch) >= 2
            box = (2 * CW + 2 * PAD, CH + 2 * PAD) if wide else \
                  (CW + 2 * PAD, CH + 2 * PAD)
            m = Image.new("L", box, 0)
            ImageDraw.Draw(m).text((PAD, PAD + font.getmetrics()[0]), ch,
                                   font=font, fill=255, anchor="ls")
            if len(self.masks) < 20000:
                self.masks[ch] = m
        return m

    def solid(self, color, width):
        key = (color, width)
        s = self.solids.get(key)
        if s is None:
            s = Image.new("RGB", (width + 2 * PAD, CH + 2 * PAD), color)
            if len(self.solids) < 4000:
                self.solids[key] = s
        return s


def paint(cv, painter, rows=None, img=None):
    """Draw one canvas (chars + colours) into a COLS*CW x rows*CH RGB image."""
    rows = ROWS if rows is None else rows
    img = img or Image.new("RGB", (COLS * CW, rows * CH), (0, 0, 0))
    d = ImageDraw.Draw(img)
    # backgrounds first: one rectangle per run of equal colour
    for y in range(rows):
        bgs = cv.bg[y]
        x = 0
        while x < COLS:
            c = bgs[x]
            if not c:
                x += 1
                continue
            x2 = x + 1
            while x2 < COLS and bgs[x2] == c:
                x2 += 1
            d.rectangle([x * CW, y * CH, x2 * CW - 1, (y + 1) * CH - 1], fill=c)
            x = x2
    # then the glyphs, tinted; painted from the padded canvas so the 1 px
    # overhang of box characters spills over and the rules stay seamless
    for y in range(rows):
        chs = cv.ch[y]
        fgs = cv.fg[y]
        for x in range(COLS):
            ch = chs[x]
            if not ch or ch == " " or ch == CONT:
                continue
            color = fgs[x]
            if not color:
                color = (200, 205, 210)
            wide = cw(ch) >= 2
            m = painter.mask(ch)
            img.paste(painter.solid(color, 2 * CW if wide else CW),
                      (x * CW - PAD, y * CH - PAD), m)
    return img


def frame(t, painter, zh=False):
    """One 1920x1080 frame; zh also draws the Chinese line under the frame."""
    if zh:
        # 32 rows: h_canvas loses one row so the Chinese line gets the last one
        cv, _ = mv.compose(t, COLS, ROWS - 1, ROWS + 1, hint=False)
        img = paint(cv, painter, rows=ROWS + 1)      # 32 * 34 = 1088 -> trim 4+4
    else:
        cv, _ = mv.compose(t, COLS, ROWS, ROWS + 1, hint=False)
        img = paint(cv, painter)                     # 31 * 34 = 1054 -> pad 13+13
    if img.size == (OUT_W, OUT_H):
        return img
    frame_img = Image.new("RGB", (OUT_W, OUT_H), (0, 0, 0))
    frame_img.paste(img, (0, (OUT_H - img.height) // 2))
    return frame_img


# ------------------------------------------------------------- driver ------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="",
                    help="输出路径（默认 out/world-execute-me_16x9_1080p[_zh].mp4）")
    ap.add_argument("--zh", action="store_true",
                    help="把画面下方那行中文字幕也渲进去"
                         "（默认不加：成片只有画面内的英文字幕）")
    ap.add_argument("--audio", default=os.path.join(ROOT, "assets",
                                                    "world-execute-me.m4a"))
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=DURATION)
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--preview", default="",
                    help="comma separated times -> PNG frames, no video")
    ap.add_argument("--preview-dir", default=os.path.join(ROOT, "out"))
    args = ap.parse_args()
    opts.ZH = bool(args.zh)
    if not args.out:
        args.out = os.path.join(ROOT, "out", "world-execute-me_16x9_1080p%s.mp4"
                                % ("_zh" if args.zh else ""))

    chars = set()
    t = args.start
    # collect the glyphs actually used in the rendered range
    while t < args.end:
        cv, _ = mv.compose(t, COLS, ROWS - 1 if args.zh else ROWS, ROWS + 1,
                           hint=False)
        for row in cv.ch:
            chars.update(c for c in row if c and c != " " and c != CONT)
        t += 1.31
    fontmap = build_fontmap(chars)
    painter = Painter(fontmap)

    if args.preview:
        times = [float(x) for x in args.preview.split(",")]
        os.makedirs(args.preview_dir, exist_ok=True)
        for t in times:
            img = frame(t, painter, args.zh)
            p = os.path.join(args.preview_dir, "preview_%06.2f.png" % t)
            img.save(p)
            print("wrote", p, img.size)
        return

    n = int(round((args.end - args.start) * args.fps))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (OUT_W, OUT_H), "-r", str(args.fps), "-i", "-",
           "-i", args.audio,
           "-map", "0:v:0", "-map", "1:a:0",
           "-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
           "-c:a", "copy", "-shortest", "-movflags", "+faststart",
           args.out]
    print("encoding %d frames (%dx%d @ %d fps, %.1f s) -> %s"
          % (n, OUT_W, OUT_H, args.fps, args.end - args.start, args.out))
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    try:
        for i in range(n):
            t = args.start + i / float(args.fps)
            proc.stdin.write(frame(t, painter, args.zh).tobytes())
            if i % 120 == 0:
                el = time.time() - t0
                eta = el / (i + 1) * (n - i - 1)
                sys.stdout.write("\r  %4d/%d  %5.1f%%  %.1f fps  eta %4.0f s   "
                                 % (i + 1, n, 100.0 * (i + 1) / n,
                                    (i + 1) / max(el, 1e-6), eta))
                sys.stdout.flush()
    finally:
        proc.stdin.close()
        rc = proc.wait()
    print("\nffmpeg exit %d, %.1f s wall, %.1f MB"
          % (rc, time.time() - t0,
             os.path.getsize(args.out) / 1e6 if os.path.exists(args.out) else 0))
    return rc


if __name__ == "__main__":
    sys.exit(main() or 0)
