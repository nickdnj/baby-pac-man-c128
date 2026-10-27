#!/usr/bin/env python3
"""tvscale.py IN.png OUT.png [xscale yscale]: nearest-neighbour rescale of a
VICE screenshot to roughly 4:3 monitor proportions (VDC shots are 856x240,
so the default stretches 1 x 2.67; for VIC shots use 2 2)."""
import sys
from PIL import Image
im = Image.open(sys.argv[1])
xs = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
ys = float(sys.argv[4]) if len(sys.argv) > 4 else im.width * 0.75 / im.height
im.resize((int(im.width * xs), int(im.height * ys)), Image.NEAREST).save(sys.argv[2])
