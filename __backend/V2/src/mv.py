#!/usr/bin/env python3
"""world.execute(me); — terminal ASCII music video.

Usage:
    python3 src/mv.py                 # play with audio
    python3 src/mv.py --silent        # no audio (visual check)
    python3 src/mv.py --dump 15,60,147  # dump frames at given seconds
    python3 src/mv.py --info          # print timeline
"""

import argparse
import atexit
import os
import select
import shutil
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import anim
import crt
import energy
import fx
import lyrics
from audio import make_player
from base import Ctx
from renderer import Canvas, Emitter, P, mix, shade, grey, pick_color_mode, cw, sw, h01
from scenes_a import (IntroScene, Verse1Scene, Verse2Scene, Pre1Scene,
                      Chorus1Scene)
from scenes_b import (Verse3Scene, Pre2Scene, Chorus2Scene, BridgeScene,
                      BuildScene, ChantScene, FinalScene, OutroScene,
                      ShutdownScene, EndCardScene)

BPM = lyrics.BPM
BEAT = lyrics.BEAT
HUD_TOTAL = 2  # chinese line + hint row, both below the frame
DURATION = lyrics.DURATION
FADE = 0.62


def build_scenes():
    out = []
    for t0, t1, key, en, zh, accent in lyrics.SECTIONS:
        cls = {
            "intro": IntroScene, "verse1": Verse1Scene, "verse2": Verse2Scene,
            "pre1": Pre1Scene, "chorus1": Chorus1Scene, "verse3": Verse3Scene,
            "pre2": Pre2Scene, "chorus2": Chorus2Scene, "bridge": BridgeScene,
            "build": BuildScene, "chant": ChantScene, "final": FinalScene,
            "outro": OutroScene, "shutdown": ShutdownScene,
            "endcard": EndCardScene,
        }[key]
        s = cls(t0, t1)
        s.key = key
        s.accent = accent
        s.chapter_en = en
        s.chapter_zh = zh
        if key == "verse1":
            # the object-creation montage replays the verse-1 cues during the
            # instrumental break, i.e. one section later than they are sung
            s.cue_off = t0
        out.append(s)
    return out


SCENES = build_scenes()


def scene_index(t):
    lo, hi = 0, len(SCENES) - 1
    idx = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if SCENES[mid].t0 <= t:
            idx = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return idx


def make_ctx(t, w, h):
    bt = (t / BEAT) % 1.0
    return Ctx(t, bt, (t / (BEAT * 4)) % 1.0, energy.at,
               lyrics.section_at(t), w, h)


# --------------------------------------------------------------------------
# frame composition
# --------------------------------------------------------------------------

# how badly the signal is broken at time t (0 clean .. 1 snow)
BURSTS = (
    (0.30, 2.45, 0.95, "ramp"),    # the opening shatters, then locks on
    (14.86, 15.62, 0.75, "hit"),   # the band lands: sync kicks
    (118.28, 118.95, 0.40, "hit"), # bridge opens
    (128.42, 129.30, 0.55, "hit"), # illegal arguments
    (147.55, 148.35, 0.70, "hit"), # EXECUTION
    (158.86, 159.40, 0.45, "hit"), # the counting
    (162.58, 163.30, 0.60, "hit"), # final
    (191.55, 192.45, 0.65, "hit"), # shutdown
    (205.78, 206.90, 0.50, "hit"), # the whisper
)


def glitch_level(t):
    """0..1 — how much CRT damage the current moment deserves."""
    v = 0.0
    if t < 15.0:                      # the boot is a dying signal
        v = max(v, 0.55 * max(0.0, 1.0 - t / 2.6))
    for a, b, k, mode in BURSTS:
        if a <= t < b:
            u = (t - a) / max(1e-6, b - a)
            if mode == "ramp":
                v = max(v, k * (1.0 - u) ** 1.4)
            else:
                v = max(v, k * (1.0 - u) ** 2.0)
    if 133.10 <= t < 147.90:          # build-up: the machine is straining
        v = max(v, 0.18 + 0.42 * (t - 133.10) / 14.80)
    if 196.0 <= t < 205.7:            # long dark: slow drift, weak sync
        v = max(v, 0.10)
    idx = scene_index(t)
    s = SCENES[idx]
    if idx > 0 and t < s.t0 + FADE:   # scene changes tear a little
        v = max(v, 0.30 * (1.0 - (t - s.t0) / FADE))
    return v


