#!/bin/bash
# tests/vice_run.sh IMAGE PRGNAME SECONDS OUTPREFIX [extra x128 args...]
# Loads PRGNAME from IMAGE on drive 9 (1571) with DLOAD"NAME",U9 + RUN,
# runs SECONDS of emulated time in warp, saves VDC + VIC screenshots.
export PATH=/opt/homebrew/bin:$PATH
IMG=$1; NAME=$2; SECS=$3; OUT=$4; shift 4
mkdir -p "$(dirname "$OUT")"
CYC=$(( SECS * 1022727 ))
rm -f "$OUT-vdc.png" "$OUT-vic.png"
x128 -default -ntsc -warp -minimized +sound -sounddev dummy \
  -drive9type 1571 -9 "$IMG" \
  -keybuf "dload\"$NAME\",u9\nrun\n" \
  -limitcycles $CYC \
  -exitscreenshot "$OUT-vdc.png" -exitscreenshotvicii "$OUT-vic.png" \
  "$@" >"$OUT.log" 2>&1
echo "exit $? ; shots:"; ls -la "$OUT"-*.png 2>/dev/null
