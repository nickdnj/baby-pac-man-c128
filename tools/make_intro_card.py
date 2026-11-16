#!/usr/bin/env python3
"""make_intro_card.py - the museum intro card for Baby Pac-Man, as a printable PDF.

One US Letter page (8.5 x 11 in, portrait, 0.4 in margins): what the game is,
how to start it on the Commodore 128, how it was built, the controls, and a QR
code to the GitHub project.

Needs reportlab, qrcode and pillow (pip install reportlab qrcode pillow).
Usage: make_intro_card.py OUT.pdf MAZE_SCREENSHOT.png PINBALL_SCREENSHOT.png
  MAZE_SCREENSHOT     a VIC (40-column) screenshot, for example from tests/energizers_start.py
  PINBALL_SCREENSHOT  a VDC (80-column) screenshot, already rescaled to 4:3
"""
import sys

import qrcode
from PIL import Image
from reportlab.lib.colors import Color, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

OUT, MAZE, PINBALL = sys.argv[1:4]
URL = "https://github.com/nickdnj/baby-pac-man-c128"
DRIVE = "U8"
COMMAND = 'DLOAD "BABY PAC-MAN",%s' % DRIVE

W, H = 612, 792
M = 29                          # 0.4 in
NAVY = Color(0.04, 0.04, 0.22)
SCREEN_BG = Color(0.17, 0.13, 0.55)      # C64-style blue
SCREEN_FG = Color(0.62, 0.62, 1.0)       # C64-style light blue
YELLOW = Color(1.0, 0.85, 0.0)
CYAN = Color(0.3, 0.9, 1.0)
GREY = Color(0.35, 0.35, 0.35)

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("Baby Pac-Man for the Commodore 128 - intro card")
c.setAuthor("Baby Pac-Man project")

# ---------------------------------------------------------------- header band
bh = 84
top = H - M
c.setFillColor(NAVY)
c.roundRect(M, top - bh, W - 2 * M, bh, 8, stroke=0, fill=1)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 46)
c.drawString(M + 16, top - 52, "BABY PAC-MAN")
c.setFillColor(CYAN)
c.setFont("Helvetica-Bold", 19)
c.drawString(M + 18, top - 75, "for the Commodore 128")
# Pac-Man chasing three dots
px, py, pr = W - M - 118, top - bh / 2, 24
c.setFillColor(YELLOW)
c.wedge(px - pr, py - pr, px + pr, py + pr, 215, 290, stroke=0, fill=1)
c.setFillColor(white)
for i in range(3):
    c.circle(px + 40 + i * 20, py, 4, stroke=0, fill=1)

# ---------------------------------------------------------------- how to start
y = top - bh - 10
ph = 152
c.setFillColor(SCREEN_BG)
c.roundRect(M, y - ph, W - 2 * M, ph, 8, stroke=0, fill=1)
c.setStrokeColor(SCREEN_FG)
c.setLineWidth(2)
c.roundRect(M + 4, y - ph + 4, W - 2 * M - 8, ph - 8, 6, stroke=1, fill=0)
c.setFillColor(YELLOW)
c.setFont("Helvetica-Bold", 17)
c.drawString(M + 18, y - 27, "HOW TO START IT ON THIS COMMODORE 128")
c.setFillColor(white)
c.setFont("Helvetica-Bold", 14)
c.drawString(M + 18, y - 50, "1.  Put the BABY PAC-MAN floppy disk in the disk drive.")
c.drawString(M + 18, y - 72, "2.  Type this exactly (U8 means disk drive 8), then press RETURN:")
c.setFillColor(black)
c.roundRect(M + 44, y - 116, W - 2 * M - 88, 36, 5, stroke=0, fill=1)
c.setFillColor(SCREEN_FG)
c.setFont("Courier-Bold", 26)
c.drawCentredString(W / 2, y - 106, COMMAND)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 14)
c.drawString(M + 18, y - 138, "3.  When it says READY, type RUN and press RETURN.  Then press FIRE!")
y -= ph + 12

# ---------------------------------------------------------------- the two screens
sh = 150
shots = [(MAZE, "THE MAZE", "plays on the 40-column screen"),
         (PINBALL, "THE PINBALL", "plays on the 80-column screen")]
imgs = [Image.open(p).convert("RGB") for p, _, _ in shots]
widths = [im.width * sh / im.height for im in imgs]
gap = (W - 2 * M - sum(widths)) / 3
x = M + gap
for (path, name, sub), im, w in zip(shots, imgs, widths):
    c.drawImage(ImageReader(im), x, y - sh, w, sh)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.5)
    c.rect(x, y - sh, w, sh, stroke=1, fill=0)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y - sh - 13, name)
    c.setFillColor(GREY)
    c.setFont("Helvetica", 9)
    c.drawString(x + c.stringWidth(name, "Helvetica-Bold", 10) + 6, y - sh - 13, sub)
    x += w + gap
y -= sh + 24

# ---------------------------------------------------------------- text columns
H1 = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=NAVY, spaceAfter=3)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9.6, leading=12.2, spaceAfter=4)
LI = ParagraphStyle("li", parent=B, leftIndent=11, bulletIndent=0, spaceAfter=2.5)
colw = (W - 2 * M - 22) / 2


