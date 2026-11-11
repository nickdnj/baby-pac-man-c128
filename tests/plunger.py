#!/usr/bin/env python3
"""plunger.py - the ball is shot up the shooter lane like a pinball plunger.

Regression test for the pinball upgrade, phase 1 (auto-fire plunger on the
v2 table). Before it the ball was dropped from the top arch; now it waits on
the plunger at the bottom of the right-hand shooter lane while the spring
compresses (GET READY), is fired straight up the lane (pb_state 3, PB_SHOOT),
turned left by the rounded top corner and enters the field.

Three parts, all through tests/vice_script.py:
 1. build/test-bot2.d64 (PINBOT), the first shot: fired from the bottom of the
    lane (sh_y0 = ball row at firing), straight up (vx = 0, vy < 0, x = the
    lane), and 0.2 s later higher up. Screenshot build/plunger-shot-vdc.png.
 2. Same image, fast launch loop (bot_quick: the ball is drained 150 frames
    after each shot), at least 32 shots: every strength (0-7) seen, at least
    95% reach the field (left of the TUNNEL lane guide wall), none stuck, the
    TUNNEL lane never lit within 2 s of a shot.
 3. build/test-auto2.d64 (full game, autopilot): a pinball visit fires the
    plunger (sh_cnt counts it) and the drain hands back to the maze
    (pb_state 2 and, 0.3 s later, mz_resume has run: its ghost hold mz_hold
    is counting down from 90; a game over would not set it), the maze runs.
The old behaviour (ball served from the arch, no PB_SHOOT, no sh_* counters)
fails part 1.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
SHOTS = 32
LANE_COL = 38              # hi byte of bx in the lane (x = 304 px)


def run(img, name, lbl, out, steps, timeout=600):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "vice_script.py"),
                        os.path.join(B, img), name, os.path.join(B, lbl),
                        os.path.join(B, out)] + steps,
                       capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    rows = {}
    # VICE prints the bytes in groups of 4 (two spaces between groups), then
    # the characters after a wider gap
    for m in re.finditer(r"^(\S+) \S+ >C:[0-9a-f]{4}((?:\s{1,2}[0-9a-f]{2})+)", r.stdout, re.M):
        rows.setdefault(m.group(1), []).append([int(b, 16) for b in m.group(2).split()])
    return rows, r.stdout + r.stderr


def s8(v):
    return v - 256 if v >= 128 else v


ok = True

# ---- 1. the first shot
rows, log = run("test-bot2.d64", "pinbot", "pinball2-bot.lbl", "plunger-shot",
                ["w=sh_cnt:1", "t=0.05", "peek=bx:6", "peek=sh_y0:1", "peek=pb_state:1", "vdc=%s" %
                 os.path.join(B, "plunger-shot-vdc.png"), "t=0.2", "peek=bx:6", "peek=pb_state:1"])
try:
    a, b = rows["bx"][0], rows["bx"][1]
    y0 = rows["sh_y0"][0][0]
    st0, st1 = rows["pb_state"][0][0], rows["pb_state"][1][0]
    by_a, by_b = a[2] | a[3] << 8, b[2] | b[3] << 8
    fired_low = y0 >= 36                       # ball row 18+ = bottom of the lane
    straight_up = st0 == 3 and a[1] == LANE_COL and a[4] == 0 and s8(a[5]) < 0
    rising = by_b < by_a
    p1 = fired_low and straight_up and rising
    print("1. first shot: fired at y %d (row %d), state %d, x col %d, vx %d, vy %d; 0.2 s later "
          "y %d (state %d) -> %s" % (y0 * 4, y0 >> 1, st0, a[1], s8(a[4]), s8(a[5]),
                                     by_b >> 6, st1, "ok" if p1 else "FAIL"))
except (KeyError, IndexError):
    p1 = False
    print("1. first shot: FAIL, no plunger shot seen (old build or no data):\n" + log[-600:])
ok = ok and p1

# ---- 2. many shots
if p1:
    rows, log = run("test-bot2.d64", "pinbot", "pinball2-bot.lbl", "plunger-many",
                    ["w=sh_cnt:1", "bot_quick=150", "warp=on", "w=sh_cnt:%d" % (SHOTS + 1),
                     "t=0.05", "peek=sh_cnt:9"])
    try:
        cnt, field, bad, tun, arm, _t, _y0, _q, seen = rows["sh_cnt"][0]
        done = cnt - arm                       # the last one may still be in flight
        rate = field / float(done) if done else 0.0
        p2 = done >= SHOTS and rate >= 0.95 and bad == 0 and tun == 0 and seen == 0xFF
        print("2. %d shots: %d reached the field (%.0f%%), %d stuck/late, TUNNEL lit by a launch %d, "
              "strengths seen %02X -> %s" % (done, field, rate * 100, bad, tun, seen,
                                             "ok" if p2 else "FAIL"))
    except (KeyError, IndexError, ValueError):
        p2 = False
        print("2. many shots: FAIL, could not read the counters:\n" + log[-600:])
    ok = ok and p2

# ---- 3. full game: plunger visit, drain back to the maze
rows, log = run("test-auto2.d64", "bpauto", "babypac2-auto.lbl", "plunger-handoff",
                ["warp=on", "w=sh_cnt:1", "warp=off", "t=0.05", "peek=mz_chute:1", "w=pb_state:2",
                 "t=0.3", "peek=mz_hold:1", "peek=frame:2", "t=1", "peek=frame:2",
                 "peek=pb_state:1"])
try:
    hold = rows["mz_hold"][0][0]
    f0, f1 = [v[0] | v[1] << 8 for v in rows["frame"][:2]]
    st = rows["pb_state"][0][0]
    p3 = "waited sh_cnt = 1" in log and "waited pb_state = 2" in log and 0 < hold <= 90 \
        and st == 2 and f1 != f0
    print("3. full game: plunger shot (chute %d), drained, maze resumed (ghost hold %d), frames "
          "%d -> %d -> %s" % (rows["mz_chute"][0][0], hold, f0, f1, "ok" if p3 else "FAIL"))
except (KeyError, IndexError):
    p3 = False
    print("3. full game: FAIL, could not read the state:\n" + log[-600:])
ok = ok and p3

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
