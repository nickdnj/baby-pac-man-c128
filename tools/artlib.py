#!/usr/bin/env python3
"""artlib.py - shared helpers for the art pass (pure Python, no ROM data).

  * FONT: our own bold 7x7 "arcade style" body font (drawn for this project).
  * Canvas: a pixel canvas in colour indices with per-cell colour resolution
    (one foreground colour per 8x8 cell, as both the VIC and the VDC require).
  * Bank: glyph allocator with de-duplication.
  * preview_*: PNG renderers (PIL, optional) for checking art without VICE.
"""
import math

RGBI = dict(black=0, dkgrey=1, dkblue=2, ltblue=3, dkgreen=4, ltgreen=5,
            dkcyan=6, ltcyan=7, dkred=8, ltred=9, dkpurp=10, ltpurp=11,
            dkyel=12, ltyel=13, ltgrey=14, white=15)
VIC = dict(black=0, white=1, red=2, cyan=3, purple=4, green=5, blue=6,
           yellow=7, orange=8, brown=9, ltred=10, dkgrey=11, grey=12,
           ltgreen=13, ltblue=14, ltgrey=15)
A_BLINK, A_UNDER, A_REV, A_ALT = 0x10, 0x20, 0x40, 0x80

RGBI_PAL = [(0, 0, 0), (85, 85, 85), (0, 0, 170), (85, 85, 255), (0, 170, 0),
            (85, 255, 85), (0, 170, 170), (85, 255, 255), (170, 0, 0),
            (255, 85, 85), (170, 0, 170), (255, 85, 255), (170, 85, 0),
            (255, 255, 85), (170, 170, 170), (255, 255, 255)]
