"""The prompt line does not have to repeat the lyric file verbatim.

This is the machine's *typing*, not the singer's text: where the song
holds a word it cannot let go of, the input line stutters the word an
extra time or two, deletes it back, and types it again -- always on the
beat, always keeping what the line *means* intact.  A few lines are
retyped whole (the command, the accusation), which is the same ritual as
the giant EXECUTION banner in the chant, just at the scale of a hand.

Pure function of time: no state, no randomness.  Every cycle is anchored
to the line's own cue and to the 130 bpm grid, so picture and vocal stay
married.

    apply(en, typed, t, t0, t1, dur, avail) -> (display, active)

`typed` is the base line as far as the typewriter has reached; the
returned string is what the prompt should show this frame, and `active`
is True while the obsession is mid-keystroke (the caller draws the last
glyph as wet ink).
"""

BEAT = 0.46154

# exact english line -> (word, max extra copies, typing speed)
# the word is duplicated in place, after its first occurrence
DUP = {
    # the chant: four sung executions already; the machine adds up to two
    "Execution execution execution execution": ("execution", 2, 26.0),
    # the solo: one sung execution, the line keeps typing it
    "Execution": ("execution", 2, 24.0),
    "If I can give them all the execution": ("execution", 1, 24.0),
    "Then I can be your only execution": ("execution", 2, 24.0),
    "I will run the execution": ("execution", 2, 24.0),
    # the plea: the pronoun it keeps saying
    "If I can have you back": ("you", 2, 22.0),
    # trapped, again and again
    "Though we are trapped": ("trapped", 1, 22.0),
    "We are trapped ah": ("trapped", 1, 22.0),
    "I am trapped": ("trapped", 1, 20.0),
    # the denial the song repeats four times, then admits
    "You have left": ("left", 1, 22.0),
    "You have left me in isolation": ("left", 1, 22.0),
    # the stretched word, sung once more by the hand
    "Trapped in lo-o-ove": ("lo-o-ove", 1, 20.0),
    "If I can feel your vibrations": ("vibrations", 1, 22.0),
}

# whole-line retype: type it, hold, wipe it, type it again
RETYPE = {
    "world.execute(me);": (0.15, 62.0),
    "You have made some illegal arguments": (0.46, 40.0),
}

# lines whose "only" is the film's motif: the prompt writes it [only]
ONLY = {
    "Then I can be your only satisfaction",
    "Then I can be your only execution",
    "If I'm the only god",
}


def _style(s):
    """The [only] motif, applied to whatever has been typed so far."""
    if "only" not in s:
        return s
    return s.replace("only", "[only]")


def _sw(s):
    # one column per glyph everywhere in this renderer
    return len(s)


def _dup_count(i, max_extra):
    """Cycle of extra copies on the beat: 0,1,..,max,..,1, back to 0."""
    if max_extra <= 0:
        return 0, 0
    seq = [0] + list(range(1, max_extra + 1)) + \
        list(range(max_extra - 1, 0, -1))
    cur = seq[i % len(seq)]
    prev = seq[(i - 1) % len(seq)] if i > 0 else 0
    return cur, prev


def _dup(en, t, t0, t1, dur, word, max_extra, cps, avail):
    """Stutter `word` an extra 0..max_extra times, typed on the beat."""
    low = en.lower()
    at = low.find(word)
    if at < 0:
        return en, False
    # do not double a word that is not a whole word
    before = low[at - 1] if at > 0 else " "
    after = low[at + len(word)] if at + len(word) < len(low) else " "
    if before.isalnum() or after.isalnum():
        return en, False
    t_full = t0 + dur
    if t < t_full:
        return en, False
    el = t - t_full
    # short lines get a compressed cycle so the stutter still lands
    step = BEAT if (t1 - t_full) >= 3 * BEAT else max(0.22, (t1 - t_full) / 2.0)
    i = int(el / step)
    frac = el - i * step
    cur, prev = _dup_count(i, max_extra)
    if cur <= 0 and prev <= 0:
        return en, False
    block = " " + word
    if cur >= prev:
        want = cur * len(block)
        got = min(want, int(frac * cps) + 1 + (len(block) if prev else 0))
    else:
        want = prev * len(block)
        got = max(0, want - int(frac * cps))
    if got <= 0:
        return en, False
    ins = (block * max_extra)[:got]
    # if the word closes the line, append; otherwise stutter in place
    end_at = low.rfind(word) + len(word)
    tail = low[end_at:]
    if not tail.strip():
        head, rest = en, ""
        ins = ins.rstrip(" ") if ins.endswith(" ") else ins
        if not ins:
            return en, False
    else:
        head, rest = en[:at + len(word)], en[at + len(word):]
        if ins.endswith(" ") and rest.startswith(" "):
            ins = ins[:-1]
        if not ins:
            return en, False
    out = head + ins + rest
    if _sw(out) > avail:
        return en, False
    active = (got % len(block)) != 0
    return out, active


def _retype(en, t, t0, dur, gap, cps, avail):
    """Type the whole line, hold, wipe it from the right, type it again."""
    t_full = t0 + dur
    hold = BEAT
    if t < t_full + hold:
        return en, False
    # wipe then retype, a breath of silence between
    n = len(en)
    wipe = n / cps
    cycle = wipe + gap + wipe
    ph = (t - (t_full + hold)) % cycle
    if ph < wipe:
        shown = n - int(ph * cps)
        return en[:max(0, shown)], True
    if ph < wipe + gap:
        return "", False
    ph2 = ph - (wipe + gap)
    shown = min(n, int(ph2 * cps) + 1)
    return en[:shown], shown < n


def apply(en, typed, t, t0, t1, dur, avail):
    """Return (display, active) for the prompt line at time t."""
    if not en:
        return typed, False
    disp = _style(typed)
    if typed != en:
        return disp, False
    if en in RETYPE and avail >= len(en):
        gap, cps = RETYPE[en]
        out, act = _retype(en, t, t0, dur, gap, cps, avail)
        if out != en:
            return _style(out), act
        return disp, False
    rule = DUP.get(en)
    if rule:
        out, act = _dup(en, t, t0, t1, dur, rule[0], rule[1], rule[2], avail)
        return _style(out), act
    return disp, False
