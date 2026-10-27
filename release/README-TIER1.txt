BABY PAC-MAN FOR C128 - TIER 1: HARDWARE DIAGNOSTICS
=====================================================

Disk images (same two programs on each; use whichever you can write):
  tier1-diag.d64   (1541 format, readable by the 1571)
  tier1-diag.d71   (1571 double-sided format)

Programs on the disk:   VDCTEST   DUALDEMO

LOADING (1571 = device 9)
-------------------------
Best from a fresh power-on (power off, wait 5 s, power on).
Either screen mode is fine (40/80 key up or down).

  DLOAD "VDCTEST",U9        <RETURN>
  RUN                       <RETURN>

  DLOAD "DUALDEMO",U9       <RETURN>
  RUN                       <RETURN>

To check the disk first:   DIRECTORY U9   (should list "VDCTEST" and "DUALDEMO")

To get out of either program: hold RUN/STOP and tap RESTORE, or press the
reset button. Then DLOAD the next program. Neither program writes to disk.

Neither program needs an 80-column monitor. Every result is also on the
40-column screen. If only one monitor is connected, use the 40-column one.

----------------------------------------------------------------------
VDCTEST - what you will see
----------------------------------------------------------------------
40-col screen (and the left half of the 80-col screen, same text):

  Row "VIDEO: NTSC  VDC STATUS $82 VER 2"
      NTSC or PAL = the machine's video standard (we expect NTSC).
      VER n = VDC chip version (status bits 0-2). Rough guide, from
      memory, not verified: 0 = early 8563 (flat C128),
      1 = later 8563, 2 = 8568 (C128DCR) or late 8563. Write it down.
  Row "VDC R25 $47  R28 $2F (AT START)"  - register values the KERNAL
      left. Just write them down.
  Row "VDC RAM: 16K / 64K / UNCLEAR  PROBE aa bb cc dd"
      64K = the 64K VDC RAM upgrade (or a C128DCR). Probe reads 11 22 33 44.
      16K = the original 16K VDC RAM. Probe repeats values (e.g. 33 44 33 44).
      UNCLEAR = neither pattern: photograph it. The game only uses 16K,
      so the game works either way.
      "NO REPLY" = the VDC chip did not respond at all (see below).
  "VDC SPEED" block: CPU cycles for 1024 writes (two ways), 1024 reads and
      256 random single pokes. "/EA" = cycles per byte. In VICE we see
      roughly 35/EA inline, 72/EA polled, 250/EA per random poke (reads
      vary a lot in VICE, 27 to 310/EA).
      Real-machine numbers are the main thing we want: photograph them.
      BUSY WAITS = how often the VDC said "not ready". TIMEOUTS should be 0.
  "VIC:" colour bars: 16 coloured blocks with labels 0-F and two-letter
      names (BK WH RD CY PU GN BL YE OR BR LR G1 G2 LG LB G3). Block 0 is
      black, so it looks empty. That is correct.
  "VDC RAM TEST" block: loops forever.
      ROUND n      = test rounds started. One round takes about 15 s.
      PASS / FAIL  = rounds with no errors / rounds with at least one error.
      BYTES CHECKED, ERR = running totals.
      LAST ERROR AT $aaaa WROTE $ww READ $rr = the most recent bad byte.
      Phase A writes patterns into VDC RAM $1000-$1FFF (not displayed)
      and reads them back. Phase B checks the rest of the 16K (screen,
      colours, font) by inverting each byte, reading it back, and
      restoring it. Only plain CPU writes are used, never the VDC
      block copy/fill (the thing suspected of corrupting on real units).
      The two hex digits + spinner at the end of the PHASE line move
      while it works. If they stop moving for more than 10 s, it is hung.
  Bottom: green "ALL VDC CHECKS OK SO FAR" or red "VDC RAM ERRORS SEEN".
      The border also turns red at the first error (it is green while
      the RAM test runs with no errors).

