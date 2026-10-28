#!/usr/bin/env python3
"""run_tour.py - drive Pac-Man through every corridor in VICE.

Boots build/test-tour.d64 (maze autopilot walking tools/mktour.py's route,
ghosts harmless) in warp mode through the VICE remote monitor and waits for
the route to finish. Passes if the whole route was walked, the board was
cleared (all dots eaten) and the tunnel was crossed both ways.
"""
import os
import re
import socket
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.environ.get("TOUR_BUILD", os.path.join(ROOT, "build"))
IMG = os.path.join(BUILD, "test-tour.d64")
LBL = os.path.join(BUILD, "babypac-tour.lbl")
labels = {}
for line in open(LBL):
    p = line.split()
    if len(p) == 3:
        labels[p[2].lstrip(".")] = int(p[1], 16)
env = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ["PATH"])
port = 6700 + (os.getpid() % 200)
shot = os.path.join(BUILD, "tour-end")
p = subprocess.Popen(["x128", "-default", "-ntsc", "-warp", "-minimized", "+sound",
                      "-sounddev", "dummy", "-drive9type", "1571", "-9", IMG,
                      "-keybuf", 'dload"bptour",u9\nrun\n',
                      "-remotemonitor", "-remotemonitoraddress", "ip4://127.0.0.1:%d" % port,
                      "-exitscreenshotvicii", shot + "-vic.png"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
sock = None
for _ in range(60):
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        break
    except OSError:
        time.sleep(0.5)
if sock is None:
    p.kill()
    sys.exit("could not reach the VICE monitor")


def peek(sym, n=1):
    a = labels[sym]
    sock.settimeout(0.01)
    try:
        while sock.recv(65536):
            pass
    except (socket.timeout, BlockingIOError):
        pass
    sock.sendall(("m %04x %04x\n" % (a, a + n - 1)).encode())
    d, t0 = b"", time.time()
    sock.settimeout(0.05)
    while time.time() - t0 < 2:
        try:
            d += sock.recv(65536)
        except socket.timeout:
            pass
        m = re.search(rb">C:%04x((?:\s+[0-9a-f]{2}){%d})" % (a, n), d, re.I)
        if m:
            break
    sock.sendall(b"x\n")
    if not m:
        return None
    return [int(x, 16) for x in m.group(1).split()]


result = {}
try:
    t0 = time.time()
    stalled = None
    last_tp, last_move = None, time.time()
    while time.time() - t0 < 300:
        time.sleep(0.5)
        b = peek("tour_boards")
        if b is None or b[0] == 0:
            continue                      # game not started yet
        d = (peek("tour_done") or [0])[0]
        if os.environ.get("TOUR_DEBUG"):
            dl = peek("mz_dotsleft", 2) or [0, 0]
            tpv = peek("tp", 2) or [0, 0]
            print("t=%3.0f boards %d done %d dots_left %d tp %04x cell %s lives %s" % (
                time.time() - t0, b[0], d, dl[0] | dl[1] << 8, tpv[0] | tpv[1] << 8,
                (peek("tour_r"), peek("tour_c")), peek("mz_lives")), flush=True)
        if d == 2:
            break
        tpv = peek("tp", 2)
        if tpv != last_tp:
            last_tp, last_move = tpv, time.time()
        elif time.time() - last_move > 20:      # the route stopped advancing
            break
        if d == 1 and b[0] == 1:          # route over but the board is not clear
            stalled = stalled or time.time()
            if time.time() - stalled > 10:
                break
    result = {k: (peek(k) or [None])[0] for k in ("tour_done", "tour_boards", "tour_wr")}
    left = peek("mz_dotsleft", 2)
    result["dots_left"] = left[0] | (left[1] << 8) if left else None
    sock.sendall(b"quit\n")
    p.wait(timeout=30)
finally:
    if p.poll() is None:
        p.kill()
print("tour result:", result, "in %.0fs" % (time.time() - t0))
ok = (result.get("tour_done") == 2 and (result.get("tour_boards") or 0) >= 2
      and (result.get("tour_wr") or 0) >= 2)
print("PASS: Pac-Man walked every corridor, ate every dot and crossed the tunnel both ways" if ok
      else "FAIL: the tour did not finish (a corridor blocks Pac-Man) or the board was not cleared")
sys.exit(0 if ok else 1)
