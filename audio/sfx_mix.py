#!/usr/bin/env python3
"""Lay a few sound effects under a finished (voiced) Repatory video.

    python3 sfx_mix.py <in.mp4> <cues.json> <out.mp4> [--sfx <dir>]

cues.json: {"cues": [{"t": 3.1, "s": "whoosh_soft"}, {"t": 6.4, "s": "plate_clank", "db": -2}]}
  t  = second where the sound's main hit should land (whooshes peak ~0.3 s in,
       so the script starts them early automatically)
  s  = file name in the sfx dir, without .wav
  db = optional trim on top of the default level for that sound (keep it within ±4)

DON'T-OVERDO-IT RULES (enforced):
  * at most 6 cues per video (warns at 5+)
  * nothing before 2.0 s: the opening logo stays silent (owner rule)
  * at least 0.5 s between cues
  * default levels sit well under the voice (voice ~ -20 dB mean; effects peak
    around -24 to -28 dBFS)
Video is copied; only the audio is re-encoded (AAC 192k).
"""
import json, os, subprocess, sys

LEVEL = {  # dB applied to the -3 dBFS source files
    "whoosh_soft": -24, "whoosh_short": -25, "pop_card": -22, "tick": -26,
    "plate_clank": -21, "rack_thud": -19, "breath_in": -24, "exhale": -24,
    "impact_low": -18,
}
LEAD = {"whoosh_soft": 0.30, "whoosh_short": 0.08, "breath_in": 0.32}
MAX_CUES, MIN_START, MIN_GAP = 6, 2.0, 0.5


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        sys.exit(__doc__)
    src, cue_path, out = a[:3]
    sfx = a[a.index("--sfx") + 1] if "--sfx" in a else os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")
    cues = sorted(json.load(open(cue_path))["cues"], key=lambda c: c["t"])
    if len(cues) > MAX_CUES:
        sys.exit(f"{len(cues)} cues: too many (max {MAX_CUES}). Keep only the biggest moments.")
    if len(cues) >= 5:
        print(f"note: {len(cues)} cues, that's the upper end; make sure each one earns its place")
    last = -9
    for c in cues:
        if c["t"] < MIN_START:
            sys.exit(f"cue at {c['t']} s is before {MIN_START} s: the opening logo stays silent")
        if c["t"] - last < MIN_GAP:
            sys.exit(f"cues at {last} and {c['t']} s are closer than {MIN_GAP} s")
        if not os.path.exists(os.path.join(sfx, c["s"] + ".wav")):
            sys.exit(f"missing sound {c['s']}.wav in {sfx}")
        last = c["t"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src]
    for c in cues:
        cmd += ["-i", os.path.join(sfx, c["s"] + ".wav")]
    parts, labels = [], []
    for i, c in enumerate(cues, 1):
        start = max(0.0, c["t"] - LEAD.get(c["s"], 0.0))
        gain = LEVEL.get(c["s"], -24) + float(c.get("db", 0))
        ms = int(round(start * 1000))
        parts.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain}dB,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    parts.append("[0:a]aresample=48000,aformat=channel_layouts=stereo[v0]")
    parts.append(f"[v0]{''.join(labels)}amix=inputs={len(cues)+1}:duration=first:normalize=0,alimiter=limit=0.95[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("wrote", out, "with", len(cues), "cues")


if __name__ == "__main__":
    main()