VIC_PAL = [(0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189),
           (139, 63, 150), (85, 160, 73), (64, 49, 141), (191, 206, 114),
           (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
           (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159)]

# ------------------------------------------------------------------ font
# 7x7 bold glyphs (2-pixel strokes), row 7 and column 7 blank.
_F = {
    'A': ["..xxx..", ".xx.xx.", "xx...xx", "xx...xx", "xxxxxxx", "xx...xx", "xx...xx"],
    'B': ["xxxxxx.", "xx...xx", "xx...xx", "xxxxxx.", "xx...xx", "xx...xx", "xxxxxx."],
    'C': ["..xxxx.", ".xx..xx", "xx.....", "xx.....", "xx.....", ".xx..xx", "..xxxx."],
    'D': ["xxxxx..", "xx..xx.", "xx...xx", "xx...xx", "xx...xx", "xx..xx.", "xxxxx.."],
    'E': ["xxxxxxx", "xx.....", "xx.....", "xxxxxx.", "xx.....", "xx.....", "xxxxxxx"],
    'F': ["xxxxxxx", "xx.....", "xx.....", "xxxxxx.", "xx.....", "xx.....", "xx....."],
    'G': ["..xxxxx", ".xx....", "xx.....", "xx..xxx", "xx...xx", ".xx..xx", "..xxxxx"],
    'H': ["xx...xx", "xx...xx", "xx...xx", "xxxxxxx", "xx...xx", "xx...xx", "xx...xx"],
    'I': [".xxxxxx", "...xx..", "...xx..", "...xx..", "...xx..", "...xx..", ".xxxxxx"],
    'J': [".....xx", ".....xx", ".....xx", ".....xx", "xx...xx", "xx...xx", ".xxxxx."],
    'K': ["xx...xx", "xx..xx.", "xx.xx..", "xxxx...", "xxxxx..", "xx.xxx.", "xx..xxx"],
    'L': ["xx.....", "xx.....", "xx.....", "xx.....", "xx.....", "xx.....", "xxxxxxx"],
    'M': ["xx...xx", "xxx.xxx", "xxxxxxx", "xxxxxxx", "xx.x.xx", "xx...xx", "xx...xx"],
    'N': ["xx...xx", "xxx..xx", "xxxx.xx", "xxxxxxx", "xx.xxxx", "xx..xxx", "xx...xx"],
    'O': [".xxxxx.", "xx...xx", "xx...xx", "xx...xx", "xx...xx", "xx...xx", ".xxxxx."],
    'P': ["xxxxxx.", "xx...xx", "xx...xx", "xx...xx", "xxxxxx.", "xx.....", "xx....."],
    'Q': [".xxxxx.", "xx...xx", "xx...xx", "xx...xx", "xx.xxxx", "xx..xx.", ".xxxx.x"],
    'R': ["xxxxxx.", "xx...xx", "xx...xx", "xx..xxx", "xxxxx..", "xx.xxx.", "xx..xxx"],
    'S': [".xxxxx.", "xx...xx", "xx.....", ".xxxxx.", ".....xx", "xx...xx", ".xxxxx."],
    'T': ["xxxxxxx", "..xxx..", "..xxx..", "..xxx..", "..xxx..", "..xxx..", "..xxx.."],
    'U': ["xx...xx", "xx...xx", "xx...xx", "xx...xx", "xx...xx", "xx...xx", ".xxxxx."],
    'V': ["xx...xx", "xx...xx", "xx...xx", "xxx.xxx", ".xxxxx.", "..xxx..", "...x..."],
    'W': ["xx...xx", "xx...xx", "xx.x.xx", "xxxxxxx", "xxxxxxx", "xxx.xxx", "xx...xx"],
    'X': ["xx...xx", "xxx.xxx", ".xxxxx.", "..xxx..", ".xxxxx.", "xxx.xxx", "xx...xx"],
    'Y': ["xx...xx", "xx...xx", ".xx.xx.", "..xxx..", "..xxx..", "..xxx..", "..xxx.."],
    'Z': ["xxxxxxx", "....xxx", "...xxx.", "..xxx..", ".xxx...", "xxx....", "xxxxxxx"],
    '0': [".xxxxx.", "xx...xx", "xx..xxx", "xx.x.xx", "xxx..xx", "xx...xx", ".xxxxx."],
    '1': ["..xx...", ".xxx...", "..xx...", "..xx...", "..xx...", "..xx...", "xxxxxx."],
    '2': [".xxxxx.", "xx...xx", ".....xx", "..xxxx.", ".xxx...", "xx.....", "xxxxxxx"],
    '3': ["xxxxxxx", "....xx.", "...xx..", "..xxxx.", ".....xx", "xx...xx", ".xxxxx."],
    '4': ["...xxx.", "..xxxx.", ".xx.xx.", "xx..xx.", "xxxxxxx", "....xx.", "....xx."],
    '5': ["xxxxxx.", "xx.....", "xxxxxx.", ".....xx", ".....xx", "xx...xx", ".xxxxx."],
    '6': ["..xxxx.", ".xx....", "xx.....", "xxxxxx.", "xx...xx", "xx...xx", ".xxxxx."],
    '7': ["xxxxxxx", "xx...xx", "....xx.", "...xx..", "..xx...", "..xx...", "..xx..."],
    '8': [".xxxxx.", "xx...xx", "xx...xx", ".xxxxx.", "xx...xx", "xx...xx", ".xxxxx."],
    '9': [".xxxxx.", "xx...xx", "xx...xx", ".xxxxxx", ".....xx", "....xx.", ".xxxx.."],
    '!': ["..xx...", "..xx...", "..xx...", "..xx...", "..xx...", ".......", "..xx..."],
    '-': [".......", ".......", ".......", ".xxxxx.", ".......", ".......", "......."],
    '.': [".......", ".......", ".......", ".......", ".......", "..xx...", "..xx..."],
    ',': [".......", ".......", ".......", ".......", "..xx...", "..xx...", ".xx...."],
    ':': [".......", "..xx...", "..xx...", ".......", "..xx...", "..xx...", "......."],
    '(': ["...xx..", "..xx...", ".xx....", ".xx....", ".xx....", "..xx...", "...xx.."],
    ')': ["..xx...", "...xx..", "....xx.", "....xx.", "....xx.", "...xx..", "..xx..."],
    '/': [".....xx", "....xx.", "...xx..", "..xx...", ".xx....", "xx.....", "x......"],
    '<': ["....xx.", "...xx..", "..xx...", ".xx....", "..xx...", "...xx..", "....xx."],
    '>': [".xx....", "..xx...", "...xx..", "....xx.", "...xx..", "..xx...", ".xx...."],
    '=': [".......", "xxxxxxx", "xxxxxxx", ".......", "xxxxxxx", "xxxxxxx", "......."],
    '+': [".......", "..xx...", "..xx...", "xxxxxx.", "..xx...", "..xx...", "......."],
    '?': [".xxxxx.", "xx...xx", "....xx.", "...xx..", "...xx..", ".......", "...xx.."],
    "'": ["..xx...", "..xx...", ".xx....", ".......", ".......", ".......", "......."],
    '"': ["xx.xx..", "xx.xx..", "x..x...", ".......", ".......", ".......", "......."],
    '[': [".xxxx..", ".xx....", ".xx....", ".xx....", ".xx....", ".xx....", ".xxxx.."],
    ']': ["..xxxx.", "....xx.", "....xx.", "....xx.", "....xx.", "....xx.", "..xxxx."],
    '*': [".......", "xx...xx", ".xx.xx.", "..xxx..", ".xx.xx.", "xx...xx", "......."],
    '#': [".xx.xx.", "xxxxxxx", ".xx.xx.", ".xx.xx.", ".xx.xx.", "xxxxxxx", ".xx.xx."],
    ' ': ["......."] * 7,
}


def font_bits(ch):
    rows = _F.get(ch)
    if rows is None:
        return None
    out = []
    for r in rows:
        b = 0
        for i, c in enumerate(r):
            if c == 'x':
                b |= 0x80 >> i
        out.append(b)
    return out + [0]


def scr_code(ch):
    """C= screen code (upper case / graphics set) of a text character."""
    if ch == '@':
        return 0
    if 'A' <= ch <= 'Z':
        return ord(ch) - 64
    if ch == '[':
        return 27
    if ch == ']':
        return 29
    if ' ' <= ch <= '?':
        return ord(ch)
    raise ValueError(ch)


def font_charset_0_63():
    """64 glyphs (screen codes 0-63) of the bold font; undefined = blank."""
    out = []
    for code in range(64):
        ch = None
        for c in _F:
            if scr_code(c) == code:
                ch = c
        bits = font_bits(ch) if ch else [0] * 8
        out.append(bits)
    return out


def rows_to_bits(rows, on='x'):
    out = []
    for r in rows:
        b = 0
        for i, c in enumerate(r[:8]):
            if c in on:
                b |= 0x80 >> i
        out.append(b)
    return out


# ------------------------------------------------------------------ canvas
class Canvas:
    """Pixel canvas of cw x ch cells. pix[y][x] = colour index (0 = off)."""

    def __init__(self, cw, ch, aspect=2.0):
        self.cw, self.ch = cw, ch
        self.W, self.H = cw * 8, ch * 8
        self.aspect = aspect          # units per scanline for fill()
        self.pix = [[0] * self.W for _ in range(self.H)]
        self.cfg = {}                 # (r, c) -> forced fg colour
        self.flags = {}               # (r, c) -> attribute flag bits
        self.text_cells = {}          # (r, c) -> (code, colour)
        self.blank_col = {}           # (r, c) -> attr colour of a blank cell

    def px(self, x, y, c):
        if 0 <= x < self.W and 0 <= y < self.H:
            self.pix[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.W and 0 <= y < self.H:
            return self.pix[y][x]
        return 0

    def fill(self, fn, x0=0, y0=0, x1=None, y1=None):
        """fn(ux, uy) -> colour (or 0/None to leave the pixel), unit space."""
        x1 = self.W if x1 is None else x1
        y1 = self.H if y1 is None else y1
        for y in range(max(0, y0), min(self.H, y1)):
            uy = (y + 0.5) * self.aspect
            row = self.pix[y]
            for x in range(max(0, x0), min(self.W, x1)):
                v = fn(x + 0.5, uy)
                if v is not None and v is not False:
                    row[x] = v

    def blit(self, rows, x, y, cmap):
        for dy, r in enumerate(rows):
            for dx, ch in enumerate(r):
                if ch in cmap:
                    self.px(x + dx, y + dy, cmap[ch])

    def text(self, row, col, s, colour, flags=0):
        for i, ch in enumerate(s):
            self.text_cells[(row, col + i)] = (scr_code(ch), colour)
            if flags:
                self.flags[(row, col + i)] = flags

    def cell_pixels(self, r, c):
        return [self.pix[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)]


class Bank:
    """Glyph allocator: free codes in order, de-duplicated."""

    def __init__(self, name, free_codes, glyphs=None):
        self.name = name
        self.free = list(free_codes)
        self.glyphs = dict(glyphs or {})     # code -> 8 bytes
        self.index = {}
        for code, g in self.glyphs.items():
            self.index.setdefault(tuple(g), code)

    def alloc(self, bits):
        key = tuple(bits)
        if key in self.index:
            return self.index[key]
        if not self.free:
            raise RuntimeError("glyph bank %s is full" % self.name)
        code = self.free.pop(0)
        self.glyphs[code] = list(bits)
        self.index[key] = code
        return code

    def used(self):
        return len(self.glyphs)


def resolve_cell(canvas, r, c, priority=None):
    """-> (fg colour, bits[8], dropped pixel count)."""
    cells = canvas.cell_pixels(r, c)
    counts = {}
    for row in cells:
        for v in row:
            if v:
                counts[v] = counts.get(v, 0) + 1
    if not counts:
        return None, [0] * 8, 0
    fg = canvas.cfg.get((r, c))
    if fg is None:
        if priority:
            # the last colour of `priority` that is present wins
            pri = [k for k in priority if k in counts]
            fg = pri[-1] if pri else max(counts, key=counts.get)
        else:
            fg = max(counts, key=counts.get)
    bits = []
    for row in cells:
        b = 0
        for i, v in enumerate(row):
            if v == fg:
                b |= 0x80 >> i
        bits.append(b)
    dropped = sum(n for k, n in counts.items() if k != fg)
    return fg, bits, dropped


# ------------------------------------------------------------------ previews
def _img():
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


def preview_vdc(path, codes, attrs, bank0, bank1, cols=80, rows=25, yscale=2):
    """codes/attrs: flat lists (rows x cols). bank0/bank1: code -> 8 bytes."""
    Image = _img()
    if not Image:
        return False
    im = Image.new("RGB", (cols * 8, rows * 8 * yscale))
    p = im.load()
    for r in range(rows):
        for c in range(cols):
            code = codes[r * cols + c]
            a = attrs[r * cols + c]
            g = (bank1 if a & A_ALT else bank0).get(code, [0] * 8)
            col = RGBI_PAL[a & 15]
            for y in range(8):
                b = g[y]
                if a & A_REV:
                    b ^= 0xFF
                for x in range(8):
                    if b & (0x80 >> x):
                        for k in range(yscale):
                            p[c * 8 + x, (r * 8 + y) * yscale + k] = col
    im.save(path)
    return True


def preview_vic(path, codes, colours, charset, sprites=(), bg=0, scale=2):
    """codes/colours flat 40x25; charset: code -> 8 bytes;
    sprites: list of (x, y, rows[21] of 24-bit ints, colour, mc, mc0, mc1)
    with x, y in screen pixels (0,0 = top-left of the text area)."""
    Image = _img()
    if not Image:
        return False
    im = Image.new("RGB", (320 * scale, 200 * scale), VIC_PAL[bg])
    p = im.load()

    def put(x, y, col):
        if 0 <= x < 320 and 0 <= y < 200:
            for i in range(scale):
                for j in range(scale):
                    p[x * scale + i, y * scale + j] = col
    for r in range(25):
        for c in range(40):
            g = charset.get(codes[r * 40 + c], [0] * 8)
            col = VIC_PAL[colours[r * 40 + c] & 15]
            for y in range(8):
                for x in range(8):
                    if g[y] & (0x80 >> x):
                        put(c * 8 + x, r * 8 + y, col)
    for (sx, sy, rows, col, mc, mc0, mc1) in sprites:
        for y, v in enumerate(rows):
            if mc:
                for x in range(12):
                    pair = (v >> (22 - 2 * x)) & 3
                    if pair:
                        cc = {1: mc0, 2: col, 3: mc1}[pair]
                        put(sx + 2 * x, sy + y, VIC_PAL[cc])
                        put(sx + 2 * x + 1, sy + y, VIC_PAL[cc])
            else:
                for x in range(24):
                    if v & (1 << (23 - x)):
                        put(sx + x, sy + y, VIC_PAL[col])
    im.save(path)
    return True
