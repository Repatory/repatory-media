#!/usr/bin/env python3
"""Make the Kokoro voice sound recorded instead of synthetic. Run it on the
vo.wav from `vo.py make`, BEFORE `vo.py mix`. Timing is unchanged (same length,
same line starts), so out/<slug>-vo.json still matches.

    python3 vo_polish.py out/<slug>-vo.wav out/<slug>-vo-p.wav

Chain: rumble cut, less boxiness, a little presence, gentle compression, a very
small room (two early reflections, ~10% wet), and a touch of room tone so the
silences aren't digitally dead. Then use the -p file in `vo.py mix`.
"""
import subprocess, sys

CHAIN = ",".join([
    "aresample=48000",
    "highpass=f=85",
    "equalizer=f=280:t=q:w=1.1:g=-2.5",   # less boxy/chesty
    "equalizer=f=3200:t=q:w=1.3:g=1.8",   # a bit of presence
    "equalizer=f=8500:t=q:w=1.5:g=-2",    # soften the synthetic fizz
    "acompressor=threshold=-22dB:ratio=2.2:attack=10:release=140:makeup=1.5",
    "aecho=0.9:0.9:19|31:0.10|0.06",      # small room, mostly dry
    "alimiter=limit=0.89",
])


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1:]
    # room tone: very quiet pink-ish noise under the whole take (~ -62 dBFS)
    fc = (f"[0:a]{CHAIN}[v];"
          "anoisesrc=color=pink:amplitude=0.0016:sample_rate=48000[n];"
          "[n]lowpass=f=4000[nn];"
          "[v][nn]amix=inputs=2:duration=first:normalize=0[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex", fc,
                    "-map", "[a]", "-ac", "1", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
