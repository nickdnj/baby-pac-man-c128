# Developer Notes: Baby Pac-Man for C128 (museum-visit sprint)

Running log of decisions, deviations from `docs/architecture.md`, and known issues.
Context: 2026-10-27, building tiered disk images for a real-hardware session at the
museum the next morning. Speed over completeness; everything below is VICE-verified
only unless it says otherwise.

## Build
- `make` (or `make tier1`, `make tier2`, `make tier3`), `make release` copies images to `release/`.
- Tools: ca65/ld65 (cc65 2.19), c1541 and x128 (VICE 3.10), Homebrew `/opt/homebrew/bin`.
- `tests/vice_run.sh IMAGE NAME SECONDS OUTPREFIX [x128 args]` loads with
  `DLOAD"NAME",U9` + `RUN` via `-keybuf` on a 1571 as drive 9, runs in warp for
  SECONDS of emulated time, and writes `OUTPREFIX-vdc.png` / `-vic.png` screenshots
  (`-exitscreenshot` = VDC window, `-exitscreenshotvicii` = VIC window).
- VICE flags confirmed: `-drive9type 1571`, `-9`, `-keybuf`, `-limitcycles`, `-warp`,
  `-exitscreenshot`, `-exitscreenshotvicii`, `-VDC16KB` / `-VDC64KB` (there is no
  `+VDC64KB`), `-VDCRevision`, `-minimized`, `-controlport1device 2` (paddles).

## Shared code layout (deviation: simpler than architecture 3.3)
- `src/hw/c128.inc` equates, `src/hw/scr.inc` charmap (A-Z -> screen codes 1-26).
- `src/lib/stub.s` PRG load address + BASIC stub `10 SYS 7184`; code at `$1C10`.
- `src/lib/vdc.s` VDC layer: poll-every-access with bounded timeout; after 4
  timeouts `vdc_dead` is set and all VDC calls return immediately (never hangs).
- `src/lib/screen.s` dual-screen text printer (VIC and/or VDC by `pr_mask`), number
  formatting. `src/lib/sys.s` setup, raster frame wait, input, CIA cycle timer.
- `src/linker/c128.cfg` one config; `MAINTOP` caps the image (default `$4000` for
  programs that keep the ROMs in).
- Gotcha: `@` maps to screen code 0, which is the string terminator. Never put `@`
  in text. Macros must not define labels (they would end ca65 cheap-local `@label`
  scopes), so strings are inlined after `jsr printi`.

## Decisions and deviations
- **No interrupts at all (deviation from 5.2).** Every program runs `SEI` from start
  and syncs by polling the VIC raster (line 251). Simpler, deterministic, nothing to
  go wrong with vectors. Sound, if any, is ticked from the main loop.
- **Tier 1 diagnostics keep the ROMs in** (`$FF00=$00`) and stay below `$4000`; the
  VIC uses the default bank 0 screen at `$0400` with the ROM font. RUN/STOP+RESTORE
  goes to the KERNAL NMI, which warm-starts BASIC: a usable exit.
- VDC font: the diagnostics copy the 512 character-ROM glyphs (MMU config `$01`,
  char ROM at `$D000`) to VDC `$2000-$3FFF` themselves, rather than trusting what the
  KERNAL left, and set R28 charset bits to `$2000` (RAM-type bit 4 left as found).
- VDC RAM probe: R28 bit 4 set temporarily, bytes 11/22/33/44 written to
  `$1F80/$5F80/$9F80/$DF80`, read back, R28 restored. Done before the screen is set
  up so stray writes on a 16K part cannot damage the font. Any cross-read = 16K.
  VICE results: 64K -> `11 22 33 44`; 16K -> `33 44 33 44` (aliases on A15, not A14).
- RAM corruption test: phase A = 5 patterns (55, AA, 00, FF, address) written as
  sequential runs to `$1000-$1FFF` and read back; phase B = per-byte
  read / write complement / read back / restore over `$0000-$0FFF` and
  `$2000-$3FFF` (live screen, attributes, font) so the display is undisturbed.
  Only the 16K the game uses is tested (64K region not tested).
