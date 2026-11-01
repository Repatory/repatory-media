#!/usr/bin/env python3
"""Build the Repatory sound-effect pack (synthesized, no licensing issues).

    python3 sfx_make.py <out_dir>

Writes 48 kHz mono WAVs, each peak-normalized to -3 dBFS. sfx_mix.py sets the
real level, so these are deliberately "hot" source files.
Needs only numpy (+ the stdlib wave module).
"""
import os, sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a, r, shape=2.0):
    """attack/decay envelope in seconds over n samples."""
    x = np.arange(n) / SR
    e = np.minimum(1, x / max(a, 1e-4))
    tail = np.clip((x - a) / max(r, 1e-4), 0, 1)
    return e * (1 - tail) ** shape


def bandnoise(n, lo, hi):
    """noise band-limited in the frequency domain (lo/hi may be arrays for sweeps is not needed here)."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, n)


def sweep_noise(d, f0, f1, q=0.35):
    """noise through a moving band-pass (a whoosh), done in short overlapping frames."""
    n = int(SR * d); out = np.zeros(n); hop = 512; win = np.hanning(hop * 2)
    src = rng.standard_normal(n + hop * 2)
    for i in range(0, n, hop):
        c = f0 * (f1 / f0) ** (i / n)
        seg = src[i:i + hop * 2] * win
        X = np.fft.rfft(seg); f = np.fft.rfftfreq(len(seg), 1 / SR)
        X *= np.exp(-((np.log(f + 1) - np.log(c)) ** 2) / (2 * q ** 2))
        y = np.fft.irfft(X, len(seg)) * win
        j = min(n, i + hop * 2); out[i:j] += y[:j - i]
    return out


def norm(x, peak_db=-3.0):
    x = x - np.mean(x)
    fade = min(len(x), int(0.004 * SR))
    x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)


def save(d, name, x):
    with wave.open(os.path.join(d, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def main(d):
    os.makedirs(d, exist_ok=True)
    # soft whoosh for a big cut (0.45 s, rises then falls)
    n = int(SR * .45); w = sweep_noise(.45, 300, 2400) * env(n, .30, .15, 1.5)
    save(d, "whoosh_soft", norm(w))
    # short swish for a quick cut (0.22 s)
    n = int(SR * .22); w = sweep_noise(.22, 900, 4500, .45) * env(n, .08, .14, 2)
    save(d, "whoosh_short", norm(w))
    # card pop: tiny sine blip with a pitch drop (for an on-screen card appearing)
    x = t(.09); f = 900 * np.exp(-x * 18)
    p = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), .002, .085, 3)
    save(d, "pop_card", norm(p))
    # soft tick (caption/table row)
    x = t(.04); k = bandnoise(len(x), 2500, 7000) * env(len(x), .0005, .035, 4)
    save(d, "tick", norm(k))
    # plate clank: inharmonic metal partials + a short noise transient
    x = t(.9); parts = [(523, 1), (1187, .6), (1840, .45), (2711, .3), (3990, .18)]
    m = sum(a * np.sin(2 * np.pi * fr * x + rng.uniform(0, 6)) * np.exp(-x * (5 + fr / 600)) for fr, a in parts)
    m[: int(.01 * SR)] += bandnoise(int(.01 * SR), 1500, 9000) * 1.5
    save(d, "plate_clank", norm(m))
    # dumbbell/bar set-down thud: low sine knock + a little body noise
    x = t(.35); f = 95 * np.exp(-x * 6)
    th = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), .002, .3, 2.5)
    th += bandnoise(len(x), 80, 900) * env(len(x), .001, .08, 3) * .5
    save(d, "rack_thud", norm(th))
    # breath in through the nose (0.5 s), for a gap between voice lines
    n = int(SR * .5); b = bandnoise(n, 600, 5500) * env(n, .32, .18, 1.2)
    b *= 1 + .3 * np.sin(2 * np.pi * 3 * t(.5))
    save(d, "breath_in", norm(b))
    # short exhale after effort (0.6 s)
    n = int(SR * .6); b = bandnoise(n, 250, 3500) * env(n, .04, .56, 1.6)
    save(d, "exhale", norm(b))
    # low soft impact for a reveal (0.8 s)
    x = t(.8); f = 60 * np.exp(-x * 1.5)
    im = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(x), .004, .75, 2)
    im += bandnoise(len(x), 40, 400) * env(len(x), .002, .2, 3) * .4
    save(d, "impact_low", norm(im))
    print("wrote", sorted(os.listdir(d)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sfx")
