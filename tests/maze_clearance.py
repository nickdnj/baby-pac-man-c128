#!/usr/bin/env python3
"""maze_clearance.py - can every actor visually pass every corridor?

Runs tools/mkmaze.py in-process and takes its wall pixels (exactly what the
VIC charset shows), then slides every Pac-Man and ghost sprite, pixel for
pixel, along every link between neighbouring open cells (tunnel and chute
cells included) and reports any overlap with a wall line. It also checks
that the open cells form one connected maze and that the tunnel wraps.

Sprite placement matches draw_sprites: hi-res Pac-Man top-left = (col*8-3,
row*8-3); multicolour ghosts (sprite X + 19) top-left = (col*8-5, row*8-3), so
both 14 px shapes sit centred on the cell.

Usage: maze_clearance.py          (exit status 1 if anything is blocked)
"""
import contextlib
import io
import os
import runpy
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.argv = ["mkmaze.py", os.devnull]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(os.environ.get("MKMAZE", os.path.join(ROOT, "tools", "mkmaze.py")))
wall = np.array(g["wallpx"], bool)
typ = g["typ"]
sprites, SP = g["sprites"], g["SP"]
H, W = len(typ), len(typ[0])


def sprite_mask(idx, multicolour):
    data = sprites[idx]
    m = np.zeros((16, 16), bool)
    for y in range(16):
        v = (data[y * 3] << 16) | (data[y * 3 + 1] << 8) | data[y * 3 + 2]
        if multicolour:
            for x in range(8):
                if (v >> (22 - 2 * x)) & 3:
                    m[y, 2 * x:2 * x + 2] = True
        else:
            for x in range(16):
                if (v >> (23 - x)) & 1:
                    m[y, x] = True
    return m


ACTORS = {}
XOFF = {}
for name in ("PAC", "PAC_HR", "PAC_HL", "PAC_HU", "PAC_HD",
             "PAC_WR", "PAC_WL", "PAC_WU", "PAC_WD"):
    ACTORS[name] = sprite_mask(SP[name], False)
    XOFF[name] = -3
for name in ("GH_R0", "GH_L0", "GH_U0", "GH_D0"):
    ACTORS[name] = sprite_mask(SP[name], True)
    XOFF[name] = -5


def hits(mask, left, top):
    """wall pixels under the sprite mask placed with its top-left at (left, top)"""
    n = 0
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        px, py = left + x, top + y
        if 0 <= px < 320 and 0 <= py < 200 and wall[py, px]:
            n += 1
    return n


passable = [[typ[r][c] in (0, 4) for c in range(W)] for r in range(H)]
cells = [(r, c) for r in range(H) for c in range(W) if passable[r][c]]

# connectivity
start = (g["pac"][0], g["pac"][1])
seen, todo = {start}, [start]
while todo:
    r, c = todo.pop()
    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        n = (r + dr, c + dc)
        if 0 <= n[0] < H and 0 <= n[1] < W and passable[n[0]][n[1]] and n not in seen:
            seen.add(n)
            todo.append(n)
# the tunnel row wraps: its two end cells are neighbours
tr = g["tunnel_row"]
isolated = [cell for cell in cells if cell not in seen and cell[1] not in (g["tunnel_cols"][0], g["tunnel_cols"][1])]
lost_dots = [(r, c) for r in range(H) for c in range(W) if g["dots"][r][c] and (r, c) not in seen]
print("open cells %d, reachable from Pac-Man's start %d" % (len(cells), len(seen)))
failed = False
if isolated:
    print("  NOT connected:", isolated)
    failed = True
if lost_dots:
    print("  DOTS Pac-Man can never reach (%d): %s" % (len(lost_dots), lost_dots))
    failed = True
print("dots %d, all reachable: %s" % (sum(map(sum, g["dots"])), not lost_dots))

links = []
for r, c in cells:
    for dr, dc in ((0, 1), (1, 0)):
        n = (r + dr, c + dc)
        if n[0] < H and n[1] < W and passable[n[0]][n[1]]:
            links.append(((r, c), n))

bad = {}
worst = {}
for name, base in ACTORS.items():
    mask = base
    for (r0, c0), (r1, c1) in links:
        x0, y0 = c0 * 8 + XOFF[name], r0 * 8 - 3
        x1, y1 = c1 * 8 + XOFF[name], r1 * 8 - 3
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for s in range(steps + 1):
            x = x0 + (x1 - x0) * s // steps
            y = y0 + (y1 - y0) * s // steps
            n = hits(mask, x, y)
            if n:
                key = ((r0, c0), (r1, c1))
                bad.setdefault(key, set()).add(name)
                worst[key] = max(worst.get(key, 0), n)
print("links checked per actor: %d, actors: %d" % (len(links), len(ACTORS)))
if bad:
    print("BLOCKED OR TOUCHING LINKS: %d" % len(bad))
    for key in sorted(bad):
        print("  %s -> %s  worst overlap %d px  (%s)" % (key[0], key[1], worst[key], ",".join(sorted(bad[key]))))
    failed = True
if failed:
    sys.exit(1)
print("OK: every actor passes every corridor link without touching a wall line")