- Cycle timing uses CIA1 timer A cascaded into timer B (32-bit), interrupts off.

## Measurements (VICE 3.10 only, NTSC, not authoritative)
| Test | VICE result |
|---|---|
| 1024 sequential writes, inline poll (`bit $D600/bpl/sta`) | ~34-37 cycles/byte |
| 1024 sequential writes via `jsr vdc_put` (timeout-capable) | ~71-74 cycles/byte |
| 1024 sequential reads via `jsr vdc_get` | ~27-42 cycles/byte (varies) |
| 256 random single pokes (set R18/R19 + write) | ~245-250 cycles each |
| KERNAL-left registers | R25 `$47`, R28 `$2F` (RAM-type bit 4 = 0 even with 64K) |
| Status / version | `$82`, version 2 (VICE default revision) |

Implication for the pinball (R2/V1): set-address is expensive (~250 cycles), so the
renderer must minimise address changes and favour short sequential runs with the
inline poll. Budget ~14,500 cycles/frame -> roughly 50 random pokes or ~350 run bytes.
VICE appears to model the VDC accepting a byte only every ~34 cycles; real hardware
may be faster or slower. VDCTEST on the real machine settles it.

## Tier 2: pinball (src/pinball/)
- `tools/mktable.py` generates `build/table_data.s`: table map (40x25 codes and
  attributes), glyphs 64-131 (68 used of 176 available), collision class and normal
  per glyph, 3 flipper poses per flipper as 8x5-cell code blocks (flipper pixels
  OR'd over the static art, deduplicated), flipper direction/normal tables, and the
  pre-shifted 6x4 ball bitmap. The ASCII table map is printed to `build/table_map.txt`.
- Table layout follows UX 7.2 in spirit, adjusted: funnel walls are one cell per
  row (rows 10-20), flipper pivots at table columns 12/27 on row 20, flippers 46 px,
  drain gap between the tips (table columns ~18-21), targets at rows 6/8 on the side
  walls, bumpers 4x2 at (4,10), (4,26), (7,18), lanes on row 3, spinner on row 11.
- **One charset, not two** (deviation from 8.5): codes 0-63 = ROM font (copied from
  the character ROM at start), 64-131 table/flipper art, `$F0-$F7` ball slots (two
  sets of four, alternating each frame). Attribute bit 7 is never used.
- Ball = software glyph sprite exactly as architecture 8.5 (compose into a slot from
  the `disp` shadow, rewrite the union of old/new cells). Collision uses the static
  `tbl_codes` map plus the glyph bitmap in RAM for shaped cells, normals from the
  per-glyph table; probe-direction normals for full blocks. Response
  `v -= (1+e)(v.n)n` with signed 8x8 shift-add multiplies (not quarter-square).
- Physics: x subunit 1/32 px, y subunit 1/64 scanline (ASPECT_Y = 2), velocities
  signed bytes capped at 88 (2.75 px per substep), 2 substeps per frame, gravity 1.
- Flippers: 3 poses (rest 25 deg down, 2 deg, 25 deg up); press = +1 pose per
  frame, release = -1 pose per 2 frames. Analytic line-segment collision per pose,
  contact band widened to -24 when the flipper moved up this frame (swept check).
  Kick = 34 + t along the normal (tip harder).
- Watchdog per FR-3.7 (600 frames, 3 nudges, then forced drain). A ball resting
  on a held flipper does NOT reset the watchdog (only a moving-flipper hit does).
- Panel text is redrawn one field per frame when dirty (VDC prints are expensive).
- ROMs are banked out (`$FF00=$3E`) right after the ROM font is copied; NMI/IRQ
  vectors in RAM point at an `RTI`, so RESTORE is ignored. Exit = reset button.
- `make tier2` also builds `build/test-bot.d64` (`PINBOT`, `-D BOT=1`): an automatic
  flipper player for unattended VICE testing. Not shipped.
- Measured in VICE: `pb_frame` worst case ~12,200 cycles with the bot flipping,
  ~7,800 with no input -> 60 Hz in VICE.

## Tier 3: maze + handoff (src/maze/)
- `tools/mkmaze.py` takes the UX 4.4 maze verbatim (rows 2-22, columns 1-38) and
  generates the cell-type map, the dot map (311 dots; UX text says 312), autotiled
  thin-line wall glyphs (16 neighbour masks), dot/energizer/door/gate/arrow/life
  glyphs, and 12 sprite shapes. Map printout in `build/maze_map.txt`.
- **VIC bank 3, not bank 1 (deviation from 4.4).** The program image runs from
  `$1C10` to about `$70B0`, which overlaps bank 1. VIC memory is `$C000` screen,
  `$C400` sprites (pointers 16+), `$C800` charset (ROM font 0-63 copied at start,
  custom 64-127). `$DD00` bits 0-1 = `%00`, `$D018 = $02`. Image limit `$C000`.
- **8x8 sprites on the cell grid** instead of 12-13 px shapes, so nothing overlaps
  the 1-cell corridors. Pac-Man 1 px/frame, ghosts 7/8, blue ghosts 1/2.
- Ghost house simplified: ghosts sit in the house and are released to the cell above
  the door on timers (0, 3, 6, 9 s); eaten ghosts teleport back in. House interior is
  wall for movement. Door is wall.
- One shared score (`pb_score`) for maze and pinball; both screens show it.
- Energizer awards = `pb_energ` targets lit this visit, into empty corner slots,
  cap 4, extras 500 points (FR-4.5). Fruit not implemented (lanes score only).
- Chutes: open at board start and after a death; shut after a pinball visit
  (FR-2.4 / UX 4.5). Without a responding VDC they never open.
- No attract mode, no initials, no docent chord, no RESTORE soft restart; idle 60 s
  -> game over -> title (FR-6.5 logic, untested by a human).
- Bug found and fixed in VICE testing: `mz_resume` kept the award count in a scratch
  byte that `mz_paint` overwrote, so energizers were never placed.
- Test-only builds: `build/test-auto.d64` (`BPAUTO`): autopilot Pac-Man heading for a
  chute, auto-start from the title, bot flippers. VICE is deterministic, so the
  first chute visit of every run looks identical in screenshots.
- `tests/vice_peek.py` runs x128 with the remote monitor and dumps memory, used to
  check actor state and energizer slots.

## Known issues / not verified
- Joystick/paddle readout in DUALDEMO not exercised with real presses in VICE (runs
  were unattended). Idle state displays correctly.
- Nothing verified on real hardware yet.
- VICE VDC read timing varies a lot between runs (27 to 310 cycles per polled read);
  write timing is steady (~35 inline, ~72 polled, ~250 per random poke).
- Real-hardware unknowns that could bite tomorrow: VDC write speed (pinball frame
  budget), RGBI colour order, VIC bank 3 use at `$C000` (Tier 3 only), paddle button
  bit assignment (bits 2/3 of `$DC01`), load time of the 70-block Tier 3 file.
- The inline VDC polls in the pinball renderer have no timeout. They only run after
  start-up confirmed the VDC answers; a VDC that stops mid-game would hang the game.

## Art pass (2026-10-27 evening, VICE-verified only)
Goal: make it look like Bally Midway's 1982 Baby Pac-Man as a non-commercial
homage, in our own pixel art (generated by `tools/artlib.py`, `tools/mktable.py`,
`tools/mkmaze.py`; nothing extracted from any ROM). New images go to
`release/art-*.d64/.d71`; `release/tier*` and `release/stable-baseline/` are untouched.
`make art-pinball` / `make art-babypac` build and copy them (do NOT run `make release`
for the art pass: that target copies the tier images).

Inherited state: an earlier art agent was killed mid-run. It had rewritten
`tools/artlib.py`, `tools/mktable.py`, `tools/mkmaze.py`, `src/pinball/pinball.s`
(two VDC glyph banks), `src/pinball/pbmain.s` (PEAK / SLOW FRAMES readout) and
`src/lib/screen.s` (`vdc_font`), and added `tests/tvscale.py` (4:3 rescale of a
VICE shot, works) and `tests/vice_cycles.py` (samples a 16-bit symbol over the
remote monitor, works). Pinball built and ran; the maze did not build (mkmaze.py's
new interface had no matching maze.s).

### Checkpoint 1: pinball table (goal 1) - `release/art-pinball.d64/.d71`
- Art (from the inherited generator, kept as is): rounded double-line blue walls
  hugging the playfield from a distance field, rounded top corners (physics arcs
  too), ringed pop bumpers in Blinky red / Inky cyan / Pinky pink with a domed cap
  and highlight, red slingshots with a groove and lamp window, tapered yellow
  flippers with a round pivot pin, fruit-lane icons (cherry, strawberry, orange,
  bell), round cyan energizer targets, a 7x4 ball with a highlight pixel, "BABY
  PAC-MAN" plate on the top wall, marquee logo + ghost chase on the left panel,
  score box + big Pac-Man and Blinky on the right panel, Pac-Man and a frightened
  ghost in the funnel walls. One fg colour per cell; two glyph banks: bank 0 ($2000)
  = ROM font + table art + flipper poses + ball slots, bank 1 ($3000, attribute
  bit 7) = our bold font + panel art. Fits a 16K VDC (screen $0000, attributes
  $0800, glyphs $2000-$3FFF).
- **Frame budget fix (mine).** Inherited art pass measured with PINBOT (25 samples
  of the 64-frame max via `tests/vice_cycles.py`): median 16,569, peak 22,337,
  106 of 13,209 frames over one NTSC frame (17,045). Pre-art dev-notes figure:
  ~12,200 worst. Two changes in `pinball.s`:
  1. Flippers redraw only the cells that differ from the drawn pose (per block row,
     first..last changed cell). Adjacent poses differ in 12 cells over 2 rows, so a
     flipper change costs ~1,000-1,250 cycles instead of ~3,300-4,000.
  2. The panel text field (one per frame) is skipped on frames that redrew a flipper.
  Result (PINBOT, 20 samples): median 14,182, peak 18,020, 6 of 11,333 frames slow.
  Unattended `PINBALL`: 11,030-11,387 per 64-frame window (release tier 2: 11,355),
  peak ~13,000, 0 slow frames.
- PINBOT-only split timing (`PROF` checkpoints, compiled out of shipped builds):
  max flipper redraw 2,488 (both flippers), physics 9,442, ball render 6,495. The
  remaining rare slow frames are physics + ball spikes landing together; physics was
  not touched.
- Tested in x128: `art-pinball.d64` (64K VDC) and `art-pinball.d71` with `-VDC16KB`:
  load with `DLOAD"PINBALL",U9`, table drawn, balls serve, target lit and counted,
  readout working. Screens: `release/preview/art1-pinball-*` (`-before-` = the
  stable tier 2, `-tv` = rescaled to 4:3).

### Checkpoint 2: maze (goal 2) - `release/art-babypac.d64/.d71`
- Art from the inherited `tools/mkmaze.py` (kept): rounded double-line walls from a
  distance field (inner line 4 px inside each face), peach dots, round energizers,
  door, gate, chute arrows, our bold font as VIC glyphs 0-63, fruit HUD icons, 45
  sprite shapes (Pac-Man closed / half / wide x 4 directions, 10 death frames,
  multicolour ghosts 4 directions x 2 feet, frightened and flashing, eyes x 4,
  four fruits as body + detail sprites, "GO" + "!" banner).
- `src/maze/maze.s` ported to it (mine):
  - Memory: charset = all 256 glyphs at `$C800`; sprites moved to **`$E000`**
    (bank 3, pointers `$80+`; `$C400` only held 16). Image now ends at `$975D`.
    Program is 109 blocks (was 70): load time on the real 1571 not measured.
  - Colours by glyph class (`vclass`): walls light blue, dots light red (peach),
    energizers cyan, door light red, gate red, arrows / lives yellow. Paused look
    unchanged in spirit (blue walls, grey dots).
  - Pac-Man: 14-px hi-res sprite centred on the cell, chomp (closed / half / wide /
    half) in his direction, advancing only while he moves.
  - Ghosts: multicolour (MC0 white eye whites, MC1 blue pupils), Blinky red,
    Pinky light red, Inky cyan, Clyde orange; feet animate, eyes look where they
    go; in the house they bob and look up / down. Blinky starts outside the door,
    the others side by side in the house.
  - Per-ghost frightened flag (`gblue`): energizer turns every non-eyes ghost blue,
    flashing white for the last 2 s; an eaten ghost becomes **eyes** that run back to
    the door at 2 px/frame, re-enter the house and come out normal after ~0.5 s
    (previously eaten ghosts teleported).
  - Energizers in the corner slots blink (cyan / off, 8 frames).
  - **Fruit**: appears at Pac-Man's start cell after 70 and 170 dots for 9.5 s;
    cherry / strawberry / orange / apple (100 / 300 / 500 / 700). The fruit level
    rises by the fruit lanes lit on the pinball (cap 3) - the Baby Pac-Man link.
    HUD shows the level icon. Fruit vanishes on a pinball visit or a death.
  - Death: 0.5 s freeze, ghosts vanish, Pac-Man folds up (10 frames x 6).
  - GO! after a pinball visit: big "GO!" (expanded sprites 6/7) over the ghost house,
    flashing white / yellow for 1 s (was text on row 24).
  - HUD: blinking 1UP, HIGH SCORE, lives as Pac-Man icons, fruit icon.
- `tests/vice_script.py` (new): scripted x128 run over the remote monitor: wait for
  a frame number (warp off, so pokes land within a frame), poke / copy state, peek,
  then quit for exit screenshots of both screens. Used to force blue ghosts,
  flashing (pointers `$9D/$9E` = flash shapes, colour white at frame&8), eyes (Blinky
  home at frame 420 after being made eyes at 332, out again by 471), fruit, death.
- Tested in x128: `art-babypac.d64` (64K VDC) and `.d71` with `-VDC16KB`, loaded with
  `DLOAD"BABY PAC-MAN",U9` (45 s run): title on both screens. Autopilot build
  (`build/test-auto.d64`): maze -> chute -> pinball -> drain -> GO! -> maze with
  energizer placed and chutes shut, deaths, game over, high score kept (3770),
  second game (150 s and 240 s runs). Screens: `release/preview/art2-*`.
- Not verified: joystick feel with a human, fruit eaten by a human (logic only:
  tile check at row 15 / col 19), the GO! banner on hardware sprites expansion
  timing, real 1571 load time of the larger program.

### Checkpoint 3: title screens (goal 3) - `release/art-babypac.d64/.d71` (rebuilt)
- VIC title (`mz_title_*` in maze.s): "BABY" / "PAC-MAN" in our 11x7 logo letters at
  3x3-pixel blocks (3 cells tall, Pac-Man as the C; 48 glyphs from `mkmaze.py`,
  charset now 64..157), HIGH SCORE, a CHARACTER / NICKNAME roster with the four ghost
  sprites, a row of dots that Pac-Man eats while Blinky, Pinky and Inky chase him
  (sprites 0, 5-7), blinking PRESS FIRE TO PLAY, "A FAN-MADE HOMAGE - NOT FOR SALE".
  Colour cycling: BABY steps through 8 colours (8 frames each), a 3-column white
  shine sweeps across PAC-MAN.
- VDC title: the marquee on the left panel colour-cycles (`pb_logo_tint`, ~6,800
  cycles every 8 frames, title only); PRESS FIRE TO PLAY uses hardware blink.
- Transition: FIRE fades the 40-col screen light grey -> grey -> dark grey -> black
  (4 frames per step), sprites off, marquee back to its own colours, then the maze
  and READY!. The existing transitions remain: dimmed maze / undimmed table + GET
  READY / blinking GO! on the VDC; dimmed table + GO! banner sprite on the VIC.
- `mz_new_game` resets the sprite multicolour mask (the title makes 1-7 multicolour;
  fruit / GO! need hi-res).
- Tested in x128: release `art-babypac.d64` (64K) and `.d71` (`-VDC16KB`): title on
  both screens. Autopilot 240 s (64K) and 300 s (16K): title -> fade -> game ->
  handoff -> game over -> title -> second game, high score kept (4115).
- Load: VICE (true drive emulation) starts the art program between 16 and 19 s after
  RUN of the keybuf, Tier 3 between 13 and 16 s (113 vs 70 blocks).
- Screens: `release/preview/art-goal3-*` (named so; `art3-*` is the table v2 checkpoint).

### Checkpoint "pinball table v2, faithful layout" - `release/art2-pinball.d64/.d71`
Requested mid-run after the maintainer supplied a flat image of the real playfield
(a private reference image). Redrawn as our own pixel art inspired by its layout
(no tracing or copying of the artwork). Separate build so the `art-*` images stay
reproducible: `tools/mktable2.py` -> `build/table2_data.s`, `pinball.s` /
`pbmain.s` with `-D TABLE2`, `make art2-pinball`. The disk holds BABY PAC-MAN (full
game, v2 table) and PINBALL (v2), plus VDCTEST / DUALDEMO.
- Layout (40x25 cells, VDC columns 20-59):
  - rounded top whose corners turn the ball into two side lanes (columns 1-3 /
    36-38, guide walls at 4 / 35, rows 3-8), labelled F-R-U-I-T-S and T-U-N-N-E-L
    down the lanes; rollovers on row 8 marked 500 / 1000;
  - a wooden arch at the top centre (solid legs at columns 17 / 22): the tunnel
    mouth, and the ball is now served from inside it (x = 160);
  - a fruit cluster at the top of each loop; two pop bumpers (Inky cyan, Clyde
    orange);
  - the round-topped central block (yellow outline, visual only): four numbered
    columns (15, 16, 23, 24), each a PAC target (rows 7-9) over a MAN target
    (rows 11-13), numbers 1-4 between the groups, a centre lane of green up-arrows,
    TIMER and SPELL PAC-MAN under it;
  - Tier 2 funnel, slingshots, flippers and 4-cell drain unchanged (flipper
    geometry and pose blocks identical);
  - deep-wall art: a pink ghost with a butterfly net (left), a red ghost (right),
    the stork bringing baby Pac-Man on the apron, MAZE under the drain.
- Width kept at 40 columns: 320 px x 200 lines is 0.80:1 in square units against
  ~0.85 for the real table. Widening would have meant reworking every 40-wide row
  table in the renderer (`disp`, `tbl_codes`, `row40` pointers, panels) the night
  before the museum; judged not worth the risk.
- Rules (`-D TABLE2` paths in `pinball.s`): 10 lights with heights (`lit_h`): targets
  0-3 PAC, 4-7 MAN, 8 FRUITS lane, 9 TUNNEL lane. Target hit: lights its 3 cells,
  200. Column complete (PAC + MAN of one number) or word complete (all four PAC or
  all four MAN): +1 energizer for the maze and 500 each. All 8 lit: they reset.
  FRUITS lane: fruit level +1 for the maze (500); TUNNEL: 1000 + bonus. Spinner and
  side energizer targets are gone. 40-col status: ENERGIZERS EARNED, PAC-MAN TARGETS
  n/8, FRUITS LANE.
- Glyphs: bank 0 146/176, bank 1 245/256. Lane letters and numbers use the ROM font in
  bank 0 (the ball crosses them).
- **Cycles** (PINBOT, 25 samples of the 64-frame max, `tests/vice_cycles.py`):
  v2 median 12,696, max 16,342, peak 16,728, **0** of 11,001 frames slow; split
  maxima: flippers 2,495, physics 7,841, ball 6,488. (v1 art table, same tool:
  median 14,182, peak 18,020, 6 of 11,333 slow.) Unattended PINBALL v2 on 16K VDC:
  12,347 window, peak 12,952, 0 slow. Painting a lit target (3 cells) costs ~1,000
  cycles in the frame of the hit.
- Tested in x128: PINBOT 60 s and 200 s (targets lit 3/8, 30 balls served from the
  arch, no stuck ball), forced test (6 targets pre-lit by monitor pokes; real hits
  then completed a word: `pb_energ` 0 -> 1 -> 2), `art2-pinball.d64` BABY PAC-MAN
  title (64K), `.d71` PINBALL with `-VDC16KB`, the autopilot game with the v2 table
  on 16K VDC (handoff, game over, second game, high score kept). Screens:
  `release/preview/art3-*` (`art3-table-v1-before-tv.png` = the v1 art table).
- Not verified: how the side lanes and the target block play for a human (the bot
  only flips); ball flow into the lanes is VICE-observed only, not tuned.

### Checkpoint 4: SID sound (goal 4) - `release/art3-sound.d64/.d71`
- New image set (earlier `art-*` / `art2-*` images left as checkpointed): table v2 +
  sound, BABY PAC-MAN and PINBALL. `make art3-sound`. Note: re-running any art target
  now rebuilds from the current source, i.e. with sound.
- Voice 1 (`pb_sfx`, shared): the gate is dropped before each effect so every effect
  retriggers (before, the maze never released the gate, so only the first dot blip
  sounded). Effects: 1 flipper thwack (noise), 2 bumper / ghost-eaten ping
  (triangle), 3 launch / target / energizer / fruit, 4 drain / death (noise),
  5 dot chomp alternating two pitches ("wa-ka"), 6 lane blip (pulse). The maze loop
  now calls `pb_sfx_tick` so effects end cleanly.
- Voice 2: maze siren (triangle, sustain 7) sweeping over 64 frames; 32 frames and
  higher while ghosts are blue. Off at chute / pinball, death, board clear, title,
  game over.
- Voice 3: start fanfare during READY! of a new game: our own C-major arpeggio
  (C5 E5 G5 C6 - A5 C6 G5 - E5 G5 C6), NOT the arcade tune.
- Cycles: PINBOT (v2 + sound) median 13,670, max 16,695, peak 16,708, 0 of 11,538
  frames slow. The maze siren costs ~60 cycles a frame.
- Tested in x128: `art3-sound.d64` title (64K), `.d71` PINBALL with `-VDC16KB`,
  autopilot 200 s on 16K (second game, high score kept). Audio checked by recording
  the SID output to WAV (real time; warp mutes sound) and analysing loudness and pitch:
  `release/preview/art-goal4-sound-check.txt`. Nobody has listened to it yet.

## 2026-10-28 maze fix after the first real-hardware run

First run on the museum's flat C128: both screens in colour, game loads and plays. Bug seen on the real machine
(and reproduced in VICE once we looked): the corridors along the middle of the maze (tunnel row 12, columns 2-8
and 31-37) were walls in the game logic and "outside" in the wall art. Cause: tools/mkmaze.py walled every cell
outside the first and last '#' of a row except '='. The tunnel row has no border '#', so its corridor cells
counted as blank space. Effects: 14 dots Pac-Man could never reach (the board could not be cleared), the tunnel
mouths led nowhere, and the walls facing those cells had no lines (the "disjointed" look). Fix: only ' ' cells
outside the border are blank (typ and kind).

Why VICE missed it: no run ever left the chute route (the old autopilot only steers to a chute), and every
screenshot looked plausible. Lesson: test the whole maze, not the happy path.

Also changed: wall lines moved from 4 px to 5 px inside the wall face (core depth 8, line at least 4.5 px from
a corridor), so a straight corridor has 16 px between lines instead of 14 for a 14 px actor. The old art let
ghosts touch a line by 1 px at 12 junctions.

New tests (`make test-tour`):
- tests/maze_clearance.py: runs mkmaze in-process, slides every Pac-Man and ghost sprite pixel by pixel along every
  link between open cells (placement as draw_sprites does it), checks connectivity and that every dot is reachable.
- tools/mktour.py + AUTOTOUR build of maze.s + tests/run_tour.py: a route that eats every dot then crosses the
  tunnel both ways, walked by an autopilot at tile centres through the real movement code in VICE (ghosts harmless,
  idle timeout off). Passes on the new data in about 3 s of warp. Negative control: built with the old maze data
  it stalls with 174 dots left and fails.
- Zero page is not cleared at power-up: the AUTOTOUR counters are zeroed in mz_init_gfx.

New disk: release/art4-mazefix.d64/.d71 (disk name "baby pac-man fix"). Not yet run on the real machine.
