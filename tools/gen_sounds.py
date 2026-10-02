#!/usr/bin/env python3
"""Generate the Tidepool sound packs as small 16-bit mono WAV files.

    python3 tools/gen_sounds.py

Writes sounds/<pack>/<name>.wav. Standard library only. Edit the PACKS table to
change a pack's character, or add a folder of your own WAVs named like the others.
"""
import math
import os
import random
import struct
import wave

RATE = 44100
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")

# Note frequencies (Hz)
C4, E4, G4 = 261.63, 329.63, 392.00
C5, E5, G5, A5, B5 = 523.25, 659.25, 783.99, 880.00, 987.77
C6, E6 = 1046.50, 1318.51


def osc(kind, phase):
    """One cycle of a waveform at phase 0..1."""
    if kind == "sine":
        return math.sin(2 * math.pi * phase)
    if kind == "square":
        return 1.0 if phase < 0.5 else -1.0
    if kind == "pulse":
        return 1.0 if phase < 0.25 else -1.0
    if kind == "triangle":
        return 4 * abs(phase - 0.5) - 1
    raise ValueError(kind)


def tone(freq, dur, kind="sine", vol=0.4, decay=0.25, attack=0.004,
         slide_to=None, partials=None):
    """A decaying note. partials is a list of (ratio, amplitude) added on top."""
    n = int(RATE * dur)
    out = []
    phase = 0.0
    parts = partials or [(1.0, 1.0)]
    for i in range(n):
        t = i / RATE
        f = freq if slide_to is None else freq + (slide_to - freq) * (i / n)
        phase += f / RATE
        env = math.exp(-t / decay) * min(1.0, t / attack)
        # short fade-out so the file never ends on a click
        tail = min(1.0, (n - i) / (RATE * 0.01))
        s = sum(a * osc(kind, (phase * r) % 1.0) for r, a in parts)
        out.append(vol * env * tail * s / sum(a for _, a in parts))
    return out


def noise(dur, vol=0.3, decay=0.02):
    n = int(RATE * dur)
    rnd = random.Random(7)
    return [vol * math.exp(-(i / RATE) / decay) * (rnd.random() * 2 - 1) for i in range(n)]


def mix(events, total):
    """events: list of (start_seconds, samples)."""
    buf = [0.0] * int(RATE * total)
    for start, samples in events:
        o = int(RATE * start)
        for i, v in enumerate(samples):
            if o + i < len(buf):
                buf[o + i] += v
    peak = max(1e-9, max(abs(v) for v in buf))
    scale = min(1.0, 0.8 / peak)
    return [v * scale for v in buf]


def save(pack, name, samples):
    d = os.path.join(ROOT, pack)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in samples))
    return path


# Each pack builds the same six sounds with its own voice.
def soft():
    p = [(1.0, 1.0), (2.0, 0.25)]
    t = lambda f, d, **k: tone(f, d, "sine", partials=p, **k)
    return {
        "startup":    mix([(0.0, t(C5, 0.6, decay=0.3)), (0.12, t(E5, 0.6, decay=0.3)),
                           (0.24, t(G5, 0.6, decay=0.3)), (0.36, t(C6, 0.9, decay=0.45))], 1.3),
        "notify":     mix([(0.0, t(E6, 0.35, decay=0.12)), (0.11, t(B5, 0.5, decay=0.18))], 0.7),
        "volume":     mix([(0.0, t(A5, 0.08, decay=0.03, vol=0.3))], 0.1),
        "theme":      mix([(0.0, t(C5, 0.45, decay=0.2, slide_to=G5))], 0.5),
        "screenshot": mix([(0.0, noise(0.05, 0.5, 0.012)), (0.07, noise(0.06, 0.4, 0.015))], 0.15),
        "bell":       mix([(0.0, t(E4, 0.4, decay=0.15)), (0.14, t(C4, 0.6, decay=0.25))], 0.8),
    }


