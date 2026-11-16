#!/usr/bin/env python3
"""dual_screen.py - both screens stay alive (status board + waiting ghosts).

Regression test for the museum request "always something happening on both
screens", on build/test-auto2.d64 (autopilot game) through tests/vice_script.py.

Part 1, maze phase, VDC status board (src/maze/board.s). The game state is
poked (ghosts held with mz_hold so nothing moves or collides), then single
board rows are read back from VDC RAM by the AUTOPLAY hook in main3.s
(dmp_req = VDC row + 1 -> dmp_c / dmp_a = screen codes / attributes of VDC
columns 25-54) and checked cell by cell:
  - ghost rows: icon colour and state word for CHASE (own colour), BLUE
    (light blue, countdown bar = ceil(fright / 30) cells), EYES (grey),
    HOME (dark); flashing (hardware blink bit) when fright < 120;
  - thermometer: one yellow cell per 5 % eaten, the dots-left number;
  - lives (Pac-Man icons from the panel art) and the fruit icon / IN MAZE.
Part 2, pinball visit, VIC (mz_wait_tick in maze.s): while the ball is in
play the ghost sprites move (registers / pointers change) but ax_lo, ax_hi,
ay, adir, gstate, gblue, fright stay byte for byte the same; the row-24
energizer counter shows pb_energ; after the drain the maze resumes with the
same ghost state and draw_sprites has put every ghost sprite back where the
state says. Then many visits / game overs: main3's AUTOPLAY check read the
whole table back from VDC RAM after every handoff and game over and found no
cell different from the table's own disp / vis_attrs (chk_bad = 0).
Screenshots: build/dual-screen-*.png.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
ALT, REV, BLINK = 0x80, 0x40, 0x10
LTBLUE, DKGREY, LTGREY, LTYEL, WHITE = 3, 1, 14, 13, 15
GCOL = {1: 9, 2: 11, 3: 7, 4: 12}           # Blinky ltred, Pinky ltpurp, Inky ltcyan, Clyde dkyel
GDIM = {1: 8, 2: 10, 3: 6, 4: 1}
GROW = {1: 5, 2: 7, 3: 9, 4: 11}            # VDC row of the ghost's icon top / word


def scr(t):
    return [ord(c) - 64 if "A" <= c <= "Z" else ord(c) for c in t]


def run(out, steps, timeout=600):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "vice_script.py"),
                        os.path.join(B, "test-auto2.d64"), "bpauto",
                        os.path.join(B, "babypac2-auto.lbl"), os.path.join(B, out)] + steps,
                       capture_output=True, text=True, timeout=timeout, cwd=ROOT)
    peeks = []
    for m in re.finditer(r"^(\S+) \S+ >C:[0-9a-f]{4}((?:\s{1,2}[0-9a-f]{2})+)", r.stdout, re.M):
        peeks.append((m.group(1), [int(b, 16) for b in m.group(2).split()]))
    return peeks, r.stdout + r.stderr


def dump(row):
    return ["dmp_req=%d" % (row + 1), "w=dmp_req:0", "peek=dmp_c:15", "peek=dmp_c+15:15",
            "peek=dmp_a:15", "peek=dmp_a+15:15"]


class Rows:
    """consume the peek list in order"""

    def __init__(self, peeks):
        self.p = list(peeks)

    def take(self, name=None):
        n, v = self.p.pop(0)
        if name and n != name:
            raise ValueError("expected %s got %s" % (name, n))
        return v

    def row(self):
        c = self.take() + self.take()
        a = self.take() + self.take()
        return c, a


fails = []


def check(what, cond, detail=""):
    print("  %-52s %s %s" % (what, "ok" if cond else "FAIL", detail))
    if not cond:
        fails.append(what)


# ---------------------------------------------------------------- part 1
shot = os.path.join(B, "dual-screen")
hold = ["mz_hold=255", "chase=1", "mode_t=0,0", "fr_shown=2"]
steps = ["f=420", "chutes_open=0", "f=800", "chutes_open=0",
         "peek=pan_codes+200:12", "peek=pan_codes+240:12", "peek=vis_codes+45:3"]
# A: Blinky chase, Pinky blue (fright 300), Inky eyes, Clyde home; 1 life,
# orange level, no fruit out; 156 dots left
steps += hold + ["gstate+1=1", "gblue+1=0", "gstate+2=1", "gblue+2=1", "fright=44,1",
                 "gstate+3=2", "gblue+3=0", "gstate+4=0", "gblue+4=0", "grel+4=255",
                 "mz_lives=1", "fr_kind=2", "fr_t=0,0", "mz_dotsleft=156,0", "t=0.6",
                 "peek=fright:2"] + dump(5) + dump(7) + dump(8) + dump(9) + dump(11) \
    + dump(14) + dump(15) + dump(16) + dump(17) + ["vdc=%s-states-vdc.png" % shot]
# B: Pinky flashing (fright 100); 3 lives, fruit out (apple); 311 dots left
steps += hold + ["fright=100,0", "mz_lives=3", "fr_kind=3", "fr_t=255,1", "mz_dotsleft=55,1",
                 "t=0.6", "peek=fr_t:2"] + dump(17) + ["peek=fr_t:2", "peek=fright:2"] \
    + dump(7) + dump(8) + dump(14) + dump(16) \
    + ["vdc=%s-flash-vdc.png" % shot]
# C: thermometer nearly full (16 left)
steps += hold + ["mz_dotsleft=16,0", "t=0.5"] + dump(14) + dump(15) + ["vdc=%s-full-vdc.png" % shot]
peeks, log = run("dual-screen-board", steps)
print("1. maze phase: VDC status board")
try:
    R = Rows(peeks)
    pac = R.take(), R.take()
    fruit = R.take()
    fr_now = R.take("fright")
    fr_now = fr_now[0] | fr_now[1] << 8

    def ghost(g, word, icon, wattr, label):
        c, a = R.row()
        check("%s: word %s" % (label, word.strip()), c[13:20] == scr(word), c[13:20])
        check("%s: icon colour" % label, a[1:4] == [icon] * 3, ["%02x" % x for x in a[1:4]])
        check("%s: word colour" % label, a[13:20] == [wattr] * 7, "%02x" % a[13])

    def bar(label, fright, flash):
        c, a = R.row()
        n = min(12, -(-fright // 30))
        on = LTBLUE | REV | (BLINK if flash else 0)
        filled = sum(1 for x in a[13:25] if x == on)
        ok = a[13:13 + filled] == [on] * filled and a[13 + filled:25] == [0] * (12 - filled) \
            and abs(filled - n) <= 1 and filled > 0
        check("%s: blue bar %d cells (fright %d -> %d)" % (label, filled, fright, n), ok,
              ["%02x" % x for x in a[13:25]])

    def cells_of(a):
        return sum(1 for x in a[6:26] if x == LTYEL | REV)

    def therm_one(c, a, label):
        d = "".join(chr(x) if 0x30 <= x <= 0x39 else " " for x in c[26:29]).strip()
        left = int(d) if d else -1
        pct = (311 - left) * 100 // 311
        cells = sum(1 for x in a[6:26] if x == LTYEL | REV)
        ok = a[6:6 + cells] == [LTYEL | REV] * cells and \
            a[6 + cells:26] == [DKGREY | REV] * (20 - cells) and cells == pct // 5
        check("%s: %d left, %d %% eaten -> %d yellow cells" % (label, left, pct, cells), ok)
        return left

    def therm(label):
        c, a = R.row()
        left = therm_one(c, a, label)
        c2, a2 = R.row()
        # (read a moment later: a dot eaten meanwhile can move the fill by one
        # cell; both rows are drawn in the same call)
        n2 = sum(1 for x in a2[6:26] if x == LTYEL | REV)
        same = a2[6:6 + n2] == [LTYEL | REV] * n2 and a2[6 + n2:26] == [DKGREY | REV] * (20 - n2)
        check("%s: second row the same (%d cells)" % (label, n2), same and abs(n2 - cells_of(a)) <= 1)
        return left

    ghost(1, "CHASE  ", GCOL[1] | ALT, GCOL[1] | ALT, "A Blinky")
    ghost(2, "BLUE   ", LTBLUE | ALT, LTBLUE | ALT, "A Pinky")
    bar("A Pinky", fr_now, False)
    ghost(3, "EYES   ", DKGREY | ALT, LTGREY | ALT, "A Inky")
    ghost(4, "HOME   ", GDIM[4] | ALT, LTGREY | ALT, "A Clyde")
    left = therm("A thermometer")
    check("A dots left about 156", 150 <= left <= 156, left)
    c, a = R.row()
    check("A lives: 1 Pac-Man icon", c[7:10] == pac[0][0:3] and c[10:18] == [32] * 8, c[7:18])
    check("A fruit icon: orange", c[26] == fruit[2] and a[26] == 12, "%02x %02x" % (c[26], a[26]))
    c, a = R.row()
    check("A no fruit out: IN MAZE blank", c[20:27] == [32] * 7, c[20:27])

    t0 = R.take("fr_t")
    c2, a2 = R.row()
    t1 = R.take("fr_t")
    out = (t0[0] | t0[1]) and (t1[0] | t1[1])       # (Pac-Man may eat it meanwhile)
    if out:
        check("B fruit out: IN MAZE (blinking)", c2[20:27] == scr("IN MAZE")
              and a2[20] == WHITE | ALT | BLINK, c2[20:27])
    else:
        print("  (B fruit eaten before the board was read: IN MAZE not checked)")
    fr_now = R.take("fright")
    fr_now = fr_now[0] | fr_now[1] << 8
    ghost(2, "BLUE   ", LTBLUE | ALT | BLINK, LTBLUE | ALT | BLINK, "B Pinky flashing")
    bar("B Pinky flashing", fr_now, True)
    c, a = R.row()
    left = therm_one(c, a, "B thermometer")
    check("B dots left about 311", 285 <= left <= 311, left)
    c, a = R.row()
    want = pac[0][0:3] + [32] + pac[0][0:3] + [32] + pac[0][0:3]
    check("B lives: 3 Pac-Man icons", c[7:18] == want, c[7:18])
    check("B fruit icon: apple", c[26] == fruit[2] and a[26] == 5, "%02x %02x" % (c[26], a[26]))
    left = therm("C thermometer")
    check("C dots left about 16", 10 <= left <= 16, left)
except (IndexError, ValueError) as e:
    check("could not read the board (%s)" % e, False, log[-800:])

# ---------------------------------------------------------------- part 2
STATE = ["peek=ax_lo:15", "peek=ax_lo+15:10", "peek=gblue:5", "peek=fright:2"]
REGS = ["peek=$D000:16", "peek=$D010:1", "peek=$C3F8:8", "peek=$D015:1"]
steps = ["warp=on", "w=sh_cnt:1", "warp=off"] + STATE + REGS + ["pb_energ=12", "t=0.6"] + STATE + REGS + \
    ["peek=$C3E0:6", "peek=$DBE0:6", "bot_quick=1", "w=pb_state:2", "t=0.3"] + STATE + REGS + \
    ["peek=frame:2", "warp=on", "t=25", "peek=chk_bad:3", "peek=cy_n:4"]
peeks, log = run("dual-screen-visit", steps)
print("2. pinball visit: waiting ghosts, energizer counter, table intact")
try:
    R = Rows(peeks)

    def state():
        a = R.take() + R.take()
        return a, R.take(), R.take()

    def regs():
        return R.take(), R.take()[0], R.take(), R.take()[0]

    s0 = state()
    r0 = regs()
    s1 = state()
    r1 = regs()
    scrn, col = R.take(), R.take()
    s2 = state()
    r2 = regs()
    frame = R.take()
    frame = frame[0] | frame[1] << 8
    check("game state unchanged during the visit", s0 == s1, "")
    gx = lambda r, g: r[0][2 * g] | (256 if r[1] & (1 << g) else 0)
    moved = [g for g in range(1, 5) if (r0[0][2 * g:2 * g + 2], r0[2][g]) != (r1[0][2 * g:2 * g + 2], r1[2][g])]
    check("ghost sprites move / look around (%d of 4 changed)" % len(moved), len(moved) >= 3, moved)
    check("Pac-Man stays hidden, ghosts shown (sprites on %02x)" % r1[3],
          r0[3] & 0x1F == 0x1E and r1[3] & 0x1F == 0x1E)
    check("row 24 counter: energizer, X, 12", scrn == [65, 32, 24, 32, 0x31, 0x32], scrn)
    # after the drain Pac-Man (actor 0) moves again and fright counts on; the
    # ghosts are held (mz_hold) and must be exactly where they waited
    gh = lambda st: [st[0][k * 5 + g] for k in range(5) for g in range(1, 5)] + st[1][1:5]
    check("same ghost state after the drain (mz_hold)", gh(s2) == gh(s1),
          "" if gh(s2) == gh(s1) else "%s -> %s" % (gh(s1), gh(s2)))
    ax_lo, ax_hi, ay, gst = s2[0][0:5], s2[0][5:10], s2[0][10:15], s2[0][20:25]
    ok = True
    for g in range(1, 5):
        x = ax_lo[g] + 256 * ax_hi[g] + 19
        y = ay[g] + 47
        yy = r2[0][2 * g + 1]
        if gx(r2, g) != x or not (yy == y or (gst[g] == 0 and yy == y - 2)):
            ok = False
            print("    ghost %d: sprite %d,%d state says %d,%d" % (g, gx(r2, g), yy, x, y))
    check("ghost sprites back where the state says (draw_sprites)", ok)
    bad = R.take()
    n = R.take()
    check("table read back after %d handoffs / game overs: %d cells differ" % (bad[2], bad[0] | bad[1] << 8),
          bad[0] == 0 and bad[1] == 0 and bad[2] >= 2)
except (IndexError, ValueError) as e:
    check("could not read the visit state (%s)" % e, False, log[-800:])

print("PASS" if not fails else "FAIL (%d)" % len(fails))
sys.exit(0 if not fails else 1)
