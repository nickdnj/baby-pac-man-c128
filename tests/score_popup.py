#!/usr/bin/env python3
"""score_popup.py - eating a blue ghost or the fruit pops its points up.

Regression test for a request from the museum: the points must show where
the ghost / fruit was (200 400 800 1600 for ghosts, 100 300 500 700 for
fruit), the maze stands still for about 45 frames, then everything is put
back (Pac-Man and the ghost sprites on again, the popup digits gone).

Uses build/test-auto2.d64 through tests/vice_script.py: puts Pac-Man and a blue
ghost on the same cell (or Pac-Man on the fruit cell with the fruit out), then
reads the screen RAM under the popup, and again once it should be over.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "score-popup")
VSCR = 0xC000


def run(steps):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "vice_script.py"),
                        os.path.join(ROOT, "build", "test-auto2.d64"), "bpauto",
                        os.path.join(ROOT, "build", "babypac2-auto.lbl"), OUT] + steps,
                       capture_output=True, text=True, timeout=240, cwd=ROOT)
    rows = [[int(b, 16) for b in m.group(1).split()] for m in
            re.finditer(r"^\S+ \S+ >C:[0-9a-f]{4}\s+((?:[0-9a-f]{2} ?)+?)\s{2,}", r.stdout, re.M)]
    return rows


def case(name, setup, row, col, text):
    off = VSCR + row * 40 + col
    steps = ["f=800", "chutes_open=0"] + setup + [
        "t=0.15", "peek=pop_t:1", "peek=$%X:%d" % (off, len(text)),
        "t=1.3", "peek=pop_t:1", "peek=$D015:1", "peek=$%X:%d" % (off, len(text))]
    rows = run(steps)
    if len(rows) != 5:
        print("%s: could not read the results: %s" % (name, rows))
        return False
    pop, shown, after, spren, later = rows[0][0], rows[1], rows[2][0], rows[3][0], rows[4]
    want = [ord(c) for c in text]
    ok = 1 <= pop <= 45 and shown[:len(want)] == want and after == 0 \
        and spren & 3 == 3 and later[:len(want)] != want
    print("%s: pop_t %d, cells %s (want %s), later pop_t %d, sprites on %02X, cells later %s -> %s" % (
        name, pop, shown[:len(want)], want, after, spren, later[:len(want)], "ok" if ok else "FAIL"))
    return ok


ok = case("ghost 200", ["ax_lo=96", "ax_hi=0", "ay=96", "ax_lo+1=96", "ax_hi+1=0", "ay+1=96",
                        "gstate+1=1", "gblue+1=1", "eatcount=0", "fright=8,1"], 12, 11, "200")
ok = case("fruit 700", ["fr_t=255,1", "fr_kind=3", "ax_lo=152", "ax_hi=0", "ay=120"], 15, 18, "700") and ok
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