def _bed(t, w, h):
    """Empty canvas with the phosphor stipple already laid down."""
    cv = Canvas(w, h)
    crt.ambient(cv, t, P.get("phos", (111, 255, 156)))
    return cv


def render_scene(t, w, h):
    """Render the scene layer (with cross-dissolve at boundaries)."""
    idx = scene_index(t)
    s = SCENES[idx]
    ctx = make_ctx(t, w, h)
    ac = P.get(s.accent, P["phos"])
    cv = Canvas(w, h)
    crt.ambient(cv, t, ac)
    if idx > 0 and t < s.t0 + FADE:
        prev = SCENES[idx - 1]
        cv_under = Canvas(w, h)
        crt.ambient(cv_under, t, ac)
        prev.draw(cv_under, ctx)
        s.draw(cv, ctx)
        k = max(0.0, min(1.0, (t - s.t0) / FADE))
        out = Canvas(w, h)
        if k >= 0.995:
            out.copy_from(cv)
        else:
            # scenes hand off by cell-wise dissolve: the old picture is eaten
            # away while the new one fills the holes (never a muddy alpha mix)
            anim.dissolve_canvases(out, cv_under, cv, k ** 0.85,
                                   seed=(int(s.t0) & 1023) + 7, band=0.20)
    else:
        s.draw(cv, ctx)
        out = cv
    crt.apply(out, t, ac, glitch_level(t), ctx.beat)
    return out, s


