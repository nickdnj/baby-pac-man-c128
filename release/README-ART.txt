BABY PAC-MAN FOR C128 - ART PASS IMAGES (homage look)
=====================================================

A loving, non-commercial homage to Bally Midway's 1982 Baby Pac-Man. All the
pixel art is our own (drawn by our generator scripts); nothing is copied or
extracted from any arcade or pinball ROM.

These are NEW images. The known-good tier images (tier1/2/3) and
release/stable-baseline/ are unchanged: if an art image misbehaves, go back
to them.

IMAGES
  baby-pac-man.d64 / .d71  NEWEST, RECOMMENDED: art3-sound plus the maze fix (the
                           tunnel-row corridors were walled off; lines widened).
  art3-sound.d64 / .d71    (maze bug, do not use): table v2 + SID sound (maze siren,
                           chomp, flipper thwack, bumper pings, start fanfare).
                           BABY PAC-MAN and PINBALL (+ VDCTEST, DUALDEMO).
                             DLOAD "BABY PAC-MAN",U9   or   DLOAD "PINBALL",U9
  art2-pinball.d64 / .d71  Table v2, "faithful layout", no sound. BABY PAC-MAN and
                           PINBALL both on the new table (+ VDCTEST, DUALDEMO).
                             DLOAD "BABY PAC-MAN",U9   or   DLOAD "PINBALL",U9
  art-babypac.d64 / .d71   BABY PAC-MAN (art pass) + PINBALL + VDCTEST + DUALDEMO
                           Same controls as Tier 3:
                             DLOAD "BABY PAC-MAN",U9     RUN
                           113 blocks (Tier 3 was 70): give it longer to load.
  art-pinball.d64 / .d71   PINBALL (art pass) + VDCTEST + DUALDEMO
                           Same controls and load commands as Tier 2:
                             DLOAD "PINBALL",U9     RUN

STATUS
  art-pinball: the 80-column pinball table redrawn: rounded double-line walls,
  ringed pop bumpers in ghost colours, slingshots, tapered flippers, marquee
  "BABY PAC-MAN" panel with a ghost chase, score box, big Pac-Man and Blinky.
  Verified in VICE only (64K and 16K VDC). Function unchanged: flippers, targets,
  lanes, watchdog, PINBALL MAX / PEAK / SLOW FRAMES readout on the 40-col screen.

  art-babypac: the maze redrawn arcade style: rounded double-line blue walls,
  chomping Pac-Man facing his direction, red / pink / cyan / orange ghosts with
  moving feet and eyes that look where they go, blue frightened ghosts that
  flash white before they recover, eaten ghosts become eyes that run home,
  blinking energizers, fruit after 70 and 170 dots (better fruit when the
  pinball fruit lanes were lit), death animation, big GO! after a pinball
  visit, 1UP / HIGH SCORE HUD. Handoff, chutes, energizer awards, watchdogs and
  idle timeout unchanged. Verified in VICE only (64K and 16K VDC).

  art2-pinball (table v2): layout after the real Baby Pac-Man playfield, in
  our own pixel art: rounded top turning into FRUITS (left) and TUNNEL (right)
  side lanes with 500 / 1000 rollovers, the wooden tunnel arch at the top (the
  ball comes out of it), fruit clusters, two pop bumpers, and the central
  block of eight PAC / MAN targets in four numbered columns around an arrow
  lane with TIMER. SPELL PAC-MAN: completing a column (PAC + MAN of one
  number) or a word (all four PAC or all four MAN) earns an energizer for
  the maze; the FRUITS lane makes the maze fruit better. Pink ghost with a
  net, red ghost, and the stork with baby Pac-Man decorate the walls.
  It runs lighter than the first art table (VICE: peak 16,728, no slow frames).

WHAT TO tell the maintainer
  * Order to try at the museum: baby-pac-man (newest), then art3-sound (has the maze bug), then art2-pinball (same, no
    sound), then art-babypac / art-pinball (first art table), and the stable
    tier images if any of these misbehave.
  * BABY PAC-MAN on the art disks is 113 blocks (Tier 3 was 70): it takes a few
    seconds longer to load.
  * The sound has only been checked by recording and analysing VICE output; turn
    the monitor volume down first. It is our own fanfare, not the arcade tune.
  * Note the PINBALL MAX, PEAK and SLOW FRAMES numbers on the 40-col screen
    after a few minutes of play. In VICE: MAX about 11,000-14,000, PEAK about
    13,000 untouched (18,000 with constant flipping), SLOW FRAMES 0 to a
    handful. One NTSC frame is 17,045 cycles. If SLOW FRAMES climbs fast on the
    real machine, the stable tier 2 image is the fallback.
