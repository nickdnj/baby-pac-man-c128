#!/usr/bin/env python3
"""mkmaze.py - generate the VIC maze data (ca65 source) from the UX 4.4 maze.
Art pass version: our own pixel art, nothing taken from any ROM.

Outputs:
  mz_type   40x25 cell types: 0 open, 1 wall, 2 door, 3 chute, 4 tunnel wrap
  mz_dots   40x25 initial dots: 0 none, 1 dot
  mz_codes  40x25 VIC screen codes of the static maze (walls, door, arrows)
  vcharset  full 256-glyph VIC charset: 0-63 our bold font, 64.. maze art
  vclass    colour class per screen code (256): 0 wall 1 dot 2 energizer
            3 door 4 gate 5 arrow 6 life 7 text/other 8 fruit icons
  spr_data  sprite shapes (64 bytes each), see the SP_* constants
  constants: NDOTS, glyph codes, slot cells, sprite indices

Walls: rounded "double line" art computed from a pixel distance field. The
inner line sits 4 px inside every wall face, so a 13-14 px actor centred on
a 1-cell corridor never touches it; the outer border gets a second line on
its outside edge, the ghost house a second line on its inside edge.
Usage: mkmaze.py OUT.s [PREVIEW_PREFIX]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import font_charset_0_63, rows_to_bits, preview_vic, VIC

MAZE = [
    "  ######################################",  # row 2  (columns 0..39)
    "  # ................##................ #",
    "  #.#####.#####.###.##.###.#####.#####.#",
    "  #.#####.#####.###.##.###.#####.#####.#",
    "  #....##....##.....##.....##....##....#",
    "  #.##.##.##.######.##.######.##.##.##.#",
    "  #.##.##.##.######.##.######.##.##.##.#",
    "  #.##..............................##.#",
    "  #.##.#####.##.####--####.##.#####.##.#",
    "  #.##.#####.##.#   BP   #.##.#####.##.#",
    "  =.......##....#   IC   #....##.......=",
    "  #.#####.##.##.#        #.##.##.#####.#",
    "  #.#####.##.##.##########.##.##.#####.#",
    "  #.......##........@.........##.......#",
    "  #.#####.##.##.###.##.###.##.##.#####.#",
    "  #.#####.##.##.###.##.###.##.##.#####.#",
    "  #....##....##.....##.....##....##....#",
    "  #.##.##.#####.###.##.###.#####.##.##.#",
    "  #.##.##.#####.###.##.###.#####.##.##.#",
    "  # .................................. #",
    "  ####v############################v####",
]
MAZE = [r[1:] for r in MAZE]
MAZE = [(r + " " * 40)[:40] for r in MAZE]
TOP = 2

W, H = 40, 25
typ = [[0] * W for _ in range(H)]
dots = [[0] * W for _ in range(H)]
for r in range(H):
    for c in range(W):
        typ[r][c] = 1 if r < TOP or r > TOP + len(MAZE) - 1 else 0
for i, row in enumerate(MAZE):
    r = TOP + i
    for c, ch in enumerate(row):
        if ch == '#':
            typ[r][c] = 1
        elif ch == '-':
            typ[r][c] = 2
        elif ch == 'v':
            typ[r][c] = 3
        elif ch == '=':
            typ[r][c] = 4
        elif ch == '.':
            dots[r][c] = 1
        elif ch == ' ' and (c == 0 or c == 39):
            typ[r][c] = 1
for r in range(TOP, TOP + len(MAZE)):
    for c in range(W):
        row = MAZE[r - TOP]
        first = row.index('#') if '#' in row else 0
        last = row.rindex('#')
        if c < first and row[c] != '=':
            typ[r][c] = 1
        if c > last and row[c] != '=':
            typ[r][c] = 1
for r in range(11, 14):
    for c in range(16, 24):
        if typ[r][c] == 0:
            typ[r][c] = 1

ndots = sum(map(sum, dots))
pac = None
for i, row in enumerate(MAZE):
    if '@' in row:
        pac = (TOP + i, row.index('@'))
chutes = [c for c, ch in enumerate(MAZE[-1]) if ch == 'v']
tunnel_row = [TOP + i for i, row in enumerate(MAZE) if '=' in row][0]
tunnel_cols = [c for c, ch in enumerate(MAZE[tunnel_row - TOP]) if ch == '=']
CHUTE_ROW = TOP + len(MAZE) - 1

# ---------------------------------------------------------------- wall art
# cell kinds for the art: 'W' wall, 'C' corridor (incl. tunnel, chute,
# chute arrow cell below), 'H' ghost-house interior, 'O' outside
kind = [['O'] * W for _ in range(H)]
for i, row in enumerate(MAZE):
    r = TOP + i
    for c, ch in enumerate(row):
        if ch in '#-':
            kind[r][c] = 'W'
        elif ch in '.@ =v':
            kind[r][c] = 'C'
# house interior and the blank cells outside the border
for r in range(11, 14):
    for c in range(16, 24):
        kind[r][c] = 'H'
for i, row in enumerate(MAZE):
    r = TOP + i
    first, last = row.index('#') if '#' in row else 1, row.rindex('#')
    for c in range(W):
        if (c < first or c > last) and row[c] != '=':
            kind[r][c] = 'O'
# tunnel channel runs to the screen edge; chutes run down through row 23
kind[tunnel_row][0] = kind[tunnel_row][39] = 'C'
for c in chutes:
    kind[CHUTE_ROW + 1][c] = 'C'

PX_W, PX_H = 320, 200


def pk(x, y):
    if 0 <= x < PX_W and 0 <= y < PX_H:
        return kind[y >> 3][x >> 3]
    return 'O'


OFFS = sorted(((math.hypot(dx, dy), dx, dy) for dx in range(-9, 10) for dy in range(-9, 10)
               if math.hypot(dx, dy) <= 9.0))


def near_dist(x, y, target):
    for d, dx, dy in OFFS:
        if pk(x + dx, y + dy) in target:
            return d
    return 99.0


# dc = distance of each wall pixel to the nearest corridor pixel; the
# "core" is everything at least 7 px deep. The line is the set of pixels
# 3 px outside the core (and at least 3.5 px from a corridor): 4 px inside
# a straight face, with rounded convex and concave corners.
dc = {}
for r in range(TOP, TOP + len(MAZE)):
    for c in range(W):
        if kind[r][c] != 'W':
            continue
        for y in range(r * 8, r * 8 + 8):
            for x in range(c * 8, c * 8 + 8):
                dc[(x, y)] = near_dist(x, y, 'C')


def is_core(x, y):
    k = pk(x, y)
    if k in 'OH':
        return True
    if k != 'W':
        return False
    return dc.get((x, y), 99.0) >= 7.0


def core_dist(x, y):
    for d, dx, dy in OFFS:
        if d > 4.0:
            break
        if is_core(x + dx, y + dy):
            return d
    return 99.0


wallpx = [[0] * PX_W for _ in range(PX_H)]
for r in range(TOP, TOP + len(MAZE)):
    for c in range(W):
        if kind[r][c] != 'W':
            continue
        is_door = MAZE[r - TOP][c] == '-'
        for y in range(r * 8, r * 8 + 8):
            for x in range(c * 8, c * 8 + 8):
                d = dc[(x, y)]
                dk = core_dist(x, y)
                on = 2.5 <= dk < 3.5 and d >= 3.5
                # second line: wall pixels touching the outside or the house
                if near_dist(x, y, 'OH') <= 1.0 and d > 4.5:
                    on = True
                if is_door:
                    on = False
                if on:
                    wallpx[y][x] = 1

# ---------------------------------------------------------------- glyphs
glyphs = {}
for i, g in enumerate(font_charset_0_63()):
    glyphs[i] = g
gclass = [7] * 256
next_code = [64]
index = {}


def alloc(bits, cls):
    key = (tuple(bits), cls)
    if key in index:
        return index[key]
    code = next_code[0]
    next_code[0] += 1
    glyphs[code] = list(bits)
    gclass[code] = cls
    index[key] = code
    return code


G_DOT = alloc([0, 0, 0, 0x18, 0x18, 0, 0, 0], 1)
G_ENER = alloc(rows_to_bits(["..xxxx..", ".xxxxxx.", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx",
                             "xxxxxxxx", ".xxxxxx.", "..xxxx.."]), 2)
G_DOOR = alloc([0, 0, 0, 0, 0, 0xFF, 0xFF, 0], 3)
G_GATE = alloc([0, 0xFF, 0x81, 0xFF, 0x81, 0xFF, 0, 0], 4)
G_ARROW = alloc(rows_to_bits(["...xx...", "...xx...", "...xx...", "xxxxxxxx", ".xxxxxx.",
                              "..xxxx..", "...xx...", "........"]), 5)
G_LIFE = alloc(rows_to_bits(["..xxxx..", ".xxxxxx.", "...xxxxx", ".....xxx", "...xxxxx",
                             ".xxxxxx.", "..xxxx..", "........"]), 6)
# fruit icons for the HUD (single colour each)
FRUIT_ICONS = [
    ["....x...", "...x.x..", "..x...x.", ".xx..xx.", "xxxx.xxx", "xxxx.xxx", ".xx...x.", "........"],  # cherry
    [".x.x.x..", "..xxx...", ".xxxxx..", "xx.x.xx.", "xxxxxxx.", ".x.x.x..", "..xxx...", "...x...."],  # strawberry
    ["....x...", "...xx...", ".xxxxx..", "xxxxxxx.", "xxxxxxx.", "xxxxxxx.", ".xxxxx..", "........"],  # orange
    ["....x...", "...x....", ".xx.xx..", "xxxxxxx.", "xxxxxxx.", "xxxxxxx.", ".xx.xx..", "........"],  # apple
]
G_FRUIT0 = None
for i, f in enumerate(FRUIT_ICONS):
    code = alloc(rows_to_bits(f), 8)
    if i == 0:
        G_FRUIT0 = code
    assert code == G_FRUIT0 + i
G_BLANK_WALL = 32

codes = [[32] * W for _ in range(H)]
for r in range(TOP, TOP + len(MAZE)):
    for c in range(W):
        ch = MAZE[r - TOP][c]
        if ch == '-':
            codes[r][c] = G_DOOR
        elif ch == '.':
            codes[r][c] = G_DOT
        elif kind[r][c] in 'WO':
            bits = []
            for y in range(8):
                b = 0
                for x in range(8):
                    if wallpx[r * 8 + y][c * 8 + x]:
                        b |= 0x80 >> x
                bits.append(b)
            codes[r][c] = alloc(bits, 0) if any(bits) else 32
for c in chutes:
    codes[CHUTE_ROW + 1][c] = G_ARROW

# ---------------------------------------------------------------- title logo
# "BABY" / "PAC-MAN" in our 11x7 logo letters (same design as the VDC
# marquee) at 3x3 pixel blocks: 33 x 21 px per letter, one letter per
# 5-cell slot, 3 cell rows tall. Pac-Man stands in for the C.
LOGO = {
    'B': ["#########..", "###....###.", "###....###.", "#########..", "###....###.", "###....###.", "#########.."],
    'A': ["..#######..", ".###...###.", "###.....###", "###########", "###.....###", "###.....###", "###.....###"],
    'Y': ["###.....###", "###.....###", ".###...###.", "..#######..", "....###....", "....###....", "....###...."],
    'P': ["#########..", "###....###.", "###....###.", "#########..", "###........", "###........", "###........"],
    'M': ["###.....###", "####...####", "#####.#####", "###.###.###", "###..#..###", "###.....###", "###.....###"],
    'N': ["###.....###", "####....###", "#####...###", "###.###.###", "###...#####", "###....####", "###.....###"],
    '-': ["....", "....", "....", "####", "....", "....", "...."],
}


def logo_rows(word_slots):
    """word_slots: [(letter, cell column)] -> 3 rows x 40 glyph codes"""
    px = [[0] * 320 for _ in range(24)]
    for ch, c0 in word_slots:
        x0, y0 = c0 * 8 + 3, 2
        if ch == 'C':
            cx, cy, rad = x0 + 15.5, y0 + 10.5, 10.6
            for y in range(24):
                for x in range(c0 * 8, c0 * 8 + 40):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    if math.hypot(dx, dy) <= rad and abs(math.atan2(dy, dx)) > math.radians(34):
                        px[y][x] = 1
            continue
        g = LOGO[ch]
        if ch == '-':
            x0 = c0 * 8 + 2
        for gy, row in enumerate(g):
            for gx, cc in enumerate(row):
                if cc == '#':
                    for k in range(3):
                        for j in range(3):
                            px[y0 + gy * 3 + k][x0 + gx * 3 + j] = 1
    out = []
    for r in range(3):
        row = []
        for c in range(40):
            bits = []
            for y in range(8):
                b = 0
                for x in range(8):
                    if px[r * 8 + y][c * 8 + x]:
                        b |= 0x80 >> x
                bits.append(b)
            row.append(alloc(bits, 7) if any(bits) else 32)
        out.append(row)
    return out


TITLE_BABY = logo_rows([('B', 10), ('A', 15), ('B', 20), ('Y', 25)])
TITLE_PAC = logo_rows([('P', 4), ('A', 9), ('C', 14), ('-', 19), ('M', 21), ('A', 26), ('N', 31)])

if next_code[0] > 256:
    sys.exit("mkmaze: VIC glyph budget exceeded")

# ---------------------------------------------------------------- sprites
# Every shape is drawn on a 16x16 grid at the top-left of the 24x21
# sprite. Actor centre = grid (7, 7) for hi-res shapes; multicolour
# shapes are 8 MC pixels wide with the actor centre between MC columns 3/4.
def spr_hires(fn):
    """fn(x, y) -> bool on a 24x21 grid"""
    data = [0] * 64
    for y in range(21):
        v = 0
        for x in range(24):
            if fn(x, y):
                v |= 1 << (23 - x)
        data[y * 3:y * 3 + 3] = [(v >> 16) & 255, (v >> 8) & 255, v & 255]
    return data


def spr_mc(rows, x0=0, y0=0):
    """rows of MC pixels: '.' 00, 'W' 01 (MC0), 'B' 10 (sprite colour),
    'P' 11 (MC1); placed at MC column x0, line y0."""
    data = [0] * 64
    code = {'.': 0, 'W': 1, 'B': 2, 'P': 3}
    for y, row in enumerate(rows):
        v = 0
        for x, ch in enumerate(row):
            v |= code[ch] << (22 - 2 * (x + x0))
        yy = y + y0
        data[yy * 3:yy * 3 + 3] = [(v >> 16) & 255, (v >> 8) & 255, v & 255]
    return data


PAC_R = 6.6


def pac_shape(direction, half_angle):
    ang = {'R': 0.0, 'L': math.pi, 'U': -math.pi / 2, 'D': math.pi / 2}[direction]

    def f(x, y):
        dx, dy = x + 0.5 - 7.0, y + 0.5 - 7.0
        if dx * dx + dy * dy > PAC_R * PAC_R:
            return False
        if half_angle <= 0:
            return True
        a = math.atan2(dy, dx) - ang
        a = (a + math.pi) % (2 * math.pi) - math.pi
        return abs(a) > half_angle
    return spr_hires(f)


sprites = []
SP = {}


def add(name, data):
    SP[name] = len(sprites)
    sprites.append(data)


# Pac-Man: 0 closed; 1-4 R L U D half open; 5-8 R L U D wide open
add('PAC', pac_shape('R', 0))
for d in 'RLUD':
    add('PAC_H' + d, pac_shape(d, math.radians(28)))
for d in 'RLUD':
    add('PAC_W' + d, pac_shape(d, math.radians(52)))
# death: facing up, the mouth opens until he folds away, then a burst
for i, deg in enumerate((70, 95, 120, 140, 158, 172, 179)):
    add('DIE%d' % i, pac_shape('U', math.radians(deg)))


def burst(rad):
    def f(x, y):
        dx, dy = x + 0.5 - 7.0, y + 0.5 - 7.0
        r = math.hypot(dx, dy)
        if r < rad - 1.6 or r > rad + 0.4:
            return False
        a = math.degrees(math.atan2(dy, dx)) % 45
        return a < 9 or a > 36
    return spr_hires(f)


add('DIE7', burst(3.5))
add('DIE8', burst(5.5))
add('DIE9', spr_hires(lambda x, y: False))
NDIE = 10

# Ghosts (multicolour): body 'B' = sprite colour, eye whites 'W' = MC0
# (white), pupils 'P' = MC1 (blue). 7 MC px wide x 14 lines, placed at MC
# column 1 so the 14-px body spans grid x 2..15 (sprite is shifted -1 px).
DOME = ["..BBB..", ".BBBBB.", "BBBBBBB"]
FEET = [["BBBBBBB", "B.B.B.B"], ["BBBBBBB", ".B.B.B."]]
EYES = {
    'R': ["BBWWBWW", "BBWWBWW", "BBWPBWP", "BBWPBWP", "BBWWBWW"],
    'L': ["WWBWWBB", "WWBWWBB", "PWBPWBB", "PWBPWBB", "WWBWWBB"],
    'U': ["BWPBWPB", "BWPBWPB", "BWWBWWB", "BWWBWWB", "BWWBWWB"],
    'D': ["BWWBWWB", "BWWBWWB", "BWWBWWB", "BWPBWPB", "BWPBWPB"],
}


def ghost_rows(d, feet):
    top = ["..BBB..", ".BBBBB."]
    up = d == 'U'
    rows = top + ["BBBBBBB"]
    if up:
        rows = top + EYES[d] + ["BBBBBBB"]
    else:
        rows = top + ["BBBBBBB"] + EYES[d]
    rows = rows + ["BBBBBBB"] * (12 - len(rows)) + FEET[feet]
    return rows


for d in 'RLUD':
    for ft in range(2):
        add('GH_%s%d' % (d, ft), spr_mc(ghost_rows(d, ft), x0=1))
FRIGHT = ["..BBB..", ".BBBBB.", "BBBBBBB", "BBBBBBB", "BBWBWBB", "BBWBWBB", "BBBBBBB",
          "BBBBBBB", "BWBWBWB", "WBWBWBW", "BBBBBBB", "BBBBBBB"]
for ft in range(2):
    add('FR%d' % ft, spr_mc(FRIGHT + FEET[ft], x0=1))
for ft in range(2):
    flash = [r.replace('W', 'P') for r in FRIGHT]
    add('FL%d' % ft, spr_mc(flash + FEET[ft], x0=1))
for d in 'RLUD':
    rows = [r.replace('B', '.') for r in ghost_rows(d, 0)]
    add('EY_' + d, spr_mc(rows, x0=1))


# Fruit (hi-res, two layers: body colour + detail colour)
def from_rows(rows, x0=1, y0=1):
    def f(x, y):
        yy, xx = y - y0, x - x0
        return 0 <= yy < len(rows) and 0 <= xx < len(rows[yy]) and rows[yy][xx] == 'x'
    return spr_hires(f)


FRUIT_SPR = [
    # cherry: red body, brown stems
    (["............", "............", "............", "............", "............",
      "..xx.....xx.", ".xxxx...xxxx", "xxxxx..xxxxx", "x.xxx..x.xxx", "xxxxx..xxxxx", ".xxx....xxx."],
     ["........xx..", "......xx.x..", "....xx...x..", "...x.....x..", "..x......x..",
      "............", "............", "............", "............", "............", "............"]),
    # strawberry: red body with seed holes, green leaves
    (["............", "............", "...xxxxxx...", "..xxxxxxxx..", ".xx.xxxx.xx.", ".xxxxx.xxxx.",
      ".xx.xxxxx.x.", "..xxxx.xxx..", "...xxxxxx...", "....xxxx....", ".....xx....."],
     ["....x..x....", "...xxxxxx...", "............", "............", "............",
      "............", "............", "............", "............", "............", "............"]),
    # orange: orange body, green leaf
    (["............", "............", "...xxxxxx...", "..xxxxxxxx..", ".xxxxxxxxxx.", ".xxxxxxxxxx.",
      ".xxxxxxxxxx.", ".xxxxxxxxxx.", "..xxxxxxxx..", "...xxxxxx...", "............"],
     [".....x.xx...", ".....xxx....", "............", "............", "............",
      "............", "............", "............", "............", "............", "............"]),
    # apple: red body, green stem and leaf
    (["............", "............", "..xxx..xxx..", ".xxxxxxxxxx.", ".xxxxxxxxxx.", ".xxxxxxxxxx.",
      ".xxxxxxxxxx.", ".xxxxxxxxxx.", "..xxxxxxxx..", "...xx..xx...", "............"],
     [".....x.xx...", ".....xxx....", "............", "............", "............",
      "............", "............", "............", "............", "............", "............"]),
]
for i, (body, detail) in enumerate(FRUIT_SPR):
    add('FRUIT%d' % i, from_rows(body, 1, 1))
    add('FRUITD%d' % i, from_rows(detail, 1, 1))

# GO! banner: our logo letters (11x7 grid, 2 lines per grid row), shown
# x/y expanded on the maze centre. Two sprites: "GO" and "!".
LOGO_G = ["..########.", ".###.......", "###........", "###...#####", "###.....###", ".###....###", "..#######.."]
LOGO_O = ["..#######..", ".###...###.", "###.....###", "###.....###", "###.....###", ".###...###.", "..#######.."]
LOGO_X = ["###", "###", "###", "###", "###", "...", "###"]


def word_sprite(letters):
    def f(x, y):
        gy = y // 2
        if gy >= 7:
            return False
        xx = x
        for L in letters:
            w = len(L[0])
            if xx < w:
                return L[gy][xx] == '#'
            xx -= w + 1
        return False
    return spr_hires(f)


add('GO', word_sprite([LOGO_G, LOGO_O]))
add('GOX', word_sprite([LOGO_X]))

# ---------------------------------------------------------------- output
out = []
o = out.append
o("; generated by tools/mkmaze.py - do not edit")
o("NDOTS = %d" % ndots)
o("PAC_ROW = %d" % pac[0])
o("PAC_COL = %d" % pac[1])
o("CHUTE_L = %d" % chutes[0])
o("CHUTE_R = %d" % chutes[1])
o("CHUTE_ROW = %d" % CHUTE_ROW)
o("TUN_ROW = %d" % tunnel_row)
o("TUN_L = %d" % tunnel_cols[0])
o("TUN_R = %d" % tunnel_cols[1])
for k, v in dict(G_DOT=G_DOT, G_ENER=G_ENER, G_DOOR=G_DOOR, G_GATE=G_GATE,
                 G_ARROW=G_ARROW, G_LIFE=G_LIFE, G_FRUIT0=G_FRUIT0).items():
    o("%s = %d" % (k, v))
o("NSPRITES = %d" % len(sprites))
for k, v in SP.items():
    o("SP_%s = %d" % (k, v))
o("NDIE = %d" % NDIE)
o('.segment "RODATA"')


def emit(name, data, per=20):
    o(name + ":")
    for i in range(0, len(data), per):
        o("  .byte " + ",".join("$%02X" % (x & 255) for x in data[i:i + per]))


emit("mz_type", [typ[r][c] for r in range(H) for c in range(W)])
emit("mz_dots", [dots[r][c] for r in range(H) for c in range(W)])
emit("mz_codes", [codes[r][c] for r in range(H) for c in range(W)])
vg = []
for code in range(256):
    vg += glyphs.get(code, [0] * 8)
emit("vcharset", vg, 16)
emit("vclass", gclass)
emit("title_baby", [c for row in TITLE_BABY for c in row])
emit("title_pac", [c for row in TITLE_PAC for c in row])
sd = []
for s in sprites:
    sd += s
emit("spr_data", sd, 16)
open(sys.argv[1], "w").write("\n".join(out) + "\n")
print("mkmaze: %d dots, pac at %s, chutes %s, tunnel row %d cols %s; glyphs 64..%d; %d sprites" %
      (ndots, pac, chutes, tunnel_row, tunnel_cols, next_code[0] - 1, len(sprites)))
for r in range(H):
    print("".join({0: '.', 1: '#', 2: '-', 3: 'v', 4: '='}[typ[r][c]] if not dots[r][c] else 'o' for c in range(W)))

# ---------------------------------------------------------------- preview
if len(sys.argv) > 2:
    CLS_COL = {0: VIC['ltblue'], 1: VIC['ltred'], 2: VIC['cyan'], 3: VIC['ltred'], 4: VIC['red'],
               5: VIC['yellow'], 6: VIC['yellow'], 7: VIC['white'], 8: VIC['red']}
    pc = []
    pcol = []
    for r in range(H):
        for c in range(W):
            code = codes[r][c]
            pc.append(code)
            pcol.append(CLS_COL[gclass[code]])
    # HUD sample text
    def txt(r, c, s, col):
        for i, ch in enumerate(s):
            from artlib import scr_code
            pc[r * 40 + c + i] = scr_code(ch)
            pcol[r * 40 + c + i] = col
    txt(0, 3, "1UP", VIC['white']); txt(0, 14, "HIGH SCORE", VIC['white'])
    txt(1, 2, "  12340", VIC['ltgrey']); txt(1, 15, "  50000", VIC['ltgrey'])
    for i in range(3):
        pc[40 + 31 + i] = G_LIFE; pcol[40 + 31 + i] = VIC['yellow']
    pc[40 + 37] = G_FRUIT0; pcol[40 + 37] = VIC['red']
    txt(24, 16, "READY!", VIC['yellow'])
    for (r, c) in ((3, 2), (3, 37), (21, 2), (21, 37)):
        pc[r * 40 + c] = G_ENER; pcol[r * 40 + c] = VIC['cyan']

    def rows21(data):
        return [(data[y * 3] << 16) | (data[y * 3 + 1] << 8) | data[y * 3 + 2] for y in range(21)]
    sp = []
    sp.append((19 * 8 - 4, 15 * 8 - 4, rows21(sprites[SP['PAC_WL']]), VIC['yellow'], False, 1, 6))
    for i, (gc, cr, nm) in enumerate(((VIC['red'], (9, 19), 'GH_L0'), (VIC['ltred'], (11, 19), 'GH_U1'),
                                      (VIC['cyan'], (12, 20), 'GH_D0'), (VIC['orange'], (9, 25), 'GH_R1'))):
        sp.append((cr[1] * 8 - 5, cr[0] * 8 - 4, rows21(sprites[SP[nm]]), gc, True, 1, 6))
    sp.append((6 * 8 - 5, 9 * 8 - 4, rows21(sprites[SP['FR0']]), VIC['blue'], True, 1, 6))
    sp.append((9 * 8 - 5, 9 * 8 - 4, rows21(sprites[SP['FL1']]), VIC['white'], True, 1, 6))
    sp.append((31 * 8 - 5, 15 * 8 - 4, rows21(sprites[SP['EY_L']]), VIC['white'], True, 1, 6))
    sp.append((12 * 8 - 4, 15 * 8 - 4, rows21(sprites[SP['FRUIT0']]), VIC['red'], False, 1, 6))
    sp.append((12 * 8 - 4, 15 * 8 - 4, rows21(sprites[SP['FRUITD0']]), VIC['brown'], False, 1, 6))
    preview_vic(sys.argv[2] + "-maze.png", pc, pcol, glyphs, sp, scale=3)
    # sprite sheet
    sheet = []
    for i, s in enumerate(sprites):
        mc = 'GH_' in [k for k, v in SP.items() if v == i][0][:3] or [k for k, v in SP.items() if v == i][0][:2] in ('FR', 'FL', 'EY')
        if [k for k, v in SP.items() if v == i][0].startswith('FRUIT'):
            mc = False
        sheet.append(((i % 12) * 26, (i // 12) * 24, rows21(s), VIC['yellow'] if not mc else VIC['red'], mc, 1, 6))
    preview_vic(sys.argv[2] + "-sprites.png", [32] * 1000, [0] * 1000, glyphs, sheet, scale=3)
