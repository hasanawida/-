#!/usr/bin/env python3
"""
sfx_gen.py — free, procedural sound design (numpy → wav). No downloads, no licenses.

  SFX  (one per entrance animation, auto-wired by assemble.py when beats.json has no "sfx"):
       pop      soft paper "plop" with a tiny click
       slam     low thud + paper slap  (headlines)
       stamp    rubber-stamp thump
       draw     marker scribble        (circle / arrow / underline)
       fade     short paper whoosh     (tape, fades)
       slide    whoosh with a stop
  MUSIC ("music": {"path": "auto"}): a quiet investigative underscore — low drone, slow chord
       movement, a soft ticking pulse — long enough to loop under a 3-minute film.

usage: python3 scripts/sfx_gen.py <out_dir> [--music seconds]
"""
import argparse
import math
import os
import wave

import numpy as np

SR = 48000


def _write(path, sig, gain=0.9):
    sig = np.asarray(sig, dtype=np.float64)
    peak = np.max(np.abs(sig)) or 1.0
    sig = sig / peak * gain
    pcm = (np.clip(sig, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return path


def _env(n, a=0.002, d=0.1, s=0.0, r=0.05):
    """ADSR in seconds → array of length n."""
    t = np.arange(n) / SR
    total = n / SR
    env = np.ones(n) * s
    env[t < a] = t[t < a] / a
    m = (t >= a) & (t < a + d)
    env[m] = 1 - (1 - s) * (t[m] - a) / d
    rel = t > total - r
    env[rel] *= np.clip((total - t[rel]) / r, 0, 1)
    return env


def _noise(n, seed=0):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _lowpass(x, cutoff):
    """One-pole lowpass (cheap, fine for sfx)."""
    rc = 1.0 / (2 * math.pi * cutoff)
    a = (1 / SR) / (rc + 1 / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def _bandpass(x, lo, hi):
    return _lowpass(x, hi) - _lowpass(x, lo)


def pop():
    n = int(SR * 0.18)
    t = np.arange(n) / SR
    sweep = np.sin(2 * math.pi * (420 - 260 * t / 0.18) * t) * _env(n, 0.001, 0.12, 0, 0.04)
    click = _noise(int(SR * 0.012), 1) * _env(int(SR * 0.012), 0.0005, 0.01, 0, 0.002)
    out = sweep * 0.8
    out[:len(click)] += click * 0.5
    return out


def slam():
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    thud = np.sin(2 * math.pi * (90 * np.exp(-t * 9) + 45) * t) * _env(n, 0.001, 0.25, 0, 0.05)
    slap = _bandpass(_noise(n, 2), 600, 4000) * _env(n, 0.001, 0.06, 0, 0.02)
    return thud * 1.0 + slap * 0.55


def stamp():
    n = int(SR * 0.22)
    t = np.arange(n) / SR
    thump = np.sin(2 * math.pi * (140 * np.exp(-t * 14) + 60) * t) * _env(n, 0.001, 0.16, 0, 0.04)
    paper = _lowpass(_noise(n, 3), 2500) * _env(n, 0.001, 0.04, 0, 0.01)
    return thump + paper * 0.35


def draw(dur=0.55):
    n = int(SR * dur)
    t = np.arange(n) / SR
    scribble = _bandpass(_noise(n, 4), 1200, 6000)
    wob = 0.6 + 0.4 * np.sin(2 * math.pi * 11 * t)          # marker strokes
    return scribble * wob * _env(n, 0.02, dur * 0.7, 0.35, 0.08) * 0.7


def whoosh(dur=0.35, stop=False):
    n = int(SR * dur)
    t = np.arange(n) / SR
    x = _bandpass(_noise(n, 5), 300, 2500)
    env = np.sin(math.pi * t / dur) ** 1.5
    out = x * env
    if stop:
        k = int(SR * 0.03)
        out[-k:] += _noise(k, 6) * np.linspace(1, 0, k) * 0.5
    return out * 0.6


MOODS = {
    #            root  chords (semitone triads rel. to root)        bpm  tick  arp   bright  swell
    "investigative": dict(root=55.0, prog=[(0, 3, 7), (-4, 0, 3), (-7, -4, 0), (-5, -1, 2)], bpm=72, tick=0.35, arp=0.0, bright=0.4, minor=True),
    "tense":         dict(root=51.9, prog=[(0, 3, 7), (1, 4, 8), (0, 3, 6), (-2, 1, 5)], bpm=96, tick=0.5, arp=0.0, bright=0.3, minor=True),
    "hopeful":       dict(root=65.4, prog=[(0, 4, 7), (5, 9, 12), (-3, 0, 4), (7, 11, 14)], bpm=84, tick=0.15, arp=0.25, bright=0.8, minor=False),
    "upbeat":        dict(root=73.4, prog=[(0, 4, 7), (-5, -1, 2), (5, 9, 12), (7, 11, 14)], bpm=112, tick=0.45, arp=0.5, bright=0.9, minor=False),
    "epic":          dict(root=49.0, prog=[(0, 3, 7), (-4, 0, 3), (5, 8, 12), (7, 10, 14)], bpm=64, tick=0.25, arp=0.0, bright=0.6, minor=True),
    "calm":          dict(root=65.4, prog=[(0, 4, 7), (-3, 0, 4), (5, 9, 12), (-5, -1, 2)], bpm=60, tick=0.0, arp=0.15, bright=0.7, minor=False),
    "tech":          dict(root=58.3, prog=[(0, 3, 7), (0, 3, 7), (-2, 1, 5), (-4, 0, 3)], bpm=100, tick=0.3, arp=0.7, bright=0.5, minor=True),
    "kids":          dict(root=78.0, prog=[(0, 4, 7), (5, 9, 12), (7, 11, 14), (0, 4, 7)], bpm=104, tick=0.2, arp=0.6, bright=1.0, minor=False),
}


def _hz(root, semis):
    return root * (2 ** (semis / 12))


def music(seconds=200, seed=0, mood="investigative"):
    """Procedural underscore in a chosen mood: drone + slow chord pads (+ arpeggio) + tick pulse."""
    M = MOODS.get(mood, MOODS["investigative"])
    n = int(SR * seconds)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    root = M["root"]
    # drone (root + octave + fifth) — quieter for bright moods
    for semis, g in ((-12, 0.32), (0, 0.22), (0.05, 0.1), (7, 0.05 if M["minor"] else 0.08)):
        out += np.sin(2 * math.pi * _hz(root, semis) * t + rng.uniform(0, 6)) * g * (1.1 - M["bright"] * 0.5)
    bar = 60 / M["bpm"] * 8
    for i in range(int(seconds / bar) + 1):
        c = M["prog"][i % len(M["prog"])]
        s0, s1 = int(i * bar * SR), min(n, int((i + 1) * bar * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        env = np.minimum(1, tt / 1.2) * np.minimum(1, (bar - tt) / 1.2)
        pad = np.zeros(s1 - s0)
        for k, semis in enumerate(c):
            f = _hz(root, semis + 12)
            wobble = 0.5 + 0.5 * np.sin(2 * math.pi * 0.07 * tt + k)
            pad += np.sin(2 * math.pi * f * tt) * wobble
            pad += np.sin(2 * math.pi * f * 2 * tt) * wobble * 0.25 * M["bright"]     # brightness harmonic
        out[s0:s1] += pad * env * 0.06
        if M["arp"] > 0:   # plucky arpeggio, 8ths
            step = 60 / M["bpm"] / 2
            k = 0
            while k * step < bar:
                a0 = s0 + int(k * step * SR)
                ln = int(SR * 0.18)
                if a0 + ln >= n:
                    break
                f = _hz(root, c[k % 3] + 24)
                ta = np.arange(ln) / SR
                out[a0:a0 + ln] += np.sin(2 * math.pi * f * ta) * np.exp(-ta * 22) * 0.12 * M["arp"]
                k += 1
    if M["tick"] > 0:
        beat = 60 / M["bpm"]
        tick = _bandpass(_noise(int(SR * 0.03), 9), 1500, 5000) * _env(int(SR * 0.03), 0.0005, 0.025, 0, 0.004)
        for i in range(int(seconds / beat)):
            p = int(i * beat * SR)
            if p + len(tick) < n:
                out[p:p + len(tick)] += tick * M["tick"] * (1.0 if i % 4 == 0 else 0.5)
    out *= 0.8 + 0.2 * np.sin(2 * math.pi * t / 32)
    return out


def generate_all(out_dir, music_seconds=None, mood="investigative"):
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "pop": _write(os.path.join(out_dir, "pop.wav"), pop(), 0.6),
        "slam": _write(os.path.join(out_dir, "slam.wav"), slam(), 0.8),
        "stamp": _write(os.path.join(out_dir, "stamp.wav"), stamp(), 0.8),
        "draw": _write(os.path.join(out_dir, "draw.wav"), draw(), 0.45),
        "fade": _write(os.path.join(out_dir, "fade.wav"), whoosh(0.3), 0.4),
        "slide_l": _write(os.path.join(out_dir, "slide.wav"), whoosh(0.4, True), 0.5),
    }
    for k in ("slide_r", "slide_up", "slide_down"):
        paths[k] = paths["slide_l"]
    paths["transition"] = _write(os.path.join(out_dir, "transition.wav"), whoosh(0.5, True), 0.55)
    if music_seconds:
        paths["music"] = _write(os.path.join(out_dir, f"underscore_{mood}.wav"), music(music_seconds, mood=mood), 0.7)
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--music", type=float, default=None)
    ap.add_argument("--mood", default="investigative", help="|".join(MOODS))
    a = ap.parse_args()
    print(generate_all(a.out_dir, a.music, a.mood))
