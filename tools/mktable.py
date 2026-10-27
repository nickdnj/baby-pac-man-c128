#!/usr/bin/env python3
"""mktable.py - generate the pinball table data (ca65 source). Art pass version.

Physics and visuals are separate layers:

  PHYSICS (unchanged from the Tier 2 build except the rounded top corners)
    tbl_codes  40x25 physics codes of the static table
    gclass     collision class per physics code (256)
    gnx, gny   collision normal per physics code, signed, 127 = 1.0
    pglyph     collision bitmaps of physics codes 64.. (8 bytes each)
    fl_dx/dy/nx/ny flipper direction/normal per flipper*3+pose

  VISUALS (art pass; our own pixel art, nothing taken from any ROM)
    vis_codes / vis_attrs   40x25 table cells (VDC columns 20-59)
    pan_codes / pan_attrs   25 rows x 40: VDC columns 0-19 then 60-79
    glyph0     bank 0 glyphs, codes 64..239 (codes 0-63 = ROM font, copied
               at run time; 240-247 = ball slots)
    glyph1     bank 1 (alternate set, attribute bit 7) glyphs 0..255:
               0-63 our bold font, 64.. panel / deep-wall art
    flip_codes 2 flippers x 3 poses x FB_H x FB_W visual codes (bank 0)
    lit_row/lit_col/lit_on/lit_off  the 8 lights (targets 0-3, lanes 4-7)
    ball_bits  8 x-shifts x 4 rows x 2 bytes (7x4 ball)
    big strings for the panel (GO! in the 3x2 logo font)

Physics space: x unit = 1 VDC pixel; y unit = half a scanline (ASPECT_Y = 2).
Usage: mktable.py OUT.s [PREVIEW_PREFIX]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import (RGBI, A_ALT, A_BLINK, A_REV, Canvas, Bank, resolve_cell,
                    font_charset_0_63, scr_code, preview_vdc)

W, H = 40, 25
C = RGBI

# collision classes (must match src/pinball/pinball.s)
C_EMPTY, C_FULL, C_SHAPE, C_BUMPER, C_SLING, C_TARGET, C_LANE, C_SPIN = range(8)

# ======================================================================
# PHYSICS MAP (same construction as the Tier 2 generator)
# ======================================================================
rows = [[' '] * W for _ in range(H)]


def put(r, c, ch):
    rows[r][c] = ch


for r in range(H):
    put(r, 0, '#')
    put(r, W - 1, '#')
for c in range(W):
    put(0, c, '#')
put(1, 1, 'q')
put(1, 38, 'p')
for c in (14, 17, 22, 25):              # fruit lanes
    put(3, c, 'f')
BUMPERS = ((4, 10), (4, 26), (7, 18))
for r0, c0 in BUMPERS:                  # pop bumpers 4x2
    for dr in range(2):
        for dc in range(4):
            put(r0 + dr, c0 + dc, 'B%d' % (dr * 4 + dc))
for r in (6, 8):                        # energizer targets
    put(r, 1, 'T')
    put(r, 38, 'T')
for c in range(18, 22):                 # spinner
    put(11, c, '~')
for r in range(10, 21):                 # funnel
    lc = r - 9
    for c in range(0, lc):
        put(r, c, '#')
    put(r, lc, '\\')
    rc = W - 1 - lc
    for c in range(rc + 1, W):
        put(r, c, '#')
    put(r, rc, '/')
for i in range(3):                      # slingshots
    put(15 + i, 11 + i, 'K')
    put(15 + i, 28 - i, 'J')
put(16, 11, 'k'); put(17, 11, 'k'); put(17, 12, 'k')
put(16, 28, 'k'); put(17, 28, 'k'); put(17, 27, 'k')
for c in range(0, 12):
    put(21, c, '#')
for c in range(28, W):
    put(21, c, '#')
for c in range(W):
    put(22, c, '#' if not (18 <= c <= 21) else ' ')
for r in (23, 24):
    for c in range(W):
        put(r, c, '#')
for c in range(17, 23):                 # drain pit (was 'd' / text: empty class)
    put(23, c, ' ')
    put(24, c, ' ')

# rounded top corners (art pass): arc of radius ARC_R units in the corner
# cells, replacing the 1-cell diagonals 'q' / 'p'.
ARC_R = 24.0
ARC_L = (8 + ARC_R, 16 + ARC_R)          # centre, physics units
ARC_R_C = (312 - ARC_R, 16 + ARC_R)


def arc_solid(ux, uy):
    for (cx, cy), side in ((ARC_L, -1), (ARC_R_C, 1)):
        if uy < cy and (ux < cx if side < 0 else ux > cx):
            if math.hypot(ux - cx, uy - cy) > ARC_R:
                return True
    return False


for r in range(1, 4):
    for c in list(range(1, 5)) + list(range(35, 39)):
        if rows[r][c] in (' ', 'q', 'p'):
            put(r, c, 'a')                 # candidate arc cell (decided below)

pglyphs = {}          # physics code -> 8 bytes
gclass = [C_EMPTY] * 256
gnx = [0] * 256
gny = [0] * 256
next_code = [64]


def bitmap(fn):
    out = []
    for ly in range(8):
        b = 0
        for lx in range(8):
            if fn(lx, ly):
                b |= 0x80 >> lx
        out.append(b)
    return out


def unit(x, y):
    l = math.hypot(x, y)
    return (x / l, y / l)


def s7(v):
    return max(-127, min(127, int(round(v * 127))))


def new_pglyph(bits, cls=C_EMPTY, n=(0, 0)):
    code = next_code[0]
    next_code[0] += 1
    pglyphs[code] = bits
    gclass[code] = cls
    gnx[code] = s7(n[0])
    gny[code] = s7(n[1])
    return code


n_dl = unit(16, -8)
n_dr = unit(-16, -8)
P = {}
P['#'] = new_pglyph([0xFF] * 8, C_FULL)
P['\\'] = new_pglyph(bitmap(lambda x, y: x <= y), C_SHAPE, n_dl)
P['/'] = new_pglyph(bitmap(lambda x, y: x >= 7 - y), C_SHAPE, n_dr)
P['K'] = new_pglyph(bitmap(lambda x, y: x <= y), C_SLING, n_dl)
P['J'] = new_pglyph(bitmap(lambda x, y: x >= 7 - y), C_SLING, n_dr)
P['k'] = new_pglyph([0xFF] * 8, C_FULL)
P['T'] = new_pglyph([0x3C, 0x7E, 0xFF, 0xE7, 0xE7, 0xFF, 0x7E, 0x3C], C_TARGET)
P['f'] = new_pglyph([0x00, 0x18, 0x3C, 0x7E, 0x18, 0x18, 0x18, 0x00], C_LANE)
P['~'] = new_pglyph([0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00], C_SPIN)


def bump_in(lx, ly, dr, dc):
    px = dc * 8 + lx + 0.5 - 16
    py = dr * 8 + ly + 0.5 - 8
    return (px / 15.5) ** 2 + (py / 7.8) ** 2 <= 1.0


for i in range(8):
    dr, dc = divmod(i, 4)
    cx = dc * 8 + 4 - 16
    cy = (dr * 8 + 4 - 8) * 2
    P['B%d' % i] = new_pglyph(bitmap(lambda lx, ly, dr=dr, dc=dc: bump_in(lx, ly, dr, dc)),
                              C_BUMPER, unit(cx, cy))

# arc cells: bitmap from arc_solid, normal = centroid(open) - centroid(solid)
arc_cache = {}
for r in range(H):
    for c in range(W):
        if rows[r][c] != 'a':
            continue
        bits = bitmap(lambda lx, ly: arc_solid(c * 8 + lx + 0.5, (r * 8 + ly + 0.5) * 2))
        nset = sum(bin(b).count('1') for b in bits)
        if nset == 0:
            put(r, c, ' ')
            continue
        if nset == 64:
            put(r, c, '#')
            continue
        sx = sy = ox = oy = 0.0
        ns = no = 0
        for ly in range(8):
            for lx in range(8):
                ux, uy = lx + 0.5, (ly + 0.5) * 2
                if bits[ly] & (0x80 >> lx):
                    sx += ux; sy += uy; ns += 1
                else:
                    ox += ux; oy += uy; no += 1
        n = unit(ox / no - sx / ns, oy / no - sy / ns)
        key = tuple(bits)
        if key not in arc_cache:
            arc_cache[key] = new_pglyph(bits, C_SHAPE, n)
        P['a%d_%d' % (r, c)] = arc_cache[key]
        put(r, c, 'a%d_%d' % (r, c))

tbl_codes = [[32] * W for _ in range(H)]
for r in range(H):
    for c in range(W):
        ch = rows[r][c]
        if ch in P:
            tbl_codes[r][c] = P[ch]
NPHYS = next_code[0]


def cls_at(r, c):
    return gclass[tbl_codes[r][c]] if tbl_codes[r][c] >= 64 else C_EMPTY


def solid_px(x, y):
    """physics solidity of table pixel (x 0..319, scanline 0..199)."""
    r, c = y >> 3, x >> 3
    if r == 0:
        return True
    code = tbl_codes[r][c]
    if code < 64:
        return False
    cl = gclass[code]
    if cl in (C_EMPTY, C_LANE, C_SPIN):
        return False
    if cl in (C_FULL, C_TARGET):
        return True
    return bool(pglyphs[code][y & 7] & (0x80 >> (x & 7)))


# ======================================================================
# FLIPPERS (physics geometry unchanged)
# ======================================================================
PIV_ROW = 20
PIVOTS = [(12 * 8 + 4, PIV_ROW * 8 + 4), (27 * 8 + 4, PIV_ROW * 8 + 4)]
FLEN = 46
ANG = [25, 2, -25]
FB_ROW, FB_H = 18, 5
FB_COL = [11, 21]
FB_W = 8


def flip_geom(f, p):
    a = math.radians(ANG[p])
    dx, dy = math.cos(a), math.sin(a)
    if f == 1:
        dx = -dx
    nx, ny = -dy, dx
    if ny > 0:
        nx, ny = -nx, -ny
    return dx, dy, nx, ny


def flip_pixel(f, p, px, sl):
    """art pass flipper: rounded pivot, tapered bat, rounded tip, pivot pin."""
    pvx, pvs = PIVOTS[f]
    ux = px + 0.5 - pvx
    uy = (sl + 0.5 - pvs) * 2
    dx, dy, nx, ny = flip_geom(f, p)
    t = ux * dx + uy * dy
    d = ux * nx + uy * ny
    rr = math.hypot(ux, uy)
    if rr <= 1.6:
        return False                    # pivot pin (black dot)
    if rr <= 6.0:
        return True
    tip = FLEN - 1.0
    if 0 <= t <= tip:
        half = 5.6 - 3.0 * t / tip
        return abs(d) <= half
    if t > tip:
        return math.hypot(t - tip, d) <= 2.6
    return False


def flip_cells():
    """set of (r, c) table cells touched by any flipper pose."""
    s = set()
    for f in range(2):
        for p in range(3):
            for br in range(FB_H):
                for bc in range(FB_W):
                    r, c = FB_ROW + br, FB_COL[f] + bc
                    for ly in range(8):
                        for lx in range(8):
                            if flip_pixel(f, p, c * 8 + lx, r * 8 + ly):
                                s.add((r, c))
    return s


FLIP_CELLS = flip_cells()

# ======================================================================
# TABLE ART
# ======================================================================
cv = Canvas(W, H, aspect=2.0)

# --- solid / wall masks and the distance field
WALLSYM = set('#\\/qp')
solid = [[solid_px(x, y) for x in range(320)] for y in range(200)]


def is_wall_cell(r, c):
    ch = rows[r][c]
    return r == 0 or ch in WALLSYM or ch.startswith('a')


# for drawing, the chute mouths are notches in the top wall
NOTCH = {(0, c) for c in list(range(5, 8)) + list(range(32, 35))}
openp = [[(not solid[y][x]) or ((y >> 3, x >> 3) in NOTCH) for x in range(320)]
         for y in range(200)]
# targets, bumpers and slings count as "open" for the wall field
for y in range(200):
    for x in range(320):
        if solid[y][x] and not is_wall_cell(y >> 3, x >> 3):
            openp[y][x] = True

RMAX = 26.0
offs = []
for dy in range(-14, 15):
    for dx in range(-27, 28):
        dd = math.hypot(dx, dy * 2)
        if dd <= RMAX:
            offs.append((dd, dx, dy))
offs.sort()
# cells with no open pixel within 4 cells: skip (distance = big)
near = [[False] * W for _ in range(H)]
for r in range(H):
    for c in range(W):
        found = False
        for rr in range(max(0, r - 2), min(H, r + 3)):
            for cc in range(max(0, c - 4), min(W, c + 5)):
                for y in range(rr * 8, rr * 8 + 8):
                    if any(openp[y][cc * 8:cc * 8 + 8]):
                        found = True
                        break
                if found:
                    break
            if found:
                break
        near[r][c] = found
dist = [[0.0] * 320 for _ in range(200)]
for y in range(200):
    for x in range(320):
        if openp[y][x]:
            continue
        if not near[y >> 3][x >> 3]:
            dist[y][x] = 99.0
            continue
        d = 99.0
        for dd, dx, dy in offs:
            xx, yy = x + dx, y + dy
            if 0 <= xx < 320 and 0 <= yy < 200 and openp[yy][xx]:
                d = dd
                break
        dist[y][x] = d

# --- wall lines: double "maze" line hugging the playfield edge
for y in range(200):
    for x in range(320):
        if openp[y][x]:
            continue
        d = dist[y][x]
        if d <= 2.5 or 5.0 < d <= 7.5:
            cv.px(x, y, C['ltblue'])


def ell(cx, cy, rx, ry):
    return lambda ux, uy: ((ux - cx) / rx) ** 2 + ((uy - cy) / ry) ** 2 <= 1.0


# --- pop bumpers: rim ring, black gap, domed cap with a highlight crescent
BUMP_COL = [C['ltred'], C['ltcyan'], C['ltpurp']]   # Blinky, Inky, Pinky
for (r0, c0), col in zip(BUMPERS, BUMP_COL):
    cx, cy = c0 * 8 + 16, (r0 * 8 + 8) * 2

    def fb(ux, uy, cx=cx, cy=cy, col=col):
        e = ((ux - cx) / 15.5) ** 2 + ((uy - cy) / 15.6) ** 2
        if e > 1.0:
            return None
        if e > 0.74:
            return col                   # rim
        if e > 0.50:
            return None                  # gap
        # cap: highlight crescent (black) at the upper left
        h = ((ux - (cx - 4.5)) / 4.0) ** 2 + ((uy - (cy - 5.0)) / 3.2) ** 2
        if h <= 1.0 and ((ux - (cx - 3.0)) / 4.2) ** 2 + ((uy - (cy - 2.6)) / 3.6) ** 2 > 1.0:
            return None
        return col
    cv.fill(fb, c0 * 8, r0 * 8, c0 * 8 + 32, r0 * 8 + 16)
    for dr in range(2):
        for dc in range(4):
            cv.cfg[(r0 + dr, c0 + dc)] = col

# --- slingshots: one red kicker: rubber edge on the hypotenuse, a black groove 2 px in,
# a lamp window in the body
for r in range(15, 18):
    for c in range(9, 31):
        ch = rows[r][c]
        if ch not in 'KJk':
            continue
        for ly in range(8):
            for lx in range(8):
                x, y = c * 8 + lx, r * 8 + ly
                if c < 20:
                    s = y - x - 32            # >= 0 inside the left sling
                else:
                    s = x + y - 351           # >= 0 inside the right sling
                if s < 0:
                    continue
                if s == 2:
                    continue                  # groove
                if (r, c) in ((17, 11), (17, 28)) and 2 <= lx <= 5 and 3 <= ly <= 5:
                    continue                  # lamp window
                cv.px(x, y, C['ltred'])
        cv.cfg[(r, c)] = C['ltred']

# --- energizer targets: a big round pellet on a wall mount
TARGET_BITS_L = ["..xxxx..", ".xxxxxx.", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx", ".xxxxxx.", "..xxxx.."]
for r in (6, 8):
    for c, flip in ((1, False), (38, True)):
        for ly, row in enumerate(TARGET_BITS_L):
            for lx, chx in enumerate(row):
                if chx == 'x':
                    cv.px(c * 8 + lx, r * 8 + ly, C['dkcyan'])
        cv.cfg[(r, c)] = C['dkcyan']

# --- fruit lanes: cherry, strawberry, orange, bell
FRUIT = {
    14: (C['dkred'], ["....x...", "...x.x..", "..x...x.", ".x...xx.", "xxx.xxxx", "xxx.xxxx", "xxx..xx.", "........"]),
    17: (C['dkpurp'], ["..x.x...", "..xxx...", ".xxxxx..", "xx.x.xx.", "xxxxxxx.", ".x.x.x..", "..xxx...", "...x...."]),
    22: (C['dkyel'], ["....x...", "...xx...", ".xxxxx..", "xxxxxxx.", "xxxxxxx.", "xxxxxxx.", ".xxxxx..", "........"]),
    25: (C['dkgreen'], ["...x....", "..xxx...", ".xxxxx..", ".xxxxx..", ".xxxxx..", "xxxxxxx.", "...x....", "........"]),
}
for c, (col, bm) in FRUIT.items():
    for ly, row in enumerate(bm):
        for lx, chx in enumerate(row):
            if chx == 'x':
                cv.px(c * 8 + lx, 3 * 8 + ly, col)
    cv.cfg[(3, c)] = col

# --- spinner: a gate on two posts
SPIN = ["........", "........", "xxxxxxxx", "x......x", "xxxxxxxx", "........", "........", "........"]
for c in range(18, 22):
    for ly, row in enumerate(SPIN):
        for lx, chx in enumerate(row):
            if chx == 'x' and not (lx in (0, 7) and ly == 3 and c not in (18, 21)):
                cv.px(c * 8 + lx, 11 * 8 + ly, C['ltgrey'])
    cv.cfg[(11, c)] = C['ltgrey']
for c in (18, 21):                         # end posts
    x = c * 8 + (0 if c == 18 else 7)
    for ly in range(1, 6):
        cv.px(x, 11 * 8 + ly, C['ltgrey'])

# --- chute mouths ("tunnels" from the maze): yellow arrows below the notch
CHEV = ["........", "x......x", "xx....xx", ".xx..xx.", "..xxxx..", "...xx...", "........", "........"]
for c in (6, 33):
    for ly, row in enumerate(CHEV):
        for lx, chx in enumerate(row):
            if chx == 'x':
                cv.px(c * 8 + lx, 1 * 8 + ly, C['ltyel'])
    cv.cfg[(1, c)] = C['ltyel']

# --- playfield inserts (visual only): arrow lamps up the centre,
# a trail of dots toward the drain ("back to the maze")
ARROW = ["...xx...", "..xxxx..", ".xxxxxx.", "xxx..xxx", "xx....xx", "........", "........", "........"]
for r, col in ((13, C['ltyel']), (14, C['dkyel'])):
    for c in (19, 20):
        for ly, row in enumerate(ARROW):
            for lx, chx in enumerate(row):
                if chx == 'x':
                    xx = lx + (4 if c == 19 else -4)
                    if 0 <= xx < 8:
                        cv.px(c * 8 + xx, r * 8 + ly, col)
        cv.cfg[(r, c)] = col
DOT = ["........", "........", "...xx...", "..xxxx..", "...xx...", "........", "........", "........"]
# a row of pac-dots under the bumpers, like a maze corridor
for c in (4, 7, 10, 13, 16, 23, 26, 29, 32, 35):
    for ly, row in enumerate(DOT):
        for lx, chx in enumerate(row):
            if chx == 'x':
                cv.px(c * 8 + lx, 9 * 8 + ly, C['ltred'])
    cv.cfg[(9, c)] = C['ltred']
for r in (17, 19):
    for c in (19, 20):
        for ly, row in enumerate(DOT):
            for lx, chx in enumerate(row):
                if chx == 'x':
                    xx = lx + (4 if c == 19 else -4)
                    if 0 <= xx < 8:
                        cv.px(c * 8 + xx, r * 8 + ly, C['ltred'])
        cv.cfg[(r, c)] = C['ltred']

# --- funnel art (deep inside the solid side walls): Pac-Man and a ghost
def pacman_fn(cx, cy, rad, col, mouth_dir=0.0, mouth=0.75, eye=True):
    def f(ux, uy):
        dx, dy = ux - cx, uy - cy
        if math.hypot(dx, dy) > rad:
            return None
        a = math.atan2(dy, dx) - mouth_dir
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) < mouth / 2 and math.hypot(dx, dy) > rad * 0.12:
            return None
        if eye:
            ex = cx + rad * 0.15 * math.cos(mouth_dir) - rad * 0.0
            if math.hypot(ux - (cx + rad * 0.12 * (1 if math.cos(mouth_dir) >= 0 else -1)),
                          (uy - (cy - rad * 0.55)) * 0.9) < rad * 0.13:
                return None
        return col
    return f


def ghost_fn(cx, cy, w, h, col, eyes='L', feet=0, eyecol=None):
    """ghost of width w, height h (units) centred at cx; top at cy - h/2."""
    top = cy - h / 2
    bot = cy + h / 2

    def f(ux, uy):
        x = (ux - (cx - w / 2)) / w        # 0..1
        y = (uy - top) / h                 # 0..1
        if not (0 <= x <= 1 and 0 <= y <= 1):
            return None
        # dome
        if y < 0.5:
            if ((x - 0.5) / 0.5) ** 2 + ((y - 0.5) / 0.5) ** 2 > 1.0:
                return None
        # feet: 3 scallops
        if y > 0.82:
            ph = (x * 3 + feet * 0.5) % 1.0
            if abs(ph - 0.5) < (y - 0.82) / 0.18 * 0.5:
                return None
        # eyes
        dxp = {'L': -0.06, 'R': 0.06, 'U': 0, 'D': 0}[eyes]
        dyp = {'L': 0, 'R': 0, 'U': -0.06, 'D': 0.06}[eyes]
        for exc in (0.3, 0.7):
            ex, ey = exc + dxp * 0.5, 0.40 + dyp * 0.5
            if ((x - ex) / 0.13) ** 2 + ((y - ey) / 0.17) ** 2 <= 1.0:
                px_, py_ = exc + dxp * 1.6, 0.42 + dyp * 1.6
                if ((x - px_) / 0.06) ** 2 + ((y - py_) / 0.08) ** 2 <= 1.0:
                    return col              # pupil (body colour)
                return eyecol               # eye white or black
        return col
    return f


# left funnel: Pac-Man chasing a line of dots up the slope
cv.fill(pacman_fn(20, 18.6 * 16, 15, C['ltyel'], mouth_dir=-1.1, mouth=1.1),
        0, 15 * 8, 6 * 8, 20 * 8)
for i, (x, y) in enumerate(((40, 16.9 * 16), (48, 15.9 * 16), (56, 14.9 * 16))):
    cv.fill(lambda ux, uy, x=x, y=y: C['ltyel'] if math.hypot(ux - x, uy - y) <= 2.6 else None,
            0, 10 * 8, 10 * 8, 20 * 8)
# right funnel: a frightened (blue) ghost running away
cv.fill(ghost_fn(320 - 22, 18.3 * 16, 26, 26, C['ltblue'], eyes='R', eyecol=None),
        33 * 8, 15 * 8, 40 * 8, 20 * 8)

# --- apron: "MAZE" under the drain, arrows on either side
cv.text(24, 18, "MAZE", C['ltred'])
DNTRI = ["........", ".xxxxx..", "..xxx...", "...x....", "........", "........", "........", "........"]
for c in (17, 22):
    for ly, row in enumerate(DNTRI):
        for lx, chx in enumerate(row):
            if chx == 'x':
                cv.px(c * 8 + lx + (-1 if c == 17 else 2), 23 * 8 + ly + 2, C['ltred'])
    cv.cfg[(23, c)] = C['ltred']

# --- top wall: title plate
cv.text(0, 14, "BABY PAC-MAN", C['ltyel'])
for c in (13, 26):
    for y in range(8):
        for x in range(8):
            cv.px(c * 8 + x, y, 0)

# ======================================================================
# PANEL ART (VDC columns 0-19 and 60-79), bank 1
# ======================================================================
L = Canvas(20, 25, aspect=2.0)
R = Canvas(20, 25, aspect=2.0)

# logo letters: 11x7 design grid of 2 px x 2 scanline blocks (22 x 14 px)
LOGO = {
    'B': ["#########..", "###....###.", "###....###.", "#########..", "###....###.", "###....###.", "#########.."],
    'A': ["..#######..", ".###...###.", "###.....###", "###########", "###.....###", "###.....###", "###.....###"],
    'Y': ["###.....###", "###.....###", ".###...###.", "..#######..", "....###....", "....###....", "....###...."],
    'P': ["#########..", "###....###.", "###....###.", "#########..", "###........", "###........", "###........"],
    'M': ["###.....###", "####...####", "#####.#####", "###.###.###", "###..#..###", "###.....###", "###.....###"],
    'N': ["###.....###", "####....###", "#####...###", "###.###.###", "###...#####", "###....####", "###.....###"],
    'G': ["..########.", ".###.......", "###........", "###...#####", "###.....###", ".###....###", "..#######.."],
    'O': ["..#######..", ".###...###.", "###.....###", "###.....###", "###.....###", ".###...###.", "..#######.."],
    '!': ["###", "###", "###", "###", "###", "...", "###"],
    '-': ["....", "....", "....", "####", "....", "....", "...."],
}


def logo_letter(cvs, ch, x, y, col):
    """draw logo letter with its top-left at pixel (x, y); returns width px."""
    if ch == 'C':                      # Pac-Man stands in for the C
        cvs.fill(pacman_fn(x + 11, (y + 7) * 2, 13.5, col, mouth_dir=0.0, mouth=1.2, eye=False),
                 x, y, x + 24, y + 15)
        return 24
    g = LOGO[ch]
    for gy, row in enumerate(g):
        for gx, chx in enumerate(row):
            if chx == '#':
                for k in range(2):
                    for j in range(2):
                        cvs.px(x + gx * 2 + j, y + gy * 2 + k, col)
    # round the outer corners a touch
    return len(g[0]) * 2 + 2


def logo_word(cvs, word, cell_col, cell_row, col, widths=None):
    x = cell_col * 8
    for ch in word:
        w = logo_letter(cvs, ch, x + 1, cell_row * 8 + 1, col)
        x += 24 if ch != '-' else 8
    return x


def hline(cvs, row, col):
    """double horizontal rule through the middle of a cell row"""
    for x in range(cvs.W):
        cvs.px(x, row * 8 + 2, col)
        cvs.px(x, row * 8 + 5, col)


# ----- LEFT panel: marquee, chase scene, tally, GO!, controls
logo_word(L, "BABY", 4, 0, C['ltpurp'])
logo_word(L, "PAC-MAN", 0, 2, C['ltyel'])
# chase scene row 5-6: ghosts after Pac-Man
GH = [C['ltred'], C['ltpurp'], C['ltcyan'], C['dkyel']]
for i, col in enumerate(GH):
    cx = 8 * (3 + 4 * i) + 8 + 4
    L.fill(ghost_fn(cx, 5.9 * 16, 20, 20, col, eyes='L', feet=i & 1, eyecol=None), 0, 4 * 8, 160, 7 * 8)
L.fill(pacman_fn(12, 5.9 * 16, 10.5, C['ltyel'], mouth_dir=math.pi, mouth=1.0), 0, 4 * 8, 24, 7 * 8)
for x in (28, 36):
    pass
hline(L, 7, C['ltblue'])
L.text(8, 2, "THIS BALL EARNS", C['ltgrey'])
L.text(9, 4, "ENERGIZERS", C['ltcyan'])
L.text(10, 4, "FRUIT LVL", C['ltgreen'])
L.text(11, 4, "BONUS", C['ltyel'])
# icons in column 2: energizer, cherry, star
ICON = {
    9: (C['ltcyan'], ["..xxxx..", ".xxxxxx.", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx", ".xxxxxx.", "..xxxx..", "........"]),
    10: (C['ltred'], FRUIT[14][1]),
    11: (C['ltyel'], ["...x....", "...x....", "xxxxxxx.", ".xxxxx..", "..xxx...", ".xx.xx..", "x.....x.", "........"]),
}
for r, (col, bm) in ICON.items():
    for ly, row in enumerate(bm):
        for lx, chx in enumerate(row):
            if chx == 'x':
                L.px(2 * 8 + lx, r * 8 + ly, col)
hline(L, 12, C['ltblue'])
hline(L, 16, C['ltblue'])
L.text(17, 2, "FLIPPERS:", C['ltyel'])
L.text(18, 2, "PADDLE BUTTONS", C['ltgrey'])
L.text(19, 2, "OR JOYSTICK", C['ltgrey'])
L.text(20, 2, "LEFT / RIGHT", C['ltgrey'])
hline(L, 21, C['ltblue'])
# lamp row: pac-dots with two energizers (blink)
for i in range(18):
    x = 8 + i * 8
    big = i in (2, 15)
    for ly in range(8):
        for lx in range(8):
            if big:
                on = (lx - 3.5) ** 2 + ((ly - 3.5) * 1.0) ** 2 <= 9.5
            else:
                on = 3 <= lx <= 4 and 3 <= ly <= 4
            if on:
                L.px(x + lx, 22 * 8 + ly, C['ltred'] if not big else C['ltcyan'])
    if big:
        L.flags[(22, 1 + i)] = A_BLINK
L.text(23, 2, "FAN-MADE HOMAGE", C['dkgrey'])

# ----- RIGHT panel: score box, big Blinky and Pac-Man, cue area
# score box rows 0-3, columns 1-18 (VDC 61-78)
for x in range(8 + 3, 19 * 8 - 3):
    R.px(x, 0 * 8 + 6, C['ltblue'])
    R.px(x, 3 * 8 + 1, C['ltblue'])
for y in range(6, 3 * 8 + 2):
    R.px(8 + 3, y, C['ltblue'])
    R.px(19 * 8 - 4, y, C['ltblue'])
R.text(1, 2, "SCORE", C['white'])
# big ghost (Blinky) with white eye cells and big Pac-Man
# ghost: columns 11-18 (64 px), rows 6-10; eyes in their own cells (white)
gx0, gy0 = 11 * 8, 6 * 8
gw, gh = 62, 68          # units (62 px wide, 34 scanlines)


def big_ghost(ux, uy):
    x = (ux - gx0) / gw
    y = (uy - gy0 * 2) / gh
    if not (0 <= x <= 1 and 0 <= y <= 1):
        return None
    if y < 0.5 and ((x - 0.5) / 0.5) ** 2 + ((y - 0.5) / 0.5) ** 2 > 1.0:
        return None
    if y > 0.84:
        ph = (x * 4) % 1.0
        if abs(ph - 0.5) < (y - 0.84) / 0.16 * 0.5:
            return None
    return C['ltred']


R.fill(big_ghost, 0, 5 * 8, 160, 12 * 8)
# eye whites: two cells each (8 px x 16 lines) - eyes looking left
for ec in (12, 15):
    for r in (7, 8):
        R.cfg[(r, ec)] = C['white']
        R.cfg[(r, ec + 1)] = C['white']
    ex = ec * 8 + 8
    ey = 8 * 8
    R.fill(lambda ux, uy, ex=ex, ey=ey: (C['white'] if ((ux - ex) / 6.5) ** 2 + ((uy - ey * 2) / 12.5) ** 2 <= 1.0
                                          else 0),
           ec * 8, 7 * 8, ec * 8 + 16, 9 * 8)
    R.fill(lambda ux, uy, ex=ex, ey=ey: (0 if ((ux - (ex - 3)) / 3.0) ** 2 + ((uy - (ey * 2 + 3)) / 5.0) ** 2 <= 1.0
                                         else None),
           ec * 8, 7 * 8, ec * 8 + 16, 9 * 8)
# big Pac-Man facing the ghost (right), columns 1-8, rows 6-10
R.fill(pacman_fn(5 * 8, 8.6 * 16, 32, C['ltyel'], mouth_dir=0.0, mouth=1.0), 0, 5 * 8, 10 * 8, 12 * 8)
# dots between them
for x in (82,):
    R.fill(lambda ux, uy, x=x: C['ltred'] if math.hypot(ux - x, uy - 8.6 * 16) <= 2.2 else None,
           9 * 8, 7 * 8, 11 * 8, 10 * 8)
hline(R, 12, C['ltblue'])
R.text(13, 2, "HIT THE", C['ltgrey'])
R.text(14, 2, "ENERGIZERS:", C['ltcyan'])
R.text(15, 2, "POWER FOR THE", C['ltgrey'])
R.text(16, 2, "MAZE!", C['ltgrey'])
R.text(17, 2, "FRUIT LANES:", C['ltgreen'])
R.text(18, 2, "BIGGER FRUIT", C['ltgrey'])
hline(R, 19, C['ltblue'])
hline(R, 23, C['ltblue'])

# GO! (big logo letters), printed at run time on the left panel rows 13-14
go_canvas = Canvas(7, 2, aspect=2.0)
x = 0
for ch in "GO!":
    w = logo_letter(go_canvas, ch, x + 1, 1, C['white'])
    x += 24 if ch != '!' else 8

# ======================================================================
# CELL RESOLUTION, GLYPH BANKS
# ======================================================================
font = font_charset_0_63()
bank1 = Bank("bank1", [c for c in range(64, 256) if not (240 <= c <= 247)],
             {i: font[i] for i in range(64)})
for c in range(240, 248):
    bank1.glyphs[c] = [0] * 8
bank0 = Bank("bank0", range(64, 240), {32: [0] * 8})
clash = []

PLAY_DEFAULT = C['white']           # ball colour in empty playfield cells

vis_codes = [[32] * W for _ in range(H)]
vis_attrs = [[PLAY_DEFAULT] * W for _ in range(H)]
NEED_B0 = set()
for r in range(H):
    for c in range(W):
        # any open (ball-reachable) cell within one cell -> must be bank 0
        for rr in range(max(0, r - 1), min(H, r + 2)):
            for cc in range(max(0, c - 1), min(W, c + 2)):
                if rr > 0 and not (cls_at(rr, cc) in (C_FULL,)) and not (rr >= 23):
                    NEED_B0.add((r, c))
for (r, c) in FLIP_CELLS:
    NEED_B0.add((r, c))
for r in range(H):
    for c in range(W):
        if (r, c) in cv.text_cells:
            code, col = cv.text_cells[(r, c)]
            vis_codes[r][c] = code
            vis_attrs[r][c] = col | A_ALT | cv.flags.get((r, c), 0)
            continue
        fg, bits, dropped = resolve_cell(cv, r, c)
        if dropped:
            clash.append(("table", r, c, dropped))
        if fg is None:
            vis_codes[r][c] = 32
            vis_attrs[r][c] = PLAY_DEFAULT
            continue
        if (r, c) in NEED_B0:
            vis_codes[r][c] = bank0.alloc(bits)
            vis_attrs[r][c] = fg | cv.flags.get((r, c), 0)
        else:
            vis_codes[r][c] = bank1.alloc(bits)
            vis_attrs[r][c] = fg | A_ALT | cv.flags.get((r, c), 0)


def resolve_panel(cvs, name):
    codes = [[32] * 20 for _ in range(H)]
    attrs = [[A_ALT | C['ltgrey']] * 20 for _ in range(H)]
    for r in range(H):
        for c in range(20):
            if (r, c) in cvs.text_cells:
                code, col = cvs.text_cells[(r, c)]
                codes[r][c] = code
                attrs[r][c] = col | A_ALT | cvs.flags.get((r, c), 0)
                continue
            fg, bits, dropped = resolve_cell(cvs, r, c)
            if dropped:
                clash.append((name, r, c, dropped))
            if fg is None:
                continue
            codes[r][c] = bank1.alloc(bits)
            attrs[r][c] = fg | A_ALT | cvs.flags.get((r, c), 0)
    return codes, attrs


lc, la = resolve_panel(L, "left")
rc_, ra = resolve_panel(R, "right")
gc, ga = resolve_panel(go_canvas, "go") if False else (None, None)
go_rows = []
for r in range(2):
    rowc = []
    for c in range(7):
        fg, bits, dropped = resolve_cell(go_canvas, r, c)
        rowc.append(bank1.alloc(bits) if fg is not None else 32)
    go_rows.append(rowc)

# ======================================================================
# FLIPPER BLOCKS (visual codes, bank 0)
# ======================================================================
flip_codes = []
for f in range(2):
    for p in range(3):
        blk = []
        for br in range(FB_H):
            for bc in range(FB_W):
                r, c = FB_ROW + br, FB_COL[f] + bc
                base = vis_codes[r][c]
                basebits = bank0.glyphs.get(base, [0] * 8) if base >= 64 else [0] * 8
                fb = bitmap(lambda lx, ly: flip_pixel(f, p, c * 8 + lx, r * 8 + ly))
                if not any(fb):
                    blk.append(base)
                    continue
                bits = [a | b for a, b in zip(basebits, fb)]
                blk.append(bank0.alloc(bits))
        flip_codes.append(blk)
for (r, c) in FLIP_CELLS:
    vis_attrs[r][c] = C['ltyel']
# the rest pose is what the static table shows
for br in range(FB_H):
    for bc in range(FB_W):
        pass

# ======================================================================
# LIGHTS
# ======================================================================
lit_row = [6, 6, 8, 8, 3, 3, 3, 3]
lit_col = [1, 38, 1, 38, 14, 17, 22, 25]
lit_off = [C['dkcyan']] * 4 + [C['dkred'], C['dkpurp'], C['dkyel'], C['dkgreen']]
lit_on = [C['ltcyan']] * 4 + [C['ltred'], C['ltpurp'], C['ltyel'], C['ltgreen']]
for i in range(8):
    vis_attrs[lit_row[i]][lit_col[i]] = lit_off[i]

# ======================================================================
# BALL: 7 x 4, symmetric about the centre (-3..+3 px)
# ======================================================================
BALL = [0b0111110, 0b1101111, 0b1111111, 0b0111110]
ball_bits = []
for sh in range(8):
    for row in BALL:
        v = (row << 9) >> sh
        ball_bits += [(v >> 8) & 0xFF, v & 0xFF]

# ======================================================================
# OUTPUT
# ======================================================================
if bank0.used() > 177:
    print("mktable: bank 0 overflow", file=sys.stderr)
    sys.exit(1)


def sb(v):
    return v & 0xFF


out = []
o = out.append
o("; generated by tools/mktable.py - do not edit")
o(".export tbl_codes, gclass, gnx, gny, pglyph, flip_codes")
o(".export vis_codes, vis_attrs, pan_codes, pan_attrs, glyph0, glyph1")
o(".export fl_dx, fl_dy, fl_nx, fl_ny, ball_bits, lit_row, lit_col, lit_on, lit_off")
o(".export go_big0, go_big1")
o("PIVL_X = %d" % PIVOTS[0][0])
o("PIVR_X = %d" % PIVOTS[1][0])
o("PIV_SL = %d" % PIVOTS[0][1])
o("FLEN = %d" % FLEN)
o("FB_ROW = %d" % FB_ROW)
o("FB_H = %d" % FB_H)
o("FB_W = %d" % FB_W)
o("FB_COLL = %d" % FB_COL[0])
o("FB_COLR = %d" % FB_COL[1])
o("NGLYPHS = %d" % NPHYS)
o(".exportzp PIVL_X, PIVR_X, PIV_SL, FLEN, FB_ROW, FB_H, FB_W, FB_COLL, FB_COLR, NGLYPHS")
o('.segment "RODATA"')


def emit(name, data, per=20):
    o(name + ":")
    for i in range(0, len(data), per):
        o("  .byte " + ",".join("$%02X" % sb(x) for x in data[i:i + per]))


emit("tbl_codes", [tbl_codes[r][c] for r in range(H) for c in range(W)])
emit("gclass", gclass)
emit("gnx", gnx)
emit("gny", gny)
pg = []
for code in range(64, NPHYS):
    pg += pglyphs[code]
emit("pglyph", pg, 16)
emit("vis_codes", [vis_codes[r][c] for r in range(H) for c in range(W)])
emit("vis_attrs", [vis_attrs[r][c] for r in range(H) for c in range(W)])
pc, pa = [], []
for r in range(H):
    pc += lc[r] + rc_[r]
    pa += la[r] + ra[r]
emit("pan_codes", pc)
emit("pan_attrs", pa)
g0 = []
for code in range(64, 256):
    g0 += bank0.glyphs.get(code, [0] * 8)
emit("glyph0", g0, 16)
g1 = []
for code in range(256):
    g1 += bank1.glyphs.get(code, [0] * 8)
emit("glyph1", g1, 16)
fc = []
for blk in flip_codes:
    fc += blk
emit("flip_codes", fc)
dx_, dy_, nx_, ny_ = [], [], [], []
for f in range(2):
    for p in range(3):
        dx, dy, nx, ny = flip_geom(f, p)
        dx_.append(s7(dx)); dy_.append(s7(dy)); nx_.append(s7(nx)); ny_.append(s7(ny))
emit("fl_dx", dx_)
emit("fl_dy", dy_)
emit("fl_nx", nx_)
emit("fl_ny", ny_)
emit("ball_bits", ball_bits, 16)
emit("lit_row", lit_row)
emit("lit_col", lit_col)
emit("lit_on", lit_on)
emit("lit_off", lit_off)
emit("go_big0", go_rows[0] + [0])
emit("go_big1", go_rows[1] + [0])

open(sys.argv[1], "w").write("\n".join(out) + "\n")
print("mktable: physics codes 64..%d; bank0 %d/176 used, bank1 %d/256 used" %
      (NPHYS - 1, bank0.used() - 1, bank1.used()))
print("colour clashes (cell: dropped pixels):",
      ", ".join("%s(%d,%d):%d" % x for x in clash) if clash else "none")
for r in range(H):
    print("".join((ch[0] if len(ch) == 1 else ('B' if ch[0] == 'B' else 'a')) for ch in rows[r]))

# ---------------------------------------------------------------- preview
if len(sys.argv) > 2:
    codes80, attrs80 = [], []
    for r in range(H):
        codes80 += lc[r] + [vis_codes[r][c] for c in range(W)] + rc_[r]
        attrs80 += la[r] + [vis_attrs[r][c] for c in range(W)] + ra[r]
    # ROM font is not available to the generator: show bank 0 text codes blank
    b0 = dict(bank0.glyphs)
    # rest-pose flippers on the static preview
    for f in range(2):
        blk = flip_codes[f * 3]
        for br in range(FB_H):
            for bc in range(FB_W):
                r, c = FB_ROW + br, FB_COL[f] + bc
                codes80[r * 80 + 20 + c] = blk[br * FB_W + bc]
    preview_vdc(sys.argv[2] + "-table.png", codes80, attrs80, b0, bank1.glyphs, yscale=2)
    lit = list(attrs80)
    for i in range(8):
        lit[lit_row[i] * 80 + 20 + lit_col[i]] = lit_on[i]
    for f in range(2):
        blk = flip_codes[f * 3 + 2]
        for br in range(FB_H):
            for bc in range(FB_W):
                r, c = FB_ROW + br, FB_COL[f] + bc
                codes80[r * 80 + 20 + c] = blk[br * FB_W + bc]
    preview_vdc(sys.argv[2] + "-table-lit.png", codes80, lit, b0, bank1.glyphs, yscale=2)
