#!/usr/bin/env python3
"""vice_peek.py IMAGE NAME WAIT_S CMD... : run x128 (warp) with the remote
monitor, wait WAIT_S real seconds, send monitor commands, print replies."""
import socket, subprocess, sys, time, os
img, name, wait = sys.argv[1], sys.argv[2], float(sys.argv[3])
cmds = sys.argv[4:]
env = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ["PATH"])
p = subprocess.Popen(["x128", "-default", "-ntsc", "-warp", "-minimized", "+sound",
    "-sounddev", "dummy", "-drive9type", "1571", "-9", img,
    "-keybuf", 'dload"%s",u9\nrun\n' % name, "-remotemonitor",
    "-remotemonitoraddress", "ip4://127.0.0.1:6510"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
try:
    time.sleep(wait)
    s = socket.create_connection(("127.0.0.1", 6510), timeout=5)
    out = b""
    for c in cmds:
        s.sendall((c + "\n").encode())
        time.sleep(0.4)
        try:
            while True:
                d = s.recv(65536)
                if not d: break
                out += d
                if len(d) < 65536: break
        except socket.timeout:
            pass
    print(out.decode(errors="replace"))
    s.sendall(b"quit\n")
finally:
    time.sleep(0.5)
    p.kill()
