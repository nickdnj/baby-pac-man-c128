#!/usr/bin/env python3
"""vice_cycles.py IMAGE NAME LABELFILE SYMBOL[,SYM2,...] SAMPLES [x128 args...]

Runs x128 (warp, remote monitor) and samples a 16-bit little-endian value
(e.g. PINBOT's `wshow` = max pb_frame cycles over the last 64 frames)
SAMPLES times, about every 0.7 s of real time. Prints every sample and the
max / median, so builds can be compared on the same emulated workload.
Extra symbols (16-bit each) are read once, at the last sample (e.g. PINBOT's
wpeak = all-time peak, wslow = frames over one NTSC frame, frame = frames).
"""
import os
import re
import socket
import statistics
import subprocess
import sys
import time

img, name, lbl, sym, n = sys.argv[1:6]
extra = sys.argv[6:]
n = int(n)
syms = sym.split(",")
labels = {}
for line in open(lbl):
    parts = line.split()
    if len(parts) == 3:
        labels[parts[2].lstrip(".")] = int(parts[1], 16)
for sy in syms:
    if sy not in labels:
        sys.exit("symbol %s not in %s" % (sy, lbl))
addr = labels[syms[0]]
final = {}
env = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ["PATH"])
port = 6510 + (os.getpid() % 200)
p = subprocess.Popen(["x128", "-default", "-ntsc", "-warp", "-minimized", "+sound",
                      "-sounddev", "dummy", "-drive9type", "1571", "-9", img,
                      "-keybuf", 'dload"%s",u9\nrun\n' % name, "-remotemonitor",
                      "-remotemonitoraddress", "ip4://127.0.0.1:%d" % port] + extra,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
vals = []
try:
    time.sleep(4.0)
    for i in range(n):
        time.sleep(0.7)
        s = socket.create_connection(("127.0.0.1", port), timeout=5)
        s.sendall(("m %04x %04x\n" % (addr, addr + 1)).encode())
        time.sleep(0.25)
        d = s.recv(65536).decode(errors="replace")
        m = re.search(r">C:%04x\s+([0-9a-f]{2})\s+([0-9a-f]{2})" % addr, d, re.I)
        if m:
            v = int(m.group(1), 16) | (int(m.group(2), 16) << 8)
            vals.append(v)
        if i == n - 1:
            for sy in syms[1:]:
                a = labels[sy]
                s.sendall(("m %04x %04x\n" % (a, a + 1)).encode())
                time.sleep(0.25)
                d = s.recv(65536).decode(errors="replace")
                m = re.search(r">C:%04x\s+([0-9a-f]{2})\s+([0-9a-f]{2})" % a, d, re.I)
                if m:
                    final[sy] = int(m.group(1), 16) | (int(m.group(2), 16) << 8)
        s.sendall(b"x\n")
        s.close()
finally:
    p.kill()
vals_nz = [v for v in vals if v]
print("samples:", vals)
if final:
    print("final:", final)
if vals_nz:
    print("max %d  median %d  min %d  (n=%d nonzero)" % (
        max(vals_nz), statistics.median(vals_nz), min(vals_nz), len(vals_nz)))
