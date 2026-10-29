#!/usr/bin/env python3
"""ghost_tunnel.py - frightened and normal ghosts at the tunnel mouths.

Regression test for a hang found on the real C128: a blue ghost whose only
legal move is "reverse" (as at a tunnel mouth) made choose_random spin for
ever, so the whole game froze right after an energizer was eaten.

Uses build/test-auto2.d64 (make build/test-auto2.d64) through tests/vice_script.py:
puts a blue ghost on the left tunnel mouth heading out, then checks that the
frame counter keeps moving and that the ghost comes out on the right side
(it must warp through, not bounce back). Then the same for a normal ghost.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "ghost-tunnel")


def run(blue):
    steps = ["f=1500", "ax_lo+1=8", "ax_hi+1=0", "ay+1=96", "adir+1=1", "gstate+1=1",
             "gblue+1=%d" % blue, "fright=$68,1" if blue else "fright=0,0"]
    for _ in range(6):
        steps += ["t=1", "peek=frame:2", "peek=ax_hi+1:1"]
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "vice_script.py"),
                        os.path.join(ROOT, "build", "test-auto2.d64"), "bpauto",
                        os.path.join(ROOT, "build", "babypac2-auto.lbl"), OUT] + steps,
                       capture_output=True, text=True, timeout=240, cwd=ROOT)
    frames = [int(m.group(1), 16) | int(m.group(2), 16) << 8 for m in
              re.finditer(r"^frame \S+ >C:[0-9a-f]{4}\s+([0-9a-f]{2}) ([0-9a-f]{2})", r.stdout, re.M)]
    side = [int(m.group(1), 16) for m in
            re.finditer(r"^ax_hi\+1 \S+ >C:[0-9a-f]{4}\s+([0-9a-f]{2})", r.stdout, re.M)]
    return frames, side


ok = True
for blue in (1, 0):
    frames, side = run(blue)
    advancing = len(frames) >= 4 and all(b != a for a, b in zip(frames, frames[1:]))
    crossed = 1 in side
    print("%s ghost: frames %s, ax_hi samples %s -> %s%s" % (
        "blue" if blue else "normal", frames, side, "running" if advancing else "HUNG",
        ", crossed the tunnel" if crossed else ", did not cross"))
    ok = ok and advancing and crossed
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
