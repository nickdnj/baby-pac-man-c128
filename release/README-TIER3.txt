BABY PAC-MAN FOR C128 - TIER 3: MAZE + PINBALL WITH HANDOFF (scope-cut)
=======================================================================

Disk images (same files on each):
  tier3-babypac.d64   (1541 format, readable by the 1571)
  tier3-babypac.d71   (1571 double-sided format)

Programs on the disk:   BABY PAC-MAN   PINBALL   VDCTEST   DUALDEMO
(PINBALL = Tier 2 on its own; VDCTEST/DUALDEMO = Tier 1 diagnostics.)

LOADING (1571 = device 9), best from a fresh power-on:

  DLOAD "BABY PAC-MAN",U9   <RETURN>
  RUN                       <RETURN>

70 blocks: the slowest of the programs to load (load time on the real
1571 not measured). Exit with the RESET button. RUN/STOP+RESTORE is ignored.

CONTROLS
  Joystick in PORT 2: steer Pac-Man; FIRE starts a game.
  Paddles in PORT 1: fire buttons = left / right flipper (either paddle
  button also starts a game). Fallback: joystick LEFT/RIGHT also flips.

WHAT YOU WILL SEE
Title: the maze on the 40-col screen with dots, ghosts in the house,
  Pac-Man in the middle, "BABY PAC-MAN - PRESS FIRE TO PLAY" on the bottom
  row. 80-col screen: the pinball table, dimmed, with "PRESS FIRE TO PLAY".
Game: "READY!" for 1.5 s, then play.
  - Eat dots (10). The two chutes are the gaps in the bottom wall with
    yellow arrows under them (columns 5 and 34). Steer down into one.
  - Entering a chute: Pac-Man disappears, the maze dims (blue walls, grey
    dots, grey border), the bottom row says "<< PINBALL IS ON THE LEFT
    SCREEN". The 80-col table brightens, GET READY / GO! shows, and after
    1 s the ball drops in from the chute mouth on the same side.
  - Pinball as in Tier 2. Lit cyan targets = energizers earned. The score
    is shared with the maze (SCORE on both screens).
  - Ball drains: the table dims ("MAZE ON CENTER SCREEN >>"), the maze
    brightens, "G O !" flashes, Pac-Man comes back just above the chute he
    took, facing up. Ghosts stay still for 1.5 s, flashing white. The
    chutes are now SHUT (red bars) until a board is cleared or a life is
    lost. Each energizer earned appears (cyan) in an empty maze corner
    (top-left, top-right, bottom-left, bottom-right; max 4, extras = 500
    points). Eating one turns the ghosts blue for 6 s; blue ghosts can be
    eaten (200/400/800/1600) and go back into the house.
  - Touching a normal ghost: Pac-Man blinks, a life is lost, chutes reopen,
    READY! again. 3 lives. GAME OVER after the last, then back to the title.
    High score is kept until power-off.
  - Eating every dot: the walls flash, a new board starts, chutes open.
  - Nobody touches the controls for 60 s (maze or pinball): GAME OVER and
    back to the title, so an abandoned game does not sit there forever.

WHAT WAS CUT (to get a working handoff for tomorrow)
  No attract/demo mode (the title just waits), no high-score initials, no
  docent key combination, no fruit (fruit lanes on the pinball only add
  points), simple ghost AI (target-tile chase/scatter, random when blue;
  eaten ghosts jump straight back into the house), small 8x8 sprites, no
  death animation beyond blinking, minimal sound, no "chutes shut" text.

IF IT FAILS - what to tell the maintainer
  * 40-col shows "80-COL CHIP (VDC) NOT RESPONDING. MAZE ONLY: CHUTES WILL
    STAY SHUT.": the maze still plays without pinball. Run VDCTEST.
  * Maze screen is garbage / wrong characters / no sprites: photograph it.
    (It uses VIC memory at $C000-$CFFF; a fault there is specific to this
    tier. Tier 1/2 use the normal 40-col screen.)
  * Entering a chute does nothing: check the chute has yellow arrows (open).
    After a pinball visit they are shut until a life is lost or the board
    is cleared. That is intended.
  * Handoff to pinball happens but the 80-col table stays dark: photograph
    both screens.
  * Freezes (nothing moves on either screen, no sound): note what was
    happening, photograph, reset.

WHAT WAS TESTED (honest status)
Verified in VICE 3.10 x128 only (NTSC, 1571 on drive 9, VDC 16K and 64K):
  - DLOAD "BABY PAC-MAN",U9 + RUN from the .d64 and the .d71: title screen
    appears on both screens and waits.
  - A test-only build (not on the disk) with an autopilot for Pac-Man and an
    automatic flipper player ran the full loop for minutes unattended:
    title -> game -> maze -> chute -> pinball -> drain -> maze resumes with
    chutes shut and awarded energizers placed in the corners (checked in
    memory: all 4 slots filled after a 4-energizer visit) -> deaths -> chutes
    reopen -> game over -> high score kept -> title -> next game.
NOT verified: a human playing it (joystick feel, Pac-Man turn timing,
whether the ghosts are fair), the paddle buttons, anything on real
hardware, idle timeout in a real session (logic only), board clear (the
autopilot never cleared a board), sound levels.
