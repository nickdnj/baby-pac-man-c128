#!/usr/bin/env python3
"""mktable2.py - pinball table v2 ("faithful layout"), ca65 source.

Layout inspired by Bally Midway's 1982 Baby Pac-Man playfield (our own pixel
art; an homage, not a copy): rounded top whose corners turn into two side
lanes (FRUITS left, TUNNEL right), a wooden arch at the top centre (the
tunnel mouth the ball comes out of), a round-topped central block with four
numbered columns of PAC / MAN drop targets around a centre lane with arrows
and TIMER, two pop bumpers, the Tier 2 funnel / slingshots / flippers /
drain, a pink ghost with a butterfly net, a red ghost, and the stork bringing
baby Pac-Man on the apron. Same data interface as mktable.py plus lit_h,
NLIGHTS and lane triggers (pinball.s built with -D TABLE2).

(mktable.py text follows for the shared parts.)

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
# side lanes: guide walls at columns 4 / 35 (rows 3-8); the lane is columns
# 1-3 / 36-38, open at the top (the rounded corner turns the ball in) and at
# the bottom onto the funnel slope. Rollover triggers on row 8.
for r in range(3, 9):
    put(r, 4, '#')
    put(r, 35, '#')
for c in (1, 2, 3, 36, 37, 38):
    put(8, c, 'r')
# wooden arch (tunnel mouth) at the top centre: legs at columns 17 and 22,
# rows 1-3; the pocket (18-21) is where the ball is served
for r in range(1, 4):
    put(r, 17, 'W')
    put(r, 22, 'W')
BUMPERS = ((2, 8), (2, 28))
for r0, c0 in BUMPERS:                  # pop bumpers 4x2
    for dr in range(2):
        for dc in range(4):
            put(r0 + dr, c0 + dc, 'B%d' % (dr * 4 + dc))
# central block: 8 drop targets, 4 numbered columns (15, 16, 23, 24), each a
# PAC target (rows 7-9) over a MAN target (rows 11-13)
TCOLS = (15, 16, 23, 24)
for c in TCOLS:
    for r in list(range(7, 10)) + list(range(11, 14)):
        put(r, c, 'T')
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
for c in range(17, 23):                 # drain pit
    put(23, c, ' ')
    put(24, c, ' ')

# rounded top corners: arc of radius ARC_R px (units) turning the top wall
# into the outer wall of each side lane
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
    for c in list(range(1, 4)) + list(range(36, 39)):
        if rows[r][c] == ' ':
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
P['T'] = new_pglyph([0xFF] * 8, C_TARGET)
P['r'] = new_pglyph([0x00] * 8, C_LANE)
P['W'] = new_pglyph([0xFF] * 8, C_FULL)


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
BUMP_COL = [C['ltcyan'], C['dkyel']]                # Inky, Clyde
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


# text in bank 0 (ROM font, codes 0-63) for cells the ball can cross
text0 = {}                               # (r, c) -> (code, colour)


def t0(row, col, txt, colour):
    for i, ch in enumerate(txt):
        if ch != ' ':
            text0[(row, col + i)] = (scr_code(ch), colour)


def bm(rows_, x, y, col, canvas=None):
    canvas = canvas or cv
    for ly, row in enumerate(rows_):
        for lx, chx in enumerate(row):
            if chx == 'x':
                canvas.px(x + lx, y + ly, col)


# --- wooden arch: the tunnel mouth at the top centre (legs 17 / 22)
WOOD = C['dkyel']
def arch_fn(ux, uy):
    """thick rounded arch: outer half-ellipse over the legs, inner pocket
    with a round top (VDC pixels are half as wide as a line is tall, so
    horizontal radii are doubled)"""
    x, y = ux, uy / 2.0                  # pixels / scanlines
    cx = 160.0
    if y < 14:
        if ((x - cx) / 24.0) ** 2 + ((y - 14) / 14.0) ** 2 > 1.0:
            return None
    elif not (136 <= x < 184):
        return None
    if y < 16:
        if ((x - cx) / 15.0) ** 2 + ((y - 16) / 9.0) ** 2 <= 1.0:
            return None
    elif 145 <= x < 175:
        return None
    # wood grain: dark seams on the legs
    if (x < 145 or x >= 175) and y >= 14 and int(y) % 6 == 5 and 1 <= (x % 8) <= 6:
        return None
    return WOOD


cv.fill(arch_fn, 17 * 8, 0, 23 * 8, 4 * 8)
for r in range(0, 4):
    for c in range(17, 23):
        cv.cfg[(r, c)] = WOOD

# --- side lanes: FRUITS reading down the left lane, TUNNEL down the right
LANE_ROWS = range(2, 8)
for i, ch in enumerate("FRUITS"):
    t0(2 + i, 2, ch, C['dkred'])
for i, ch in enumerate("TUNNEL"):
    t0(2 + i, 37, ch, C['dkcyan'])
t0(9, 1, "500", C['ltgrey'])
t0(9, 35, "1000", C['ltgrey'])
# rollover arrows (up) above the values
UPA = ["...x....", "..xxx...", ".xxxxx..", "xx.x.xx.", "...x....", "...x....", "........", "........"]

# --- fruit cluster at the top of the FRUITS loop
FRUITS_ART = [
    (5, C['ltred'], ["....x...", "...x.x..", "..x...x.", ".xx..xx.", "xxxx.xxx", "xxxx.xxx", ".xx...x.", "........"]),
    (6, C['ltpurp'], [".x.x.x..", "..xxx...", ".xxxxx..", "xx.x.xx.", "xxxxxxx.", ".x.x.x..", "..xxx...", "...x...."]),
    (7, C['dkyel'], ["....x...", "...xx...", ".xxxxx..", "xxxxxxx.", "xxxxxxx.", "xxxxxxx.", ".xxxxx..", "........"]),
]
for c, col, rows_ in FRUITS_ART:
    bm(rows_, c * 8, 1 * 8, col)
    cv.cfg[(1, c)] = col
for c, col, rows_ in ((32, C['ltred'], FRUITS_ART[0][2]), (33, C['dkyel'], FRUITS_ART[2][2])):
    bm(rows_, c * 8, 1 * 8, col)
    cv.cfg[(1, c)] = col

# --- central block: round-topped yellow outline, 4 numbered target columns
PANEL = C['ltyel']
PX0, PX1 = 14 * 8 + 3, 26 * 8 - 4        # outline x (px)
PY1 = 14 * 8 + 3                         # bottom line (scanline)
PCX, PCY, PR = (PX0 + PX1) / 2.0, 6 * 8 + 4, (PX1 - PX0) / 2.0


def panel_fn(ux, uy):
    x, y = ux, uy / 2.0
    # sides
    if PCY <= y <= PY1 and (abs(x - PX0) < 1 or abs(x - PX1) < 1):
        return PANEL
    if abs(y - PY1) < 0.6 and PX0 <= x <= PX1:
        return PANEL
    # round top: ellipse arc (rx = PR px, ry = 18 lines)
    if y < PCY:
        e = ((x - PCX) / PR) ** 2 + ((y - PCY) / 18.0) ** 2
        if 0.86 <= e <= 1.0:
            return PANEL
    return None


cv.fill(panel_fn, 13 * 8, 3 * 8, 27 * 8, 15 * 8)
# target inserts: rounded block with the letter cut out (our bold font)
from artlib import font_bits
TARGET_OFF, TARGET_ON = C['dkyel'], C['ltyel']
for c in TCOLS:
    for r, ch in zip(list(range(7, 10)) + list(range(11, 14)), "PACMAN"):
        g = font_bits(ch)
        for ly in range(8):
            for lx in range(8):
                corner = (lx in (0, 7)) and (ly in (0, 7))
                # letter (7x7) sits 1 px in from the top-left of the insert
                gx, gy = lx - 1, ly - 1
                letter = 0 <= gx < 7 and 0 <= gy < 7 and (g[gy] & (0x80 >> gx))
                if not corner and not letter:
                    cv.px(c * 8 + lx, r * 8 + ly, TARGET_OFF)
        cv.cfg[(r, c)] = TARGET_OFF
# centre lane: up arrows (alternating greens) and TIMER
ARROW = ["...xx...", "..xxxx..", ".xxxxxx.", "xxx..xxx", "xx....xx", "........", "........", "........"]
for i, r in enumerate(range(7, 14)):
    col = C['ltgreen'] if i % 2 == 0 else C['dkgreen']
    for c in (19, 20):
        for ly, row in enumerate(ARROW):
            for lx, chx in enumerate(row):
                if chx == 'x':
                    xx = lx + (4 if c == 19 else -4)
                    if 0 <= xx < 8:
                        cv.px(c * 8 + xx, r * 8 + ly, col)
        cv.cfg[(r, c)] = col
# column numbers between the PAC and MAN groups (row 10)
t0(10, 15, "1", C['ltyel'])
t0(10, 16, "2", C['ltyel'])
t0(10, 23, "3", C['ltyel'])
t0(10, 24, "4", C['ltyel'])
t0(15, 18, "TIMER", C['ltgreen'])
t0(16, 14, "SPELL PAC-MAN", C['ltyel'])

# --- deep wall art: pink ghost with a butterfly net (left), red ghost (right)
cv.fill(ghost_fn(22, 17.7 * 16, 30, 32, C['ltpurp'], eyes='R', eyecol=None),
        0, 15 * 8, 6 * 8, 20 * 8)
NET = C['white']
def net_fn(ux, uy):
    x, y = ux, uy / 2.0
    # hoop deep in the wall (rows 13-14, columns 0-2), handle to the ghost
    e = ((x - 13) / 8.0) ** 2 + ((y - 112) / 5.0) ** 2
    if 0.55 <= e <= 1.0:
        return NET
    t = (y - 117) / 17.0
    if 0 <= t <= 1 and abs(x - (19 + 7 * t)) < 0.8:
        return NET
    return None
cv.fill(net_fn, 0, 12 * 8, 6 * 8, 17 * 8)
cv.fill(ghost_fn(320 - 22, 17.7 * 16, 30, 32, C['ltred'], eyes='L', eyecol=None),
        34 * 8, 15 * 8, 40 * 8, 20 * 8)

# --- apron: the stork bringing baby Pac-Man (left), MAZE under the drain
STORK = C['white']
STORK_ROWS = [
    "..............xx..........................",
    "............xxxxx.........................",
    "...........xxxxxxxx.......................",
    "..xxxxxxxxxxxxxxxx.xx.....................",
    ".xxxxxxxxxxxxxxxxxxxxxxxxxxxx.............",
    "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx........",
    "....xxxxxxxxxxxxxxxxxxxxxx......xxxxxx....",
    ".......xxxxxxxxxxxxxxxx...........xxxx....",
    "...........xxxxxxxx...............xx......",
    ".............x..x.................x.......",
    "............x..x..................x.......",
]
bm(STORK_ROWS, 3 * 8, 22 * 8 + 3, STORK)
for r in (22, 23, 24):
    for c in range(3, 9):
        cv.cfg[(r, c)] = STORK
BEAK = C['dkyel']
bm(["xxxxxxx.", ".xxxxx..", "..xx...."], 9 * 8 + 2, 23 * 8 + 1, BEAK)
cv.cfg[(23, 9)] = BEAK
# the bundle with baby Pac-Man hanging from the beak
cv.fill(pacman_fn(11 * 8 + 4, (23 * 8 + 4) * 2, 7.5, C['ltyel'], mouth_dir=0.0, mouth=1.0),
        11 * 8, 23 * 8, 12 * 8, 24 * 8)
cv.text(24, 18, "MAZE", C['ltred'])
DNTRI = ["........", ".xxxxx..", "..xxx...", "...x....", "........", "........", "........", "........"]
for c in (17, 22):
    for ly, row in enumerate(DNTRI):
        for lx, chx in enumerate(row):
            if chx == 'x':
                cv.px(c * 8 + lx + (-1 if c == 17 else 2), 23 * 8 + ly + 2, C['ltred'])
    cv.cfg[(23, c)] = C['ltred']

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
    10: (C['ltred'], FRUITS_ART[0][2]),
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
R.text(13, 2, "SPELL PAC-MAN:", C['ltyel'])
R.text(14, 2, "A COLUMN OR A", C['ltgrey'])
R.text(15, 2, "WORD = ENERGIZER", C['ltcyan'])
R.text(16, 2, "FOR THE MAZE!", C['ltgrey'])
R.text(17, 2, "FRUITS LANE:", C['ltred'])
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
        if (r, c) in text0:              # ROM font, bank 0 (ball can cross)
            code, col = text0[(r, c)]
            vis_codes[r][c] = code
            vis_attrs[r][c] = col
            continue
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
# targets 0-3 = PAC (columns 1-4), 4-7 = MAN; 8 = FRUITS lane, 9 = TUNNEL
lit_row = [7, 7, 7, 7, 11, 11, 11, 11, 2, 2]
lit_col = list(TCOLS) + list(TCOLS) + [2, 37]
lit_h = [3] * 8 + [6, 6]
lit_off = [TARGET_OFF] * 8 + [C['dkred'], C['dkcyan']]
lit_on = [TARGET_ON] * 8 + [C['ltred'], C['ltcyan']]
NLIGHTS = len(lit_row)
for i in range(NLIGHTS):
    for k in range(lit_h[i]):
        vis_attrs[lit_row[i] + k][lit_col[i]] = lit_off[i]

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
o(".export go_big0, go_big1, lit_h")
o("NLIGHTS = %d" % NLIGHTS)
o("SERVE_X = %d" % 160)
o(".exportzp NLIGHTS, SERVE_X")
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
emit("lit_h", lit_h)
emit("go_big0", go_rows[0] + [0])
emit("go_big1", go_rows[1] + [0])

open(sys.argv[1], "w").write("\n".join(out) + "\n")
print("mktable2: physics codes 64..%d; bank0 %d/176 used, bank1 %d/256 used" %
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
    for i in range(NLIGHTS):
        for k in range(lit_h[i]):
            lit[(lit_row[i] + k) * 80 + 20 + lit_col[i]] = lit_on[i]
    for f in range(2):
        blk = flip_codes[f * 3 + 2]
        for br in range(FB_H):
            for bc in range(FB_W):
                r, c = FB_ROW + br, FB_COL[f] + bc
                codes80[r * 80 + 20 + c] = blk[br * FB_W + bc]
    preview_vdc(sys.argv[2] + "-table-lit.png", codes80, lit, b0, bank1.glyphs, yscale=2)