def arcade():
    t = lambda f, d, **k: tone(f, d, "pulse", vol=0.28, attack=0.002, **k)
    return {
        "startup":    mix([(0.0, t(C5, 0.1, decay=0.2)), (0.09, t(E5, 0.1, decay=0.2)),
                           (0.18, t(G5, 0.1, decay=0.2)), (0.27, t(C6, 0.35, decay=0.25))], 0.7),
        "notify":     mix([(0.0, t(E6, 0.07, decay=0.2)), (0.07, t(C6, 0.14, decay=0.2))], 0.3),
        "volume":     mix([(0.0, t(A5, 0.04, decay=0.04))], 0.05),
        "theme":      mix([(0.0, t(C5, 0.25, decay=0.3, slide_to=C6))], 0.3),
        "screenshot": mix([(0.0, noise(0.04, 0.4, 0.01)), (0.06, t(E6, 0.05, decay=0.1))], 0.15),
        "bell":       mix([(0.0, t(G4, 0.12, decay=0.2)), (0.12, t(C4, 0.25, decay=0.3))], 0.4),
    }


def blocky():
    """Short, dry, wooden clicks and pops."""
    tri = lambda f, d, **k: tone(f, d, "triangle", vol=0.5, attack=0.001, **k)
    pop = lambda f, d: tone(f * 1.6, d, "sine", vol=0.5, decay=0.03, attack=0.001, slide_to=f * 0.5)
    return {
        "startup":    mix([(0.0, tri(C4, 0.12, decay=0.05)), (0.1, tri(E4, 0.12, decay=0.05)),
                           (0.2, tri(G4, 0.12, decay=0.05)), (0.3, tri(C5, 0.3, decay=0.12))], 0.7),
        "notify":     mix([(0.0, pop(E5, 0.1)), (0.09, pop(A5, 0.12))], 0.3),
        "volume":     mix([(0.0, noise(0.02, 0.3, 0.006)), (0.0, tri(C5, 0.04, decay=0.02))], 0.06),
        "theme":      mix([(0.0, pop(C5, 0.12)), (0.08, pop(E5, 0.12)), (0.16, pop(G5, 0.16))], 0.35),
        "screenshot": mix([(0.0, noise(0.03, 0.6, 0.008)), (0.05, noise(0.04, 0.5, 0.01))], 0.1),
        "bell":       mix([(0.0, tri(G4 * 0.5, 0.18, decay=0.08)), (0.12, tri(C4 * 0.5, 0.25, decay=0.1))], 0.45),
    }


def glass():
    p = [(1.0, 1.0), (2.76, 0.5), (5.4, 0.2)]
    def t(f, d, **k):
        k.setdefault("vol", 0.4)
        return tone(f, d, "sine", partials=p, attack=0.002, **k)
    return {
        "startup":    mix([(0.0, t(G5, 1.0, decay=0.5)), (0.15, t(C6, 1.0, decay=0.5)),
                           (0.3, t(E6, 1.4, decay=0.7))], 1.8),
        "notify":     mix([(0.0, t(E6, 0.6, decay=0.25)), (0.12, t(G5 * 2, 0.8, decay=0.3))], 1.0),
        "volume":     mix([(0.0, t(C6, 0.12, decay=0.05, vol=0.3))], 0.15),
        "theme":      mix([(0.0, t(G5, 0.5, decay=0.2)), (0.07, t(C6, 0.5, decay=0.2)),
                           (0.14, t(E6, 0.7, decay=0.3))], 0.9),
        "screenshot": mix([(0.0, noise(0.04, 0.35, 0.01)), (0.05, t(C6 * 2, 0.2, decay=0.05, vol=0.3))], 0.3),
        "bell":       mix([(0.0, t(E5, 0.5, decay=0.2)), (0.14, t(C5, 0.8, decay=0.35))], 1.0),
    }


PACKS = {"soft": soft, "arcade": arcade, "blocky": blocky, "glass": glass}

if __name__ == "__main__":
    total = 0
    for pack, build in PACKS.items():
        for name, samples in build().items():
            path = save(pack, name, samples)
            total += os.path.getsize(path)
            print(f"{pack}/{name}.wav")
    print(f"{total / 1024:.0f} KB total")
