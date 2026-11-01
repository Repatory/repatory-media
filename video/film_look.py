#!/usr/bin/env python3
"""Give a clean 3D render the feel of real phone footage. Run it on the encoded
render (before vo.py mix), so the shake/blur never touches the audio steps.

    python3 film_look.py <in.mp4> <out.mp4> [--strength 1.0] [--fps 30] [--blur]

What it adds, all subtle on purpose:
  * handheld drift: slow, uneven ±~3 px wander + a hint of rotation (two
    out-of-phase sine waves, so it never looks like a regular wobble)
  * 30 fps output (survives Instagram's compression better than 60 fps);
    --blur adds a light blend of neighbouring frames (test it first: on fast
    moves it can ghost the face, so it's off by default)
  * lens: a soft vignette
The frame is zoomed ~1.5% so the drift never shows a black edge, which means
anything placed within ~15 px of the frame edge gets trimmed (nothing of ours
lives there). --strength 0 turns the drift off; 1.5 is the most I'd use.
Video is re-encoded (libx264 crf 18); audio (if any) is copied.
"""
import subprocess, sys


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    src, out = a[:2]
    k = float(a[a.index("--strength") + 1]) if "--strength" in a else 1.0
    blur = "--blur" in a
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 30
    W, H = 1080, 1920
    z = 1.016
    zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
    mx, my = (zw - W) / 2, (zh - H) / 2
    ax, ay, rot = 3.0 * k, 3.5 * k, 0.0012 * k   # px, px, radians
    xs = f"{mx}+{ax}*(0.6*sin(2*PI*t*0.37)+0.4*sin(2*PI*t*0.91+1.3))"
    ys = f"{my}+{ay}*(0.6*sin(2*PI*t*0.29+0.7)+0.4*sin(2*PI*t*0.83+2.1))"
    vf = ",".join([
        *(["tmix=frames=2:weights='3 1'"] if blur else []),  # light motion blur (opt-in)
        f"fps={fps}",
        f"scale={zw}:{zh}:flags=lanczos",
        f"rotate='{rot}*sin(2*PI*t*0.23)':ow={zw}:oh={zh}:fillcolor=black",
        f"crop={W}:{H}:'{xs}':'{ys}'",
        "vignette=angle=PI/6:mode=forward",
        "format=yuv420p",
    ])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", vf,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "copy", "-movflags", "+faststart", out], check=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
