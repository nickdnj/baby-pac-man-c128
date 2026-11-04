#!/usr/bin/env python3
"""energizers_start.py - every new board starts with its four corner energizers.

Regression test for a report from the real C128 (v0.2.1): the maze came up
with no power pellets at all, because they were only ever awarded by the
pinball table. Uses build/test-auto2.d64 through tests/vice_script.py: waits
until the game is under way, then checks that the four corner slots
(rows 3/21, columns 2/37) hold an energizer (dots = 2) and show the energizer
glyph on the VIC screen.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "energizers-start")
VSCR = 0xC000
SLOTS = [3 * 40 + 2, 3 * 40 + 37, 21 * 40 + 2, 21 * 40 + 37]

steps = ["f=420"]
for off in SLOTS:
    steps.append("peek=dots+%d:1" % off)
for off in SLOTS:
    steps.append("peek=$%X:1" % (VSCR + off))
r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "vice_script.py"),
                    os.path.join(ROOT, "build", "test-auto2.d64"), "bpauto",
                    os.path.join(ROOT, "build", "babypac2-auto.lbl"), OUT] + steps,
                   capture_output=True, text=True, timeout=240, cwd=ROOT)
vals = [int(m.group(1), 16) for m in
        re.finditer(r"^\S+ \S+ >C:[0-9a-f]{4}\s+([0-9a-f]{2})", r.stdout, re.M)]
if len(vals) != 8:
    print("could not read the slots:\n" + r.stdout + r.stderr)
    sys.exit(1)
dots, glyphs = vals[:4], vals[4:]
print("dots in the corner slots: %s, screen glyphs: %s" % (dots, glyphs))
ok = all(d == 2 for d in dots) and len(set(glyphs)) == 1 and glyphs[0] not in (0x20, 0)
print("PASS" if ok else "FAIL: expected four energizers (dots = 2, same non-blank glyph)")
sys.exit(0 if ok else 1)