def mmss(t):
    t = max(0.0, t)
    return "%02d:%02d" % (int(t) // 60, int(t) % 60)


def draw_border(cv, s, t, w, h, paused=False, audio_desc=""):
    ac = P.get(s.accent, P["phos"])
    line = shade(ac, 0.55)
    cv.put(0, 0, "┌", line)
    cv.put(w - 1, 0, "┐", line)
    cv.put(0, h - 1, "└", line)
    cv.put(w - 1, h - 1, "┘", line)
    for x in range(1, w - 1):
        cv.put(x, 0, "─", line)
    # title
    title = " world.execute(me); "
    show_title = w >= 64
    if show_title:
        cv.text(2, 0, title, mix(P["white"], ac, 0.25))
    # chapter, centered
    chap = " %s · %s " % (s.chapter_en, s.chapter_zh)
    if w >= 84 and sw(chap) + 6 < w - 2 * (len(title) + 2):
        cv.ctext(0, chap, shade(ac, 0.9))
    # time
    ts = " %s / %s " % (mmss(t), mmss(DURATION))
    cv.rtext(0, ts, shade(ac, 0.95), right=w - 2)

    # bottom border doubles as progress bar
    for x in range(1, w - 1):
        cv.put(x, h - 1, "─", shade(ac, 0.3))
    span = w - 6
    k = max(0.0, min(1.0, t / DURATION))
    played = int(span * k)
    x0 = 3
    for i in range(played):
        cv.put(x0 + i, h - 1, "━", shade(ac, 0.85))
    for sec in lyrics.SECTIONS:
        x = x0 + int(span * (sec[0] / DURATION))
        if 0 <= x < w - 2:
            cv.put(x, h - 1, "┃", shade(ac, 0.55))
    ph = x0 + played
    cv.put(min(w - 2, ph), h - 1, "♥", mix(P["rose"], P["white"], 0.25))
    if paused:
        cv.ctext(h - 1, " PAUSED ", P["amber"])


def draw_divider(cv, t, y, w, accent):
    """Rule between picture and prompt — doubles as the status ribbon."""
    if y < 0 or y >= cv.h:
        return
    ac = P.get(accent, P["phos"])
    cv.hline(0, y, w, "─", shade(ac, 0.16))
    cv.put(0, y, "╞", shade(ac, 0.5))
    cv.put(w - 1, y, "╡", shade(ac, 0.5))

    # live level meter, one cell per band
    try:
        e = energy.at(t)
    except Exception:
        e = 0.3
    blocks = "▁▂▃▄▅▆▇█"
    nb = max(5, min(14, (w - 30) // 2))
    for i in range(nb):
        v = e * 0.5 + 0.5 * h01(i, int(t * 14), 91)
        v = min(1.0, max(0.0, v))
        cv.put(2 + i, y, blocks[int(v * 7.99)], shade(ac, 0.22 + 0.6 * v))

    # counters: frame budget, hex address, energy
    if w >= 62:
        lab = " 0x%04X · %2d%% · %4.2f " % ((int(t * 130) & 0xFFFF),
                                            int(e * 100), e)
        x = 3 + nb
        if x + sw(lab) < w - 12:
            cv.text(x, y, lab, shade(ac, 0.30))

    lab = " stdin "
    x = w - 3 - sw(lab)
    if x > 4:
        cv.text(x, y, lab, shade(ac, 0.45))


def draw_input(cv, t, y, w, accent):
    """The prompt line inside the frame: the english lyric types itself."""
    if y < 0 or y >= cv.h:
        return
    ac = P.get(accent, P["phos"])
    cv.fill(0, y, w, 1, " ", None, mix(P["black"], ac, 0.08))
    cv.put(1, y, ">", shade(ac, 0.9))
    x0 = 3
    right_pad = 2
    if w >= 66:
        cv.rtext(y, " ⏎ enter ", shade(P["grey_dim"], 0.65), right=w - 3)
        right_pad = 12
    avail = max(8, w - x0 - right_pad - 1)
    blink = (int(t / 0.46) % 2) == 0
    info = lyrics.line_at(t)
    if not info:
        if w >= 70:
            cv.text(x0 + 2, y, "waiting for input",
                    shade(P["grey_dim"], 0.35))
        cv.put(x0, y, "▮" if blink else "▯", shade(ac, 0.7))
        return
    en, zh, t0, t1, age, remain = info
    dur = max(0.35, min(0.85 * max(0.4, t1 - t0), len(en) / 25.0))
    n = int(len(en) * max(0.0, min(1.0, age / dur)) + 1e-6)
    cut = 0
    while sw(en[cut:n]) > avail and cut < max(0, len(en) - 8):
        cut += 1
    shown = en[cut:n]
    col = shade(mix(P["white"], ac, 0.15),
                0.55 + 0.45 * min(1.0, age / 0.2))
    x = x0
    if cut > 0:
        cv.put(x0, y, "…", shade(P["grey"], 0.5))
        x = x0 + 1
    cv.text(x, y, shown, col)
    if shown and n < len(en):
        # the freshest glyph is almost white, like wet ink
        cv.text(x + sw(shown[:-1]), y, shown[-1],
                mix(P["white"], ac, 0.05))
    cx = x + sw(shown)
    if n >= len(en):
        if w >= 66:
            cv.rtext(y, " ⏎ enter ", shade(ac, 0.95), right=w - 3)
    if cx < w - right_pad - 1 and (blink or n >= len(en)):
        cv.put(cx, y, "▮", mix(P["white"], ac, 0.1))


def draw_zh(cv, t, y, w, accent):
    """The chinese line, outside the frame at the very bottom: appears centred."""
    if y < 0 or y >= cv.h:
        return
    info = lyrics.line_at(t)
    if not info:
        return
    en, zh, t0, t1, age, remain = info
    s = zh
    while sw(s) > w - 6 and len(s) > 4:
        s = s[:-2]
    if not s:
        return
    ac = P.get(accent, P["phos"])
    a_in = min(1.0, age / 0.16)
    a_out = min(1.0, remain / 0.14)
    a = max(0.0, min(a_in, a_out))
    col = mix(P["white"], ac, 0.22)
    col = shade(col, 0.28 + 0.72 * a)
    cv.ctext(y, s, col)


def draw_hint(cv, t, w, h, interactive, audio_desc, paused):
    y = h - 1
    if paused or t < 7.5:
        if interactive:
            msg = "空格 暂停 · ←/→ 快退快进 · Q 退出"
        else:
            msg = "q / ctrl-c 退出"
        if audio_desc:
            msg = "♪ %s   " % audio_desc + msg
        col = shade(P["grey"], 0.75)
        if t > 6.0 and not paused:
            col = shade(col, max(0.0, (7.5 - t) / 1.5))
        # draw over bottom border area inside canvas, small
        cv.ctext(y, " %s " % msg, col)


def compose(t, w, h_canvas, h_total, interactive=False, audio_desc="",
            paused=False, hint=True):
    # frame rows: 0 top border | 1..h-4 picture | h-3 rule | h-2 prompt | h-1 border
    scene_h = max(6, h_canvas - 3)
    cv, s = render_scene(t, w, scene_h)
    full = Canvas(w, h_total)
    for y in range(min(scene_h, h_canvas)):
        full.ch[y] = cv.ch[y][:]
        full.fg[y] = cv.fg[y][:]
        full.bg[y] = cv.bg[y][:]
    draw_border(full, s, t, w, h_canvas, paused, audio_desc)
    draw_divider(full, t, h_canvas - 3, w, s.accent)
    draw_input(full, t, h_canvas - 2, w, s.accent)
    if hint:
        draw_hint(full, t, w, h_canvas + 1, interactive, audio_desc, paused)
    draw_zh(full, t, h_canvas + 1, w, s.accent)
    return full, s


# --------------------------------------------------------------------------
# terminal
# --------------------------------------------------------------------------

class Term:
    def __init__(self):
        self.fd = sys.stdin.fileno() if sys.stdin.isatty() else None
        self.saved = None
        self.atexit_done = False

    def size(self):
        try:
            sz = shutil.get_terminal_size(fallback=(100, 30))
            return sz.columns, sz.lines
        except Exception:
            return 100, 30

    def enter(self):
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H")
        sys.stdout.flush()
        if self.fd is not None:
            try:
                import termios
                import tty
                self.saved = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd)
            except Exception:
                self.saved = None
        atexit.register(self.leave)
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            try:
                signal.signal(sig, self._on_sig)
            except Exception:
                pass

    def _on_sig(self, *_a):
        self.leave()
        os._exit(130)

    def leave(self):
        if self.atexit_done:
            return
        self.atexit_done = True
        try:
            sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
        except Exception:
            pass
        if self.saved is not None:
            try:
                import termios
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
            except Exception:
                pass

    def keys(self):
        """Non-blocking key read; returns list of tokens."""
        if self.fd is None:
            return []
        out = []
        try:
            while select.select([self.fd], [], [], 0)[0]:
                b = os.read(self.fd, 16)
                if not b:
                    break
                s = b.decode("utf-8", "ignore")
                i = 0
                while i < len(s):
                    c = s[i]
                    if c == "\x1b" and i + 2 < len(s) and s[i + 1] == "[":
                        seq = s[i:i + 3]
                        out.append({"A": "up", "B": "down", "C": "right",
                                    "D": "left"}.get(s[i + 2], "esc"))
                        i += 3
                    else:
                        out.append(c)
                        i += 1
        except Exception:
            pass
        return out


# --------------------------------------------------------------------------
# dump mode (QA)
# --------------------------------------------------------------------------

def dump_times(spec, w, h_canvas, h_total):
    times = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            a, b = part.split(":")
            step = 1.0
            if "/" in b:
                b, st = b.split("/")
                step = float(st)
            v = float(a)
            while v <= float(b) + 1e-9:
                times.append(v)
                v += step
        else:
            times.append(float(part))
    for t in times:
        full, s = compose(t, w, h_canvas, h_total, interactive=False, hint=False)
        print("=" * w)
        print("### t=%.2f  scene=%s  %s / %s" % (t, s.key, s.chapter_en, s.chapter_zh))
        print("=" * w)
        print(full.to_text())
        info = lyrics.line_at(t)
        if info:
            print("--- zh: %s" % info[1])
            print("--- en: %s" % info[0])
        else:
            print("--- (no lyric)")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def find_audio(explicit=None):
    cands = []
    if explicit:
        cands.append(explicit)
    cands += [
        os.path.join(ROOT, "assets", "world-execute-me.m4a"),
        os.path.join(ROOT, "world.execute(me);-Mili.mp4"),
        os.path.join(ROOT, "world.execute(me);-Mili.m4a"),
        os.path.join(ROOT, "world.execute(me);-Mili.mp3"),
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="world.execute(me); — terminal ASCII music video")
    ap.add_argument("--silent", action="store_true", help="no audio, just visuals")
    ap.add_argument("--fps", type=float, default=20.0)
    ap.add_argument("--start", type=float, default=0.0, help="start time (s)")
    ap.add_argument("--audio", default=None, help="audio file path")
    ap.add_argument("--player", default=None,
                    choices=["mpv_ipc", "mpv", "ffplay", "mpg123", "paplay",
                             "silent"])
    ap.add_argument("--volume", type=int, default=100)
    ap.add_argument("--color", default="auto",
                    choices=["auto", "rgb", "256", "mono"])
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--dump", default=None,
                    help="render frames at times (e.g. 15,60 or 0:20/2)")
    ap.add_argument("--dump-size", default="100x30")
    ap.add_argument("--info", action="store_true", help="print timeline")
    ap.add_argument("--no-hud", action="store_true")
    ap.add_argument("--offset", type=float, default=0.0,
                    help="subtitle timing offset in seconds")
    args = ap.parse_args(argv)

    if args.info:
        print("BPM %.1f  beat %.4fs  bar %.4fs  duration %.2fs"
              % (BPM, BEAT, BEAT * 4, DURATION))
        print("\nsections:")
        for t0, t1, key, en, zh, acc in lyrics.SECTIONS:
            print("  %7.2f - %7.2f  %-10s %-24s %s" % (t0, t1, key, en, zh))
        print("\nlyrics (%d lines):" % len(lyrics.LINES))
        for t0, t1, en, zh in lyrics.LINES:
            print("  %7.2f  %-52s %s" % (t0, en, zh))
        return 0

    if args.offset:
        # apply a subtitle-only offset by shifting lookup time
        _orig = lyrics.line_at
        lyrics.line_at = lambda t, _o=_orig: _orig(t + args.offset)

    if args.dump:
        try:
            dw, dh = args.dump_size.lower().split("x")
            w, htot = int(dw), int(dh)
        except ValueError:
            w, htot = 100, 30
        hcan = htot - HUD_TOTAL
        dump_times(args.dump, w, hcan, htot)
        return 0

    mode = "mono" if args.mono else pick_color_mode(args.color)
    emit = Emitter(mode)

    term = Term()
    tw, th = term.size()
    if args.width:
        tw = args.width
    if args.height:
        th = args.height
    if tw < 48 or th < 14:
        print("终端太小 (需要至少 48x14)，当前 %dx%d" % (tw, th), file=sys.stderr)
        return 2

    hcan = max(10, th - HUD_TOTAL)

    audio_path = None if args.silent else find_audio(args.audio)
    if not args.silent and not audio_path:
        print("找不到音频文件，改为无声播放。", file=sys.stderr)

    if args.silent or not audio_path:
        player, desc = make_player(None, DURATION, args.start, force="silent")
    else:
        player, desc = make_player(audio_path, DURATION, args.start,
                                   args.volume, args.player)

    # restore the terminal even if we are killed by a signal
    def _sig(signum, frame):
        raise KeyboardInterrupt
    for _s in ("SIGTERM", "SIGHUP", "SIGQUIT"):
        try:
            signal.signal(getattr(signal, _s), _sig)
        except (AttributeError, ValueError):
            pass

    term.enter()
    paused = False
    last_size = (tw, th)
    frame_dt = 1.0 / max(4.0, min(60.0, args.fps))
    next_tick = time.monotonic()
    frames = 0
    try:
        while True:
            t = player.time()
            if player.finished() or t > DURATION + 0.35:
                break
            # resize
            frames += 1
            if frames % 10 == 0:
                sz = term.size()
                if (sz[0], sz[1]) != last_size:
                    last_size = (sz[0], sz[1])
                    tw = args.width or sz[0]
                    th = args.height or sz[1]
                    hcan = max(10, th - HUD_TOTAL)
                    sys.stdout.write("\x1b[2J")
            full, s = compose(t, tw, hcan, th, interactive=(term.fd is not None),
                              audio_desc=desc, paused=paused)
            buf = emit.frame(full)
            sys.stdout.write(buf)
            sys.stdout.flush()
            frames = frames
            # keys
            for k in term.keys():
                if k in ("q", "Q", "\x03", "esc"):
                    raise KeyboardInterrupt
                if k == " ":
                    player.pause()
                    paused = not paused
                elif k == "left":
                    player.seek(-5.0)
                elif k == "right":
                    player.seek(5.0)
                elif k == "up":
                    player.seek(30.0)
                elif k == "down":
                    player.seek(-30.0)
            # pacing
            next_tick += frame_dt
            now = time.monotonic()
            if next_tick > now:
                time.sleep(min(0.25, next_tick - now))
            else:
                next_tick = now
    except KeyboardInterrupt:
        pass
    finally:
        try:
            player.close()
        except Exception:
            pass
        term.leave()
    return 0


if __name__ == "__main__":
    sys.exit(main())
