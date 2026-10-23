"""Audio playback with clock synchronisation.

Backends, best first:

  mpv_ipc   mpv with --input-ipc-server; the clock is mpv's own time-pos, so
            seeking / pausing inside mpv is reflected in the visuals and we can
            forward our own keys (space / arrows / q) to it.
  mpv       mpv subprocess, clock = monotonic minus measured spawn latency.
  ffplay    same, ffplay -nodisp -autoexit.
  mpg123    same.
  paplay    raw-ish wav playback (we transcode a wav beside the m4a once).
  silent    no audio at all; clock = monotonic.  Used for previews & tests.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

MPV_CANDIDATES = ("mpv", "/usr/bin/mpv", "/usr/local/bin/mpv")


def _which(cmd):
    p = shutil.which(cmd)
    if p:
        return p
    if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
        return cmd
    return None


class Player:
    duration = None

    def time(self):
        raise NotImplementedError

    def finished(self):
        return False

    def pause(self):
        pass

    def seek(self, dt):
        pass

    def set_pause(self, value=None):
        pass

    def close(self):
        pass


class SilentPlayer(Player):
    def __init__(self, duration, start=0.0):
        self.duration = duration
        self.t0 = time.monotonic() - start
        self._paused = False
        self._paused_at = None
        self._base = start

    def time(self):
        if self._paused:
            return self._paused_at
        return self._base + (time.monotonic() - self.t0)

    def pause(self):
        if self._paused:
            self._base = self._paused_at
            self.t0 = time.monotonic()
            self._paused = False
        else:
            self._paused_at = self.time()
            self._paused = True

    def seek(self, dt):
        self._base = max(0.0, min(self.duration - 0.2, self.time() + dt))
        self.t0 = time.monotonic()
        if self._paused:
            self._paused_at = self._base

    def finished(self):
        return self.time() > self.duration


class MpvIPC(Player):
    """Full-featured: mpv on a unix socket, we poll time-pos."""

    def __init__(self, path, duration, start=0.0, volume=100):
        self.duration = duration
        self.exe = _which("mpv")
        if not self.exe:
            raise RuntimeError("mpv not found")
        self.sockdir = tempfile.mkdtemp(prefix="wexec-")
        self.sockpath = os.path.join(self.sockdir, "mpv.sock")
        args = [
            self.exe, path,
            "--no-video", "--no-audio-display", "--no-terminal",
            "--really-quiet",
            "--input-ipc-server=" + self.sockpath,
            "--pause",
            "--volume=%d" % volume,
            "--start=%.3f" % start if start > 0 else "--start=0",
        ]
        self.proc = subprocess.Popen(args, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        self.sock = None
        self.buf = b""
        self.req = 0
        self._pos = start
        self._ok = False
        self._paused_by_us = True
        self._deadline = time.monotonic() + 8.0
        self._last_query = 0.0
        self._eof = False
        # wait for socket
        while time.monotonic() < self._deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("mpv exited early")
            if os.path.exists(self.sockpath):
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.settimeout(1.0)
                    s.connect(self.sockpath)
                    s.setblocking(False)
                    self.sock = s
                    break
                except OSError:
                    pass
            time.sleep(0.02)
        if self.sock is None:
            self.close()
            raise RuntimeError("mpv ipc timeout")
        # subscribe to events we care about
        self._send({"command": ["observe_property", 1, "eof-reached"]})
        self._send({"command": ["observe_property", 2, "pause"]})
        # unpause once we have a valid position
        for _ in range(60):
            self._query()
            if self._pos is not None:
                break
            time.sleep(0.02)
        self._send({"command": ["set_property", "pause", False]})
        self._paused_by_us = False

    # -- ipc plumbing -----------------------------------------------------
    def _send(self, obj):
        if not self.sock:
            return
        self.req += 1
        obj = dict(obj)
        obj.setdefault("request_id", self.req)
        try:
            self.sock.sendall((json.dumps(obj) + "\n").encode())
        except OSError:
            pass

    def _drain(self):
        if not self.sock:
            return
        try:
            while True:
                chunk = self.sock.recv(65536)
                if not chunk:
                    self._eof = True
                    break
                self.buf += chunk
        except BlockingIOError:
            pass
        except OSError:
            self._eof = True
        while b"\n" in self.buf:
            line, self.buf = self.buf.split(b"\n", 1)
            if not line.strip():
                continue
            try:
                msg = json.loads(line.decode("utf-8", "replace"))
            except ValueError:
                continue
            if "error" in msg and msg.get("error") == "success":
                d = msg.get("data")
                if isinstance(d, (int, float)):
                    self._pos = float(d)
            ev = msg.get("event")
            if ev == "property-change":
                name = msg.get("name")
                if name == "eof-reached" and msg.get("data"):
                    self._eof = True
                elif name == "pause":
                    self._pos_paused = bool(msg.get("data"))

    def _query(self):
        self._send({"command": ["get_property", "time-pos"]})
        self._drain()

    # -- player api -------------------------------------------------------
    def time(self):
        now = time.monotonic()
        if now - self._last_query > 0.035:
            self._last_query = now
            self._query()
        return self._pos if self._pos is not None else 0.0

    def finished(self):
        if self.proc.poll() is not None:
            return True
        if self._eof:
            return True
        p = self._pos
        return p is not None and p >= self.duration - 0.05

    def pause(self):
        self._send({"command": ["cycle", "pause"]})

    def seek(self, dt):
        self._send({"command": ["seek", dt, "relative+exact"]})

    def close(self):
        try:
            if self.sock:
                self._send({"command": ["quit"]})
                self.sock.close()
        except OSError:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=1.5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        try:
            os.unlink(self.sockpath)
        except OSError:
            pass
        try:
            os.rmdir(self.sockdir)
        except OSError:
            pass


class PipePlayer(Player):
    """mpv/ffplay/mpg123/paplay + monotonic clock with spawn compensation."""

    def __init__(self, path, duration, start=0.0, volume=100):
        self.duration = duration
        self.kind = None
        self.proc = None
        cmds = []
        mpv = _which("mpv")
        if mpv:
            cmds.append(("mpv", [mpv, path, "--no-video", "--no-terminal",
                                 "--really-quiet", "--volume=%d" % volume]
                         + (["--start=%.3f" % start] if start > 0 else [])))
        ffplay = _which("ffplay")
        if ffplay:
            cmds.append(("ffplay", [ffplay, "-nodisp", "-autoexit",
                                    "-loglevel", "quiet", "-volume", str(volume),
                                    "-ss", "%.3f" % start, path]))
        mpg123 = _which("mpg123")
        if mpg123:
            cmds.append(("mpg123", [mpg123, "-q", path]))
        paplay = _which("paplay")
        wav = _wav_cache(path)
        if paplay and wav:
            cmds.append(("paplay", [paplay, wav]))
        for kind, cmd in cmds:
            try:
                self.proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL,
                                             stderr=subprocess.DEVNULL)
                self.kind = kind
                break
            except OSError:
                continue
        if not self.proc:
            raise RuntimeError("no audio player available")
        self.t0 = time.monotonic()
        self.base = start
        # spawn latency: players need a moment before sound actually starts
        self.comp = {"mpv": 0.22, "ffplay": 0.42, "mpg123": 0.18,
                     "paplay": 0.12}.get(self.kind, 0.3)
        self._paused = False
        self._paused_at = None

    def time(self):
        if self._paused:
            return self._paused_at
        t = self.base + (time.monotonic() - self.t0) - self.comp
        return max(0.0, t)

    def pause(self):
        # cannot pause the child reliably; pause the clock only
        if self._paused:
            self.base = self._paused_at
            self.t0 = time.monotonic()
            self._paused = False
        else:
            self._paused_at = self.time()
            self._paused = True

    def seek(self, dt):
        # not supported without ipc; restart from scratch is out of scope
        pass

    def finished(self):
        if self.proc.poll() is not None:
            return True
        return self.time() > self.duration

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=1.0)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


_WAV_CACHE = {}


def _wav_cache(path):
    """Best effort: transcode to wav for paplay (once)."""
    if path in _WAV_CACHE:
        return _WAV_CACHE[path]
    out = None
    ff = _which("ffmpeg")
    if ff:
        try:
            tmp = os.path.join(tempfile.gettempdir(),
                               "wexec-%d.wav" % (hash(path) & 0xFFFFFFF))
            if not os.path.exists(tmp):
                subprocess.run([ff, "-v", "error", "-y", "-i", path,
                                "-ac", "2", "-ar", "44100", tmp],
                               check=True, timeout=90)
            out = tmp
        except Exception:
            out = None
    _WAV_CACHE[path] = out
    return out


def make_player(path, duration, start=0.0, volume=100, force=None):
    """Try backends in order, return (player, description)."""
    order = ["mpv_ipc", "mpv", "ffplay", "mpg123", "paplay", "silent"]
    if force:
        order = [force]
    errs = []
    for kind in order:
        try:
            if kind == "mpv_ipc":
                if not path:
                    raise RuntimeError("no audio file")
                return MpvIPC(path, duration, start, volume), "mpv (ipc, seekable)"
            if kind == "mpv":
                if not path:
                    raise RuntimeError("no audio file")
                p = PipePlayer(path, duration, start, volume)
                return p, "%s (clock sync)" % p.kind
            if kind == "ffplay":
                if not path:
                    raise RuntimeError("no audio file")
                p = PipePlayer(path, duration, start, volume)
                if p.kind != "ffplay":
                    p.close()
                    raise RuntimeError("ffplay not used")
                return p, "ffplay (clock sync)"
            if kind == "mpg123":
                if not path:
                    raise RuntimeError("no audio file")
                p = PipePlayer(path, duration, start, volume)
                if p.kind != "mpg123":
                    p.close()
                    raise RuntimeError("mpg123 not used")
                return p, "mpg123 (clock sync)"
            if kind == "paplay":
                p = PipePlayer(path, duration, start, volume)
                if p.kind != "paplay":
                    p.close()
                    raise RuntimeError("paplay not used")
                return p, "paplay (clock sync)"
            if kind == "silent":
                return SilentPlayer(duration, start), "silent"
        except Exception as e:  # noqa
            errs.append("%s: %s" % (kind, e))
    return SilentPlayer(duration, start), "silent (%s)" % "; ".join(errs)