def block(items, x0, y0, width):
    """draw paragraphs top-down from y0; returns the y below them"""
    for p in items:
        w, h = p.wrap(width, 1000)
        y0 -= h
        p.drawOn(c, x0, y0)
        y0 -= p.getSpaceAfter() if hasattr(p, "getSpaceAfter") else 0
    return y0


left = [
    Paragraph("WHAT IT IS", H1),
    Paragraph("In 1982 Bally Midway put a video maze on top of a little pinball table and called it "
              "<b>Baby Pac-Man</b>. This is a new, fan-made tribute that runs on the Commodore 128, "
              "which can drive <b>two screens at once</b>: the maze on the 40-column screen and the "
              "pinball table on the 80-column screen.", B),
    Paragraph("Steer Pac-Man round the maze and take a chute at the bottom: he becomes the pinball. "
              "Hit the targets to earn energizers, then drain the ball and carry them back into the maze.", B),
    Paragraph("&nbsp;", ParagraphStyle("sp", parent=B, fontSize=4, leading=4)),
    Paragraph("HOW IT WAS BUILT", H1),
    Paragraph("Written from scratch in <b>6502 assembly language</b> with the cc65 tools on a modern computer.", LI.clone("l1", bulletText="•")),
    Paragraph("All the pixel art, sound and table layout are our own. No arcade ROM data is used.", LI.clone("l2", bulletText="•")),
    Paragraph("Tested in the VICE emulator, then run on a real Commodore 128.", LI.clone("l3", bulletText="•")),
    Paragraph("Designed and coded with the help of an AI assistant (Claude, by Anthropic).", LI.clone("l4", bulletText="•")),
]
right = [
    Paragraph("CONTROLS", H1),
    Paragraph("<b>Maze:</b> joystick steers Pac-Man. FIRE starts a game.", LI.clone("c1", bulletText="•")),
    Paragraph("<b>Pinball flippers:</b> the <b>Commodore key</b> is the left flipper and "
              "<b>Right SHIFT</b> is the right flipper. Joystick left / right also work, and FIRE raises both.",
              LI.clone("c2", bulletText="•")),
    Paragraph("The plunger fires the ball by itself. There is nothing to pull.", LI.clone("c3", bulletText="•")),
    Paragraph("To stop, press RESET.", LI.clone("c4", bulletText="•")),
]
xl, xr = M + 4, M + 4 + colw + 22
y_left = block(left, xl, y, colw)
y_right = block(right, xr, y, colw)

# ---------------------------------------------------------------- QR code
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0, box_size=1)
qr.add_data(URL)
qr.make(fit=True)
mat = qr.get_matrix()
n = len(mat)
qsize = 104
cell = qsize / n
pad = 4 * cell                  # the QR quiet zone is 4 modules of plain white
qx = xr + pad
qy = y_right - 8 - pad - qsize
c.setFillColor(white)
c.rect(qx - pad, qy - pad, qsize + 2 * pad, qsize + 2 * pad, stroke=0, fill=1)
c.setFillColor(black)
for r, row in enumerate(mat):
    for k, on in enumerate(row):
        if on:
            c.rect(qx + k * cell, qy + qsize - (r + 1) * cell, cell + 0.2, cell + 0.2, stroke=0, fill=1)
c.setStrokeColor(NAVY)
c.setLineWidth(1.5)
c.rect(qx - pad - 1.5, qy - pad - 1.5, qsize + 2 * pad + 3, qsize + 2 * pad + 3, stroke=1, fill=0)
tx = qx + qsize + pad + 14
tw = xr + colw - tx
cap = [
    Paragraph("GET IT FREE", ParagraphStyle("g", fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=NAVY)),
    Paragraph("Scan with your phone to download the game, the disk image and all the source code.",
              ParagraphStyle("gc", parent=B, spaceBefore=3)),
    Paragraph("<font name='Courier-Bold' size='7.6'>github.com/<br/>nickdnj/baby-pac-man-c128</font>",
              ParagraphStyle("gu", parent=B, spaceBefore=4)),
]
block(cap, tx, qy + qsize + pad - 4, tw)

# ---------------------------------------------------------------- footer
c.setStrokeColor(GREY)
c.setLineWidth(0.6)
c.line(M, M + 30, W - M, M + 30)
foot = Paragraph(
    "An unofficial, non-commercial fan homage, made for the VCF museum community and not for sale. "
    "Baby Pac-Man and Pac-Man are trademarks of their respective owners; this project is not endorsed by or "
    "connected to them.",
    ParagraphStyle("f", fontName="Helvetica", fontSize=7.6, leading=9.4, textColor=GREY))
w, h = foot.wrap(W - 2 * M, 100)
foot.drawOn(c, M, M + 24 - h)

c.showPage()
c.save()
low = min(y_left, qy - pad)
print("wrote %s; text ends at y=%.0f, footer rule at y=%d (gap %.0f pt)" % (OUT, low, M + 30, low - (M + 30)))