80-col screen: the same results on the left, a header on the right, and at
the bottom 16 colour bars numbered 0-15 with names. The expected order is:
  0 black, 1 dark grey, 2 dark blue, 3 light blue, 4 dark green,
  5 light green, 6 dark cyan, 7 light cyan, 8 dark red, 9 light red,
  10 dark purple, 11 light purple, 12 dark yellow (often brown),
  13 light yellow, 14 light grey, 15 white.
  Bar 0 is black (looks empty). If the colours do not match the names,
  photograph them: the game's palette assumes this order.

Suggested: let VDCTEST run for at least 10 minutes (longer is better),
then photograph both screens.

----------------------------------------------------------------------
DUALDEMO - what you will see
----------------------------------------------------------------------
Both screens in colour at the same time:
  40-col: title, frame counter, colour bars, a ball (hardware sprite) that
          bounces around the whole screen and changes colour at each
          bounce. Bottom line: "80-COL SCREEN SHOULD SHOW A 2ND BALL".
  80-col: title, frame counter, colour bars, a ball character bouncing in
          the lower part of the screen, changing colour at each bounce.
The FRAME counter on both screens must keep counting (60 per second NTSC).

Live inputs (on both screens; a word turns WHITE while active, grey otherwise):
  JOYSTICK PORT 2: UP DOWN LEFT RIGHT FIRE  - plug the joystick in port 2.
  PORT 1 (PADDLE FIRE BUTTONS): PADDLE-1 FIRE  PADDLE-2 FIRE
          - plug the paddle pair in port 1, press each button in turn.
          Write down which physical paddle lights PADDLE-1 (that one will
          be the LEFT flipper).
  PORT 1 AS JOYSTICK: the same port 1 lines as joystick directions (a
          joystick in port 1 lights these; paddle buttons light LEFT/RIGHT).
  PADDLE KNOBS (PORT 1): X nnn Y nnn - turning the paddle knobs should
          change these numbers (0-255). 255 with nothing plugged in is normal.
          The game does not use the knobs; this is only a health check.

----------------------------------------------------------------------
IF IT FAILS - what to tell the maintainer
----------------------------------------------------------------------
* "?FILE NOT FOUND": check DIRECTORY U9; check the drive is device 9
  (try U8 if the drive is set to 8: DLOAD "VDCTEST",U8).
* Screen stays at "STARTING..." with a blue or cyan border: the VDC did
  not answer. tell the maintainer the border colour. (Blue = stuck in the first VDC
  checks; cyan = stuck setting up the 80-col screen; purple = stuck in
  the speed test; green = RAM test running normally.)
* "VDC NOT RESPONDING" / "NO REPLY": the 80-col chip is not answering.
  The 40-col results are still valid. Photograph.
* Red border / FAIL count above 0: photograph both screens, including the
  LAST ERROR line. Note how long it ran.
* 80-col screen blank or rolling but 40-col fine: the 80-col monitor or
  cable (or the monitor is not in RGBI mode). Photograph the 40-col.
* Colours on the 80-col bars in a different order: photograph them.
* Machine freezes with no counters moving: note which program, what was
  on screen and the border colour.

----------------------------------------------------------------------
WHAT WAS TESTED (honest status)
----------------------------------------------------------------------
Verified in VICE 3.10 x128 only (NTSC C128, 1571 as drive 9, DLOAD ...,U9
then RUN typed via the keyboard buffer), with VDC 16K and VDC 64K:
  - both programs load and run from the .d64 and the .d71
  - VDCTEST reports 64K / 16K correctly for each VICE setting, runs the RAM
    test loop with 0 errors, shows both colour tests
  - DUALDEMO animates both screens and counts frames
NOT verified anywhere: the joystick / paddle readouts with real presses
  (VICE runs were unattended; the idle state shows correctly), paddle knob
  values, and everything on real hardware: real VDC timing, real VDC RAM
  behaviour, the RGBI colour order on the museum monitor, which version
  number the museum's VDC reports. VICE's VDC timing is not authoritative.
