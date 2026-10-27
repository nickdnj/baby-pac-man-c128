BABY PAC-MAN FOR C128 - TIER 2: PINBALL ON THE 80-COLUMN SCREEN
================================================================

Disk images (same files on each):
  tier2-pinball.d64   (1541 format, readable by the 1571)
  tier2-pinball.d71   (1571 double-sided format)

Programs on the disk:   PINBALL   VDCTEST   DUALDEMO
(VDCTEST and DUALDEMO are the Tier 1 diagnostics, copied here so one disk
does everything. See README-TIER1.txt for them.)

LOADING (1571 = device 9), best from a fresh power-on:

  DLOAD "PINBALL",U9        <RETURN>
  RUN                       <RETURN>

Loading takes longer than the Tier 1 programs (43 blocks; load time on
the real 1571 not measured). Exit with the
RESET button (RUN/STOP+RESTORE does nothing in this program, on purpose).

CONTROLS
  Left flipper  = left paddle's fire button (port 1, "PADDLE-1" in DUALDEMO)
  Right flipper = right paddle's fire button (port 1, "PADDLE-2")
  Fallback: a joystick in port 2, pushed LEFT or RIGHT, works the flippers.
  A joystick in port 1 also works (left/right).
  Nothing else to press: each ball launches by itself.

WHAT YOU WILL SEE
80-column screen (RGBI monitor):
  - Centre: the pinball table, 40 columns wide, light-blue walls, "BABY
    PAC-MAN" on the top wall, two chute mouths (yellow V shapes) at the top,
    four green fruit-lane arrows, three purple pop bumpers, four cyan
    energizer targets on the side walls, a grey spinner, red slingshots,
    yellow flippers, and the drain ("OUT") in the middle at the bottom.
  - Left panel: PINBALL, THIS BALL EARNS (energizers, fruit level, bonus),
    GET READY / GO! for one second before each launch, and the controls hint.
  - Right panel: SCORE.
40-column screen: title, "THE PINBALL IS ON THE 80-COLUMN SCREEN", score,
  ball number, energizers lit, fruit lanes lit, live flipper-button lights
  ([LEFT] / [RIGHT] turn yellow while a button is held), a status line
  (GET READY / BALL IN PLAY / DRAINED! NEXT BALL), and a performance line:
  "PINBALL MAX nnnnn CYCLES/FRAME".

Play: after GET READY (1 s) the ball drops in from a top chute (left and
right alternate). Gravity pulls it down; it bounces off walls, bumpers (100
points, they kick), slingshots (10, they kick) and targets (500 the first
time; a lit target turns light cyan and counts an energizer; all four lit
re-arms them). Rolling over a fruit lane lights it (+fruit level, 200).
The spinner gives 50. Hold a flipper button to hold the flipper up; flick it
to hit the ball (the tip hits harder). The only way out is the centre drain:
"DRAINED! NEXT BALL..." then a new ball 2 s later. There is no game over in
this tier: it plays balls forever (the ball counter keeps going).

A ball that gets stuck (no scoring and no flipper hit for 10 s) is nudged; after
3 nudges it is drained automatically, so it can never hang on a trapped ball.

WHAT THE NUMBERS MEAN
  PINBALL MAX nnnnn CYCLES/FRAME: worst-case CPU time the pinball needed in
  the last ~1 s. An NTSC frame is about 17,000 cycles, of which roughly
  15,000-16,000 are usable. Below ~15,000 = full speed (60 updates/s).
  Above that = the game slows down a little during busy moments (it does not
  break). In VICE this shows about 7,000-12,500. THIS IS THE KEY NUMBER TO
  PHOTOGRAPH ON THE REAL MACHINE: real VDC timing is the biggest unknown.

IF IT FAILS - what to tell the maintainer
  * Red/black flashing border and "80-COL CHIP (VDC) IS NOT RESPONDING":
    the VDC did not answer. Run VDCTEST and photograph it.
  * 40-col screen shows the status and the score counts up but the 80-col
    screen is blank: monitor/cable/RGBI mode problem. The game is running.
  * Table looks scrambled or letters are wrong shapes on the 80-col screen:
    VDC charset/RAM problem. Photograph, then run VDCTEST.
  * Ball leaves trails, flickers badly, or the flippers do not appear to
    move when a button is held while [LEFT]/[RIGHT] light up on the
    40-col screen: photograph both screens and note the PINBALL MAX number.
  * [LEFT]/[RIGHT] never light up: the paddle buttons are not reaching the
    computer. Try a joystick in port 2 left/right. Run DUALDEMO to check.
  * Flippers are swapped: tell the maintainer (it is a one-line change).
  * Everything frozen (score, ball number and the 40-col status all stop):
    note what was on both screens. Press reset.

WHAT WAS TESTED (honest status)
Verified in VICE 3.10 x128 only (NTSC, 1571 as drive 9, VDC 16K and 64K):
  - loads with DLOAD "PINBALL",U9 + RUN from the .d64 (and the .d71 lists
    correctly); draws the table and panels; balls launch from alternating
    chutes, bounce, score, light targets, drain and relaunch (ball 10 after
    60 s with nobody playing)
  - a test-only build with an automatic flipper player (not on the disk)
    flipped the ball back up repeatedly, scored, lit energizer targets
    (score ~3,900 over 4 balls in 90 s); flipper poses render
  - pinball frame time 7,000-12,500 cycles in VICE
NOT verified: how the flippers FEEL to a human (nobody could hold a paddle
in the automated runs; the physics constants are first guesses), real
paddle buttons, anything on real hardware (VDC speed, look on the RGBI
monitor, ball roundness, overscan). Sound is minimal (short SID blips).
