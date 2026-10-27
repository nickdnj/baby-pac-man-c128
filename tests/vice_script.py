#!/usr/bin/env python3
"""vice_script.py IMAGE NAME LABELFILE OUTPREFIX STEP [STEP ...]

Scripted x128 run (warp, remote monitor) for checking game states that are
hard to reach by waiting. Steps (run in order):
  f=N            wait until the 16-bit `frame` counter is in N..N+899
                 (warp is switched off 150 frames before N, so pokes land
                 within a frame or two; the rest of the run is real time)
  t=S            wait S real seconds
  warp=on|off    the run starts with warp OFF (real time, exact timing);
                 use warp=on before a long wait (then f= turns it off again)
  w=SYM:V        wait until the byte at SYM equals V
  SYM=V[,V..]    poke bytes (hex or decimal) at a label (or $hex address)
  SYM+K=V[,V..]  ... at label + K
  peek=SYM:N     print N bytes at SYM
  vdc=PATH       monitor screenshot (the VDC window) to PATH
  mon=TEXT       raw monitor command(s), ';'-separated, all in one stop,
                 e.g. "mon=t 0008 0008 0009;t 0012 0012 0013" (copies)
At the end x128 quits, writing OUTPREFIX-vdc.png / OUTPREFIX-vic.png
(exit screenshots of both windows). Example:
  vice_script.py build/test-auto.d64 bpauto build/babypac-auto.lbl out/blue \
      f=1500 fright=$68,1 gblue+1=1,1,1,1 f=1530
"""
import os
import re
import socket
import subprocess
import sys
import time

img, name, lbl, out = sys.argv[1:5]
steps = sys.argv[5:]
labels = {}
for line in open(lbl):
    p = line.split()
    if len(p) == 3:
        labels[p[2].lstrip(".")] = int(p[1], 16)


def addr_of(sym):
    m = re.match(r"([$\w]+)(?:\+(\d+))?$", sym)
    base, off = m.group(1), int(m.group(2) or 0)
    if base.startswith("$"):
        return int(base[1:], 16) + off
    return labels[base] + off


def val(v):
    return int(v[1:], 16) if v.startswith("$") else int(v)


env = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ["PATH"])
port = 6600 + (os.getpid() % 300)
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
for suf in ("-vdc.png", "-vic.png"):
    if os.path.exists(out + suf):
        os.remove(out + suf)
p = subprocess.Popen(["x128", "-default", "-ntsc", "-warp", "-minimized", "+sound",
                      "-sounddev", "dummy", "-drive9type", "1571", "-9", img,
                      "-keybuf", 'dload"%s",u9\nrun\n' % name,
                      "-remotemonitor", "-remotemonitoraddress", "ip4://127.0.0.1:%d" % port,
                      "-exitscreenshot", out + "-vdc.png",
                      "-exitscreenshotvicii", out + "-vic.png"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


_sock = [None]


def _conn():
    if _sock[0] is None:
        for _ in range(60):
            try:
                _sock[0] = socket.create_connection(("127.0.0.1", port), timeout=10)
                break
            except OSError:
                time.sleep(0.5)
    return _sock[0]


def mon(cmd, wait=0.25, until=None):
    """Send monitor command(s) in one stop; return the reply text. With
    `until` (regex) return as soon as it shows up (fast polling). One
    persistent connection; 'x' resumes the machine after each call."""
    s = _conn()
    s.settimeout(0.01)                 # drop stale output of earlier calls
    try:
        while s.recv(65536):
            pass
    except (socket.timeout, BlockingIOError):
        pass
    for c in cmd.split(";"):           # one session: the machine stays stopped
        s.sendall((c.strip() + "\n").encode())
        if not until:
            time.sleep(0.05)
    d = b""
    if until:
        s.settimeout(0.05)
        t0 = time.time()
        while time.time() - t0 < 2.0 and not re.search(until, d.decode(errors="replace"), re.I):
            try:
                c = s.recv(65536)
                if not c:
                    break
                d += c
            except socket.timeout:
                pass
    else:
        time.sleep(wait)
        s.settimeout(0.5)
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except socket.timeout:
            pass
    s.sendall(b"x\n")
    s.settimeout(0.02)
    try:                               # drain the echo of 'x'
        s.recv(65536)
    except socket.timeout:
        pass
    return d.decode(errors="replace")


def read16(a):
    d = mon("m %04x %04x" % (a, a + 1), until=r">C:%04x\s+\w\w\s+\w\w[^\n]*\n" % a)
    if os.environ.get("VS_DEBUG"):
        print("read", round(time.time(), 2), d.strip()[-70:])
    m = re.search(r">C:%04x\s+([0-9a-f]{2})\s+([0-9a-f]{2})" % a, d, re.I)
    return int(m.group(1), 16) | (int(m.group(2), 16) << 8) if m else None


try:
    time.sleep(0.5)
    mon("warp off")                    # real time: polls/pokes land exactly
    for st in steps:
        k, v = st.split("=", 1)
        if k == "f":
            target = val(v)
            fa = labels["frame"]
            t0 = time.time()
            slow = False
            prev = None
            while time.time() - t0 < 240:
                f = read16(fa)
                # before the program runs `frame` is garbage: only trust a
                # counter that is moving forward at a plausible rate
                live = f is not None and prev is not None and 0 < (f - prev) % 65536 < 600
                prev = f
                if live and not slow and target - 150 <= f < target + 900:
                    mon("warp off")        # real time from here: exact pokes
                    slow = True
                if live and target <= f < target + 900:
                    break
                time.sleep(0.02)
            print("frame", f)
        elif k == "warp":
            mon("warp " + v)
        elif k == "t":
            time.sleep(float(v))
        elif k == "w":
            sym, want = v.split(":")
            a = addr_of(sym)
            t0 = time.time()
            got = None
            while time.time() - t0 < 240:
                d = mon("m %04x %04x" % (a, a))
                m = re.search(r">C:%04x\s+([0-9a-f]{2})" % a, d, re.I)
                got = int(m.group(1), 16) if m else None
                if got == val(want):
                    break
                time.sleep(0.1)
            print("waited", sym, "=", got)
        elif k == "mon":
            print("mon", v); print(mon(v).strip())
        elif k == "vdc":
            mon('screenshot "%s" 2' % v, 1.0)
        elif k == "peek":
            sym, n = v.split(":")
            a = addr_of(sym)
            print(sym, mon("m %04x %04x" % (a, a + int(n) - 1)).strip().splitlines()[0])
        else:
            a = addr_of(k)
            bs = " ".join("%02x" % val(x) for x in v.split(","))
            mon("> %04x %s" % (a, bs))
            print("poked", k, bs)
    s = _conn()
    s.sendall(b"quit\n")
    p.wait(timeout=30)
    s.close()
finally:
    if p.poll() is None:
        p.kill()
print("shots:", [f for f in (out + "-vdc.png", out + "-vic.png") if os.path.exists(f)])
