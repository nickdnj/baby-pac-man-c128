# Product Requirements Document: Baby Pac-Man for the Commodore 128

**Version:** 0.1 (draft, not reviewed)
**Last Updated:** 2026-10-27
**Author:** the maintainer DeMarco, with AI assistance (product-requirements agent)
**Requester / stakeholder:** the museum stakeholder, VCF National Board (email of 2026-10-26)
**Status:** Draft. Six machine questions are out to the stakeholder and not yet answered (see Section 9). Every requirement that depends on them rests on a numbered assumption.

**Sources:** the original request (the ask), the project brief (museum setup, research, the maintainer's decisions).

**Confidence markers used in this document**
- **[Confirmed]**: stated by the project owners, or marked confirmed in the research brief.
- **[Unconfirmed]**: from memory or shallow research. Verify before relying on it.
- **[Assumption An]**: a default we are building to until the stakeholder answers. See Section 8.

---

## 1. Overview

### 1.1 Purpose
the stakeholder wants Baby Pac-Man on the museum's Commodore 128, using both of its screens in color. Baby Pac-Man (Bally Midway, 1982) is a hybrid machine: a video Pac-Man maze sits above a short real pinball table, and two chutes link them. The C128 has two independent video outputs, the 40-column VIC-IIe and the 80-column VDC. That makes it a natural fit: the maze plays on one screen and the pinball on the other.

The game is a **tribute and an artwork** made by the software team [Confirmed, the maintainer 2026-10-27]. It is not an emulation of the arcade ROM. Where arcade details are uncertain, the team picks values that suit the tribute, and the stakeholder reviews them.

Prior art: research found no Baby Pac-Man port for the C64, C128 or Atari 8-bit (only Atari 7800), and no other true dual-screen action game on the C128. The leads are Volley For Two and the dual-monitor PETSCII Robots [Unconfirmed, shallow search]. This would be an unusual exhibit piece, which is part of its value to the museum.

### 1.2 Goals
- G1. A playable Baby Pac-Man tribute on a real C128. The maze is on the main screen and the pinball is on the second screen. Both are in color.
- G2. The defining mechanic works as the stakeholder described: entering a chute freezes the maze and switches play to pinball, the ball auto-launches, and when the ball drains down the middle, control returns to the maze and the pinball freezes.
- G3. Joystick for the maze; paddle buttons (one per flipper) for the pinball.
- G4. It runs unattended on a museum floor. Staff load it the way they load the current game, it boots into an attract mode, it survives a full day of visitors, and a docent can recover it without help.
- G5. Operational ownership goes to the museum. After handover, nobody needs the maintainer to run, reload or replace it.

### 1.3 Non-goals (v1)
- An arcade-accurate reproduction (ROM-level behavior, exact maze geometry, exact scoring tables, sampled arcade audio).
- Two-player alternating play. v1 is single player (A10).
- C64 mode, or a version that runs on one screen only.
- Saving high scores to disk. Scores are kept in RAM and reset at power-off; see 3.8 for the reason.
- Physical cabinet work, custom controllers or wiring. One exception: the optional fallback flipper buttons in A5, if the museum has no working paddles.
- An IP/licensing review. the maintainer decided there is no IP gate, because this is a tribute [Confirmed]. That decision is recorded here and is not reopened.
- Distribution beyond the museum. Wider release can be decided later (open question Q10).

### 1.4 Users
| User | Who | What they need |
|---|---|---|
| Visitor (primary) | Museum and VCF event visitors. Mixed ages, many first-timers to the C128, no instructions read, sessions of 1–5 minutes. | Walk up, see something moving on both screens, press fire, and understand within seconds which screen and which controller is live. |
| Docent / museum staff (operator) | Volunteers who open and close the exhibit. Not programmers. They know the existing `DLOAD` routine. | Load it in under a minute from a one-page card. Recover from a hang or crash by power-cycling and reloading. Keep spare disks. Know who to contact. |
| Museum owner (post-handover) | A person the stakeholder names (Q9). | Owns the exhibit, the disks, the source archive and the decisions about future changes. |
| the museum stakeholder (stakeholder, approver) | VCF board; requester. Has little time. | Short, visual check-ins: a pinball layout mock, then a playable build. Approves rules and look. |
| VCF community (secondary) | Visitors at VCF East and other events where the machine is shown. | Same as visitors. A credible piece of C128 craft. |

### 1.5 Success metrics
| ID | Metric | Target | How measured |
|---|---|---|---|
| S1 | Both screens display in color during play | 100% of the time on the museum setup (given A3) | Visual check at acceptance |
| S2 | Unattended stability on real hardware | 8 continuous hours in attract mode plus intermittent play, with no lockup, garbage or corruption on either screen; then 3 consecutive museum days | Soak test at M4 plus docent log |
| S3 | Load time from the 1571 | Under 60 s from typing the load command to attract mode (target under 30 s) | Stopwatch on real hardware |
| S4 | First-time visitor comprehension | 4 out of 5 untutored testers start a game and use the correct controller on each screen within 30 s of a screen switch | Hallway test at M4 |
| S5 | Flipper responsiveness | Flipper starts moving within 1 video frame (under 17 ms at NTSC) of a button press | Frame-step in VICE; feel test on hardware |
| S6 | Docent self-sufficiency | A docent who has not seen the game before loads it and recovers it from a forced crash, using only the operating card | Observed at handover (M5) |
| S7 | Ownership transferred | Museum owner named, handover checklist signed, no open item that depends on the maintainer | Handover sign-off |
| S8 | Stakeholder approval | the stakeholder approves the pinball mock (M2) and the final build (M4) | Email reply |

---

## 2. Scope

### 2.1 In scope (v1)
- Maze game on the 40-column VIC-IIe screen: Pac-Man, four ghosts, dots, energizers, fruit, two chutes at the bottom (A2).
- Pinball game on the 80-column VDC screen: a short table, two flippers, auto-launch, a center drain, and targets that feed back into the maze.
- The freeze/resume handoff between the two screens.
- Attract mode on both screens, title, free-play start, game over, high-score table kept in RAM.
- SID sound effects and short original jingles in the spirit of the original.
- A delivered disk (and disk images) that loads with the museum's existing `DLOAD` routine from the 1571.
- A docent operating card, spare disks, a source archive and a handover package.

### 2.2 Out of scope
See 1.3. Also out of scope: network features, joystick calibration UIs, and any settings menu that visitors can reach.

### 2.3 Constraints
- **Hardware:** a single stock Commodore 128 (model unknown, A1) with two monitors. A 1571 floppy is device 9 [Confirmed, docents thread]. No RAM expansion or cartridges are assumed.
- **Delivery:** must load from the museum's 1571 using a BASIC 7 command the docents already know (`DLOAD`, then `RUN`) [Confirmed pattern].
- **Builder:** the software team writes all of the code [Confirmed]. the stakeholder has no time for technical work.
- **Timeline:** no date has been given. Open question Q8, for example whether the target is VCF East.
- **Budget:** volunteer/tribute project. Any purchases (a monitor, paddles, buttons) are the museum's decision, not a project dependency, unless an assumption fails.

---

## 3. Functional Requirements

### 3.1 Screens and roles
- FR-1.1 The maze shall be displayed on the 40-column VIC-IIe output, and the pinball on the 80-column VDC output (A2).
- FR-1.2 Both screens shall show game content at all times while the program runs. The inactive game stays visible in its frozen state; it is never blanked. (the stakeholder: "The first screen freezes.")
- FR-1.3 The inactive screen shall carry a clear but unobtrusive "paused" cue, such as a dimmed or flashing banner or arrow ("PINBALL ->" or "<- BACK TO MAZE"). The active screen shall flash "GO!" for about 1 s after each switch, so visitors know where to look. The two monitors sit side by side (VIC front and center, VDC on the left) [Confirmed], so the cue should point physically toward the active monitor.

### 3.2 Maze (40-column screen)

**User story:** As a visitor, I want to steer Pac-Man through the maze with the joystick, eating dots and avoiding ghosts, so that I can clear the maze and score.

**Rules (tribute of the arcade; the research describes the arcade, not this build [Unconfirmed in detail]):**
- FR-2.1 Standard Pac-Man play: eat dots; four ghosts with chase/scatter behavior; touching a ghost costs a life, unless Pac-Man is energized, in which case the ghost is eaten for escalating points.
- FR-2.2 Energizers are earned on the pinball, not printed in the maze. The maze starts each board with **no energizers**, and targets on the pinball table award them (FR-3.6). This is the core link between the two halves in Baby Pac-Man [Unconfirmed: recalled from the arcade; verify against the reference video and Pinwiki before M2. If wrong, the maze starts with standard energizers and the pinball awards bonus points/fruit instead].
- FR-2.3 Two chutes at the bottom of the maze lead "down" to the pinball. When the chutes are open, Pac-Man entering either one triggers the handoff (3.4).
- FR-2.4 Chutes close after a return from pinball and stay closed until the board is cleared or a life is lost [Confirmed in research: Wikipedia/StrategyWiki/Pinwiki]. Closed chutes are drawn visibly different, for example as a gate.
- FR-2.5 Fruit appears per board as in Pac-Man. Its value can be raised by pinball targets (FR-3.6).
- FR-2.6 Three lives per game. An extra life at a score threshold (value set at M3).
- FR-2.7 Maze layout: the arcade maze is taller than the VIC's 25 text rows (about 28x31 tiles, from memory [Unconfirmed]). v1 uses a **redrawn maze that fits one 40x25 screen without scrolling**. It keeps the topology that matters: the ghost house, side tunnels if they fit, and the two bottom chutes. the stakeholder wrote "the maze should be fine on the main screen"; this compromise is not visible in his note, so it is flagged for his review at M2.

**Acceptance criteria**
- [ ] Pac-Man and the four ghosts move smoothly at the full frame rate (60 Hz NTSC, A4) with no sprite flicker.
- [ ] Each ghost is distinguishable by color.
- [ ] Clearing the board starts the next board and reopens the chutes.
- [ ] Entering an open chute always triggers the handoff. Entering a closed chute does nothing (it acts as a wall).
- [ ] The maze resumes from exactly the frozen state after pinball (see FR-4.4).

### 3.3 Pinball (80-column screen)

**User story:** As a visitor, I want to keep the ball alive with the two flipper buttons and hit targets, so that I can earn energizers and bonuses to take back into the maze.

- FR-3.1 A short table drawn on the VDC screen, laid out per Section 6.4. Two flippers at the bottom, a center drain between them, **no outlanes** [Confirmed in research], and no plunger.
- FR-3.2 Auto-launch: when play switches to pinball, the ball launches by itself after a 1 s "GET READY" beat, so the player has time to reach the paddles [the stakeholder: "It automatically launches when you switch screens."]. Launch strength may vary slightly so play is not deterministic.
- FR-3.3 Left paddle button → left flipper; right paddle button → right flipper. Holding the button holds the flipper up; releasing it drops the flipper.
- FR-3.4 Ball physics are believable rather than simulated: gravity, wall and bumper rebounds, flipper impulse that depends on where the ball meets the flipper and whether the flipper is moving. Ball speed is capped so the ball can never pass through a flipper or wall (no tunneling).
- FR-3.5 The **only** way to leave the pinball is a drain down the center [the stakeholder; Confirmed]. There is no tilt and no ball save in v1.
- FR-3.6 Table features, a tribute set to confirm against the reference video at M2:
  - Energizer targets: award energizers, which are placed in the maze on return (FR-2.2).
  - Fruit targets: raise the value of the next fruit.
  - Bumpers and/or a spinner for points.
  - A visible tally on the side panel of what this ball has earned.
- FR-3.7 A watchdog for a stuck ball: if the ball has not hit a scoring element or a flipper for 10 s (value to tune), a nudge moves it. If it is still stuck after 3 nudges, the ball is treated as drained. An unattended exhibit must never hang on a trapped ball.

**Acceptance criteria**
- [ ] The ball launches within 1.5 s of the screen switch with no input.
- [ ] Each flipper responds within 1 frame (S5) and never moves without input.
- [ ] Center drain returns control to the maze 100% of the time. No other exit exists.
- [ ] Awards earned on pinball show up in the maze on return.
- [ ] A ball trapped by design or by a bug resolves within 40 s (FR-3.7).

### 3.4 Maze → pinball handoff

**User story:** As a visitor, when Pac-Man goes down a chute, I want the game to switch to the pinball screen and launch the ball so I can play pinball immediately.

**Flow**
1. Pac-Man enters an open chute.
2. Maze freezes: Pac-Man, ghosts, timers (energizer, fruit, ghost mode) and sound all stop. The maze stays on screen with a paused cue (FR-1.3).
3. A short transition sound plays. The VDC screen shows "GO!" and "GET READY".
4. The pinball table becomes active (unfrozen). The ball auto-launches (FR-3.2).
5. Flipper input is live. Maze input is ignored.

- FR-4.1 Only one game simulates at a time. The frozen game does no work and holds no timers.
- FR-4.2 The switch takes no more than 0.5 s from chute entry to visible "GO!" on the VDC screen.

### 3.5 Pinball → maze handoff
**Flow**
1. The ball drains down the center.
2. Pinball freezes. The table stays on screen with its earned tally and a paused cue.
3. Earned awards are applied to the maze: energizers placed, fruit value raised, points added.
4. The maze resumes. Chutes are now closed (FR-2.4).

- FR-4.3 The drained ball is not a lost life. Lives are lost only in the maze [Unconfirmed vs. arcade; matches the stakeholder's description].
- FR-4.4 Resume placement: Pac-Man reappears at the exit of the chute he entered, facing up. Ghosts resume from their frozen positions. **Grace period:** ghosts hold still for 1.5 s ("READY") after resume, so a ghost that was frozen next to the chute cannot kill Pac-Man instantly. (Design decision for the stakeholder to confirm. The alternative is to resume Pac-Man exactly where he froze.)
- FR-4.5 Where energizers are placed: in the classic four corner positions, filling empty ones first. The cap is 4 on the board at once, and extra awards convert to points [tribute choice; confirm with the stakeholder].

### 3.6 Controls
- FR-5.1 Maze: digital joystick (Atari-style DB9), four directions. Pac-Man turns are buffered: a direction pressed slightly before a junction is taken at that junction.
- FR-5.2 Pinball: Commodore/Atari paddle pair, using **only the fire buttons**, one per flipper. The paddle knobs are not used. Paddle fire buttons read as the left/right lines of the control port on CIA1 ($DC00/$DC01) [Unconfirmed, from memory; verify in the C128 Programmer's Reference Guide].
- FR-5.3 Default ports: joystick in **port 2**, paddles in **port 1**. Both stay plugged in (A5, A6).
- FR-5.4 Fallback flipper input: joystick left/right also work the flippers during pinball, so the exhibit still works if the paddles fail or go missing. Joystick fire starts a game.
- FR-5.5 To start a game from attract mode: press joystick fire or either paddle button.
- FR-5.6 The keyboard is ignored during attract mode and play. Visitors cannot break out of the game, including with RUN/STOP. One exception: a documented docent key chord that returns to the title (not to BASIC); see 3.8. RUN/STOP+RESTORE and the reset button are the docent's hard recovery.
- FR-5.7 Exact port and paddle line behavior (including port 1 input interfering with keyboard scanning) is an architecture item to verify in VICE and on hardware.

### 3.7 Game flow and attract mode
- FR-6.1 Once loaded, the program goes straight to attract mode. No prompt is needed.
- FR-6.2 Attract mode cycles through: title on both screens; a short demo of the maze (AI-driven Pac-Man) with the pinball screen showing its table and the high-score table; a demo chute handoff with a short AI pinball rally; "PRESS FIRE" prompts on both screens.
- FR-6.3 Free play, no credits.
- FR-6.4 Game over: show the score on both screens. If it is a high score, take 3-letter initials with the joystick, with a 20 s timeout that falls back to "???". Then return to attract mode.
- FR-6.5 Idle handling: if there is no input for 60 s during play, the game is abandoned and returns to attract mode. This covers visitors who walk away mid-game, including mid-pinball, where FR-3.7 alone would not end the game.

### 3.8 Exhibit operations behavior
- FR-7.1 High scores live in RAM only. Writing to disk unattended risks corrupting the only disk in the drive, and the 1571 would wear for no exhibit benefit. The table resets on power-cycle; the default table has tribute names.
- FR-7.2 Docent key chord (for example CTRL+SHIFT+F1, to be defined) returns to the title and resets high scores. It is documented only on the operating card.
- FR-7.3 The program never needs the disk after loading. The docent may remove it.
- FR-7.4 Sound volume: SID output is at a moderate default. If the museum wants a quieter exhibit (Q11), a build-time setting is available, not a visitor-facing menu.

---

## 4. Non-Functional Requirements

### 4.1 Performance
- NFR-1 The maze runs at full frame rate (60 Hz NTSC). Sprite motion is smooth, with no visible tearing.
- NFR-2 The pinball updates the ball and flippers at least 30 Hz (target 60 Hz) with no visible VDC update artifacts (torn ball, stale characters).
- NFR-3 The frozen 40-column maze stays stable and readable while the pinball runs. This rules out CPU speed tricks that garble or blank the VIC display (see R4).
- NFR-4 Handoff latency ≤ 0.5 s (FR-4.2). Flipper latency ≤ 1 frame (S5).

### 4.2 Reliability (unattended museum use)
- NFR-5 No lockups, crashes or screen corruption in an 8-hour soak test on the real museum machine (S2).
- NFR-6 No state accumulates over time: no memory growth, no counters that wrap and break play (for example a score past 999,999 rolls cleanly or caps).
- NFR-7 Deterministic recovery: power-cycle, reload, and the game is back in under 2 minutes, using only the operating card.
- NFR-8 The program never writes to disk (FR-7.1).
- NFR-9 Defensive VDC access: every VDC register access waits on the status flag. Block copy/fill is used only if it is proven reliable on the target hardware (R1).

### 4.3 Usability and accessibility
- NFR-10 Everything a visitor needs is on screen. No instructions are required to start. A one-line hint on each screen names the controller ("JOYSTICK" / "PADDLE BUTTONS = FLIPPERS").
- NFR-11 Color is not the only signal for game state. Active/paused screen, open/closed chutes and ghost vulnerability are also shown by shape, flashing or text. This also keeps the game playable if a monitor is monochrome (A3).
- NFR-12 Text is legible from about 1.5 m on both monitors: no single-pixel-wide text on the VDC screen.

### 4.4 Security
Not applicable beyond FR-5.6 (visitors cannot drop to BASIC or alter the program).

---

## 5. Technical Requirements and Constraints

These are requirements and verified-or-not facts for the architecture team, not a design.

### 5.1 Platform facts
| Fact | Status | Consequence |
|---|---|---|
| VIC-IIe (40-col) and VDC (80-col) are independent and can display at the same time | [Confirmed] in principle; Volley For Two reportedly uses both [Unconfirmed whether simultaneously, Q5] | Basis of the whole design |
| VDC has its own RAM, reached indirectly through a register pair with a status poll | [Confirmed] | Every VDC write costs CPU time; plan the update budget |
| VDC RAM is 16K on the flat C128 and plastic C128D, 64K on the C128DCR | [Unconfirmed, memory]; model unknown (A1) | Design to 16K |
| VDC has block copy and block fill | [Confirmed] | Block copy reported corrupting on real DCR hardware while fine in VICE (R1) |
| VDC has no hardware sprites | [Unconfirmed, memory; widely held] | The pinball ball and flippers must be drawn in software |
| VDC text mode: per-cell foreground color (16 RGBI colors) on one global background color; custom charset; 8x8 cells (taller possible) | [Unconfirmed, memory] | Main color constraint for the pinball (6.4) |
| VDC bitmap mode: 2 colors per 8x8 cell with attributes; full 640x200 color bitmap needs more than 16K (16,000 + 2,000 bytes) | [Unconfirmed] | Color bitmap is out at 16K, unless the bitmap is shortened (about 640x176 might fit in 16K, unverified) |
| VDC color needs an RGBI (digital) monitor; the VDC's composite/mono pin gives monochrome only | [Unconfirmed, memory] | "Both screens in color" depends on A3 |
| VIC-IIe display is garbled/blanked when the C128 runs at 2 MHz (except during border time) | [Unconfirmed, memory] | Conflicts with keeping the frozen maze visible (NFR-3); plan for 1 MHz or a border-time 2 MHz trick |
| VIC-IIe has 8 hardware sprites | [Confirmed, well known] | Pac-Man + 4 ghosts + fruit = 6. Fits. |
| VICE x128 shows the VDC in a separate window | [Confirmed] | Both screens can be developed and tested in emulation |
| cc65 ships a VDC driver (libsrc/c64/emd/c64-vdc.s) | [Confirmed] | Reference code for VDC access |

### 5.2 Toolchain
- TR-1 Choice of assembler/compiler (cc65 + assembly, or KickAssembler, or similar) is an architecture decision. Requirement: reproducible build from a clean checkout, with one command producing the PRG and the disk images.
- TR-2 Source, build scripts and disk images live in this repo (`src/`, `tests/`, release artifacts).
- TR-3 VICE x128 is the development and regression environment. Real hardware is the acceptance environment. VICE passing is **not** acceptance (R1).

### 5.3 Delivery format
- TR-4 Deliverable: one program file on a 5.25" disk that loads in C128 mode with `DLOAD "BABY PAC-MAN",U9` then `RUN` (exact syntax to verify on BASIC 7.0; filename final at M3). Also a `.d64`/`.d71` image and a bare `.prg` for SD-card use if that drive returns (A7).
- TR-5 Note on filenames: the docents' `DLOAD "NAME.PRG"` pattern looks like it comes from the SD-card drive, where host filenames include `.PRG`. On a real 1571 disk the name has no `.PRG` suffix. The operating card must use the exact name on the delivered disk. [Unconfirmed: inferred.]
- TR-6 Autoboot (optional, recommended): the C128 power-on autoboot reads the boot sector from device 8 only [Unconfirmed, memory]. If the museum sets the 1571 to device 8 (the SD drive is out anyway), the delivered disk can autoboot straight into attract mode: power on and it runs. This is the most reliable way for docents to start it. The disk must still load manually from device 9 if the drive stays at 9.
- TR-7 Video standard: NTSC build (A4). If PAL is needed, a PAL build variant.

### 5.4 Memory budget (VDC, 16K baseline; estimate for architecture to confirm)
| Use | Bytes |
|---|---|
| Screen (80x25 character codes) | 2,000 |
| Attributes (80x25 colors) | 2,000 |
| Character set, 512 glyphs x 16 bytes | 8,192 |
| Second screen + attribute buffer (optional double buffer) | 4,000 |
| Total | about 16,192 of 16,384 |
Tight but feasible. If double buffering is not needed, about 4K is free.

---

## 6. User Experience

### 6.1 Key journey (visitor)
1. Visitor approaches. Both screens animate (attract mode); the center screen shows the maze demo, the left screen the pinball table.
2. "PRESS FIRE": visitor grabs the joystick and presses fire. The game starts in the maze.
3. Visitor clears dots and reaches a bottom chute. Maze freezes and dims; the left screen flashes "GO! PADDLE BUTTONS = FLIPPERS".
4. Ball auto-launches. Visitor picks up the paddles and flips. Targets light; the side panel shows "+2 ENERGIZERS".
5. Ball drains down the middle. Pinball freezes; the center screen flashes "GO!" and energizers appear in the maze.
6. Visitor plays on until out of lives, enters initials, and the game returns to attract mode.

### 6.2 Key journey (docent)
Morning: power on monitors, drive and C128. Insert the disk. Type the command from the card (or nothing, if autoboot, TR-6). Attract mode is running. If a problem occurs: power-cycle, reload. Evening: power off. Spare disks are in the labeled sleeve by the computer.

### 6.3 Dual-screen color requirements
- UX-1 Both screens in color during all modes (the stakeholder; G1), given A3.
- UX-2 Maze (VIC): black background, blue maze walls, yellow Pac-Man, red/pink/cyan/orange ghosts, blue frightened ghosts. The VIC palette has all of these, though "pink" and "orange" are approximations [Unconfirmed: palette match to verify on the monitor].
- UX-3 Pinball (VDC, RGBI palette): black global background (text mode allows only one background color, 5.1). Table art is drawn in foreground colors per 8x8 cell. Ball is white or light gray.
- UX-4 Color clash: when the ball passes through a cell that holds colored table art, the ball takes on that cell's color. Design the table so that the ball's paths run mostly through empty, background-colored cells, and keep colored decorative art away from the main ball lanes. Accept small clash where unavoidable. the stakeholder should see this in the M2 mock, not discover it at M4.
- UX-5 Maze and table use the same visual vocabulary, so the link reads at a glance: the same Pac-Man yellow, the same energizer icon, matching chute art at the bottom of the maze and the top of the table.

### 6.4 Screen real estate: the stakeholder's question, answered
**the stakeholder asked:** "What I'm not sure about is screen real-estate for the pinball. If there is enough room to fit everything."

**Short answer: yes, it fits. That is a reasoned feasibility view, not yet a proven one. Six items below must be verified in VICE and on the real machine.**

Why it fits:
1. **The table is short.** Baby Pac-Man's pinball is a shortened table under the maze [Confirmed in research]. A full-length pinball table would be awkward on a landscape monitor. A short one is a good match.
2. **The VDC screen is wide.** 80x25 characters, 640x200 pixels. A central band of about 40 columns x 25 rows (320x200 pixels) covers half the screen's width and its full height. On a 4:3 monitor that band is roughly 2:3, upright like a short pinball table. The research suggested using the center 200–250 pixels; 320 gives more room and still leaves side panels.
3. **The sides hold the rest.** About 20 columns on each side for score, high score, balls/lives, earned energizers, fruit level, the "PADDLE BUTTONS = FLIPPERS" hint and decorative art. Nothing else needs to compete with the table for space.
4. **Element budget, in 8x8 cells (rough):** flippers about 6–7 cells long each; drain gap about 3 cells; chute/launch entries over 2–3 rows at top; flipper and drain zone 3–4 rows at bottom. That leaves about 18 rows x 36 columns for targets, bumpers and lanes. That is enough for a tribute feature set (FR-3.6).
5. **The pinball does not compete with the maze for CPU time.** Only one game runs at a time (FR-4.1), so the pinball gets nearly the whole CPU while it is active.
6. **Text mode with a custom charset works at 16K VDC RAM** (5.4), so the answer does not depend on the C128 model (A1).

Compromises the stakeholder should know about:
- The VDC's pixels are about twice as tall as they are wide. A round ball is drawn about 2 cells wide by 1 cell tall in pixel terms, or a 6–8 pixel wide by 4 line tall shape. Curves and angled flippers look stair-stepped. This is the 8-bit look, not a bug.
- One background color for the whole table, and one foreground color per 8x8 cell (UX-4). The table will be bold and blocky rather than painted.
- With 25 rows, vertical precision is limited. Ball motion is smooth (pixel-level), but the art is cell-level.

**What must be verified (owner: architecture/dev, at M1–M2):**
| # | Item | Where |
|---|---|---|
| V1 | Ball and flipper updates at 30–60 Hz within the VDC access budget at 1 MHz, with no tearing | VICE, then real hardware |
| V2 | Ball looks round and readable on the museum's 80-column monitor (pixel aspect) | Real monitor (photo from the museum is acceptable) |
| V3 | Overscan: the left/right edges of an 80-column display may be cut off on some monitors. Keep the table and critical text inside a safe area | Real monitor |
| V4 | Character budget: flipper animation frames + ball soft-sprite glyphs + table art fit in 256 (or 512) glyphs | VICE |
| V5 | VDC memory map fits 16K (5.4) | VICE configured for 16K VDC |
| V6 | VDC write/copy behavior on the actual model; no corruption over a soak test (R1) | Real hardware only |

Options if something fails: a taller character cell or extra rows (the VDC can be reprogrammed for more rows, at a monitor-compatibility risk); a bitmap table if the machine turns out to have 64K VDC RAM (A1); or simplifying the table art.

### 6.5 Error handling (visitor-facing)
- No error messages are visible to visitors during normal operation. Internal faults (for example a VDC status timeout) reset to attract mode rather than hanging.
- If the 80-column screen is unexpectedly absent (no monitor), the game still runs; the docent card covers checking the monitor.
- No demo fallback disguised as real play (project rule): attract mode is clearly labeled as a demo ("PRESS FIRE TO PLAY").

---

## 7. Dependencies, Risks

### 7.1 Dependencies
| Dependency | Impact if unavailable |
|---|---|
| the stakeholder's answers to Q1–Q6 | Team builds to the assumptions; rework risk listed in Section 8 |
| Access to real C128 hardware for early testing (A12) | R1 cannot be retired early; the risk moves to M4, where a failure is most expensive |
| An RGBI color monitor on the 80-column output (A3) | The color goal (G1) is not met on the 80-column screen |
| Working paddles (A5) | Fallback to joystick left/right flippers (FR-5.4) or simple buttons |
| A named museum owner (Q9) | Handover (M5) cannot complete; the project fails the ownership rule |
| Reference material on arcade rules (YouTube video, Pinwiki) | Tribute rules drift from the stakeholder's expectations. The reference video has **not been watched** by this agent. |

### 7.2 Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | VDC block copy/fill corrupts on real hardware (reported on DCR) though fine in VICE | Medium | High | Smoke test VDC writes on real hardware in M1. Default to CPU-driven writes; use block ops only after a hardware soak test. Treat VICE as not authoritative for VDC timing. |
| R2 | CPU timing: VDC access is slow (each byte goes through a status poll), and VIC bad lines and sprites steal cycles. Pinball could miss 30 Hz | Medium | Medium | One game runs at a time (FR-4.1). Update only the cells that changed. Measure the cycle budget in M1. |
| R3 | Color limits: VDC text mode gives one background color + per-cell foreground; ball color clash; VIC palette approximations of ghost colors | High (certain to some degree) | Low–Medium | Design around it (UX-4). Show the stakeholder the real look at M2. |
| R4 | 2 MHz mode garbles/blanks the VIC display, but the frozen maze must stay visible (NFR-3) | Medium | Medium | Plan at 1 MHz. Use 2 MHz only during border time if needed, verified on hardware. |
| R5 | VIC maze does not fit 25 rows at arcade proportions | Certain | Low | Redrawn maze (FR-2.7). Flag to the stakeholder at M2. |
| R6 | 80-column monitor is monochrome or composite (A3) | Unknown | High for G1 | Ask the stakeholder (Q3). Mono-safe design (NFR-11). Museum sources an RGBI monitor or adapter if needed. |
| R7 | Model is DCR (64K VDC) and shows the reported block-copy problem, or a flat C128 with 16K differs in behavior | Unknown | Medium | Design to 16K, CPU writes, early hardware test |
| R8 | Docents type the wrong load command or device (DLOAD defaults to device 8) | Medium | Medium | Exact command on a laminated card; autoboot option (TR-6) |
| R9 | Floppy wear or disk failure on the exhibit | Medium over months | Medium | Load once per day; no disk writes; 3 write-protected copies plus an image on SD/USB |
| R10 | Stuck ball or idle game hangs the exhibit | Medium | Medium | FR-3.7 and FR-6.5 |
| R11 | Rules or feel differ from what the stakeholder expects of Baby Pac-Man | Medium | Medium | M2 mock review; confirm FR-2.2, FR-4.4, FR-4.5 with the stakeholder |
| R12 | Project stays dependent on the maintainer | Medium | High (project rule) | Handover plan, Section 11 |

---

## 8. Assumptions (defaults until the stakeholder answers)

Each assumption gives a default, what the team builds, and what changes if it is wrong.

| # | Assumption (default) | If wrong |
|---|---|---|
| **A1** | **C128 model and VDC RAM: unknown, so design to 16K VDC RAM** (flat C128 or plastic C128D). Text-mode pinball. (Maps to Q1.) | **If 64K (C128DCR):** nothing breaks. Bitmap-mode table art becomes an optional upgrade. R1 (DCR block-copy corruption) becomes more likely, so early hardware testing matters more. **If an upgraded or odd machine:** confirm with a quick VDC RAM test program the team supplies. |
| **A2** | **The main screen is the 40-column VIC screen**, front and center; maze there, pinball on the 80-column VDC on the left. (the maintainer's confirmed assumption; Q2.) | **If the stakeholder wants the maze on the 80-column screen:** the cheapest fix is to swap the physical monitor positions, with no code change. Moving the maze onto the VDC in software is a major redesign (no sprites on the VDC) and is not recommended. |
| **A3** | **The 80-column monitor is RGBI color** (for example a 1084/1084S/1902-type set in digital RGBI mode). (Q3.) | **If composite or monochrome:** the VDC output shows in mono only; "both screens in color" cannot be met in software. The game still plays (NFR-11). The museum would need an RGBI monitor or an RGBI-to-VGA/HDMI adapter. Decision for the stakeholder. |
| **A4** | **NTSC machine** (US museum). | **If PAL:** timing tables and speeds change; build a PAL variant (low effort if planned from the start, so architecture should keep timing values parameterized). |
| **A5** | **One working joystick and one working paddle pair with working fire buttons** are on hand. (Q4.) | **If no paddles:** the flippers use joystick left/right (FR-5.4), or the museum adds two arcade buttons wired to a DB9 (simple; parts about $10–20, not a project deliverable). **If the joystick is flaky:** the museum sources one. The game is unaffected. |
| **A6** | **Joystick in port 2 and paddles in port 1, both plugged in permanently**, so visitors switch hands, not cables. | If the museum wants a single controller per port or swaps cables, the defaults change by build setting. If port 1 input disturbs keyboard scanning in a way that matters, flippers move to port 2 too (joystick fallback). |
| **A7** | **The load device is the 1571 at device 9; the SD-card drive stays removed.** Load with `DLOAD "<name>",U9` then `RUN`. (Q6.) | **If the SD drive returns as device 8:** also deliver the `.prg`/disk image for SD, and update the card. **If the museum sets the 1571 to device 8:** enable autoboot (TR-6), the best option. |
| **A8** | **Both video outputs and monitors work at the same time on the museum machine** (for example, Volley For Two shows on both at once). (Q5.) | If only one screen works at a time, this is a cabling or monitor problem to fix before M4. Nothing is gained by building around it. |
| **A9** | **Exhibit hours are about 8 hours a day.** Staff power on and off daily. | If the machine is left on for days, the soak test extends to 72 h (S2). |
| **A10** | **Single player only** is acceptable. | Two-player alternating is a v2 feature (moderate effort: state per player for both games). |
| **A11** | **"Go down" means Pac-Man entering one of two chutes at the bottom of the maze**, as in the arcade. | If the stakeholder means something else (for example a joystick-down command anywhere), it is a rule change, small in code. Confirm at M2. |
| **A12** | **The team can get hands-on time with a real C128 + 1571 + RGBI monitor during M1**, either at the museum or a borrowed or owned machine. | If not, R1/R2/R4 are only retired at M4, and the schedule should include a buffer for a hardware fix cycle. |
| **A13** | **Free play.** | No change needed for coins; out of scope. |
| **A14** | **Arcade rules that we have not verified** (energizers earned only on pinball FR-2.2, drain not costing a life FR-4.3, resume placement FR-4.4, energizer cap FR-4.5) follow the tribute choices in this PRD. | Each is a contained rule change. the stakeholder reviews them at M2. |

**Assumptions that most need the stakeholder's answer:** A3 (monitor color: decides whether G1 is achievable), A1 (model: decides R1 exposure and the 64K options), A5 (paddles: decides the control scheme), A7 (device: decides load command and autoboot), A12 (hardware access: not one of the stakeholder's six questions, but it decides when the biggest risk is retired).

---

## 9. Open Questions

Sent to the stakeholder in the maintainer's drafted email (not yet answered):
- [ ] Q1. Which C128 model (flat, D, DCR), and so VDC RAM (16K or 64K)? → A1
- [ ] Q2. Which screen is "main" (assumed the 40-column)? → A2
- [ ] Q3. What do the two monitors plug into; is the 80-column one RGBI color? → A3
- [ ] Q4. Controllers on hand: joysticks, paddles, working buttons? → A5
- [ ] Q5. Does Volley For Two drive both screens at once on the real machine? → A8
- [ ] Q6. SD-card drive status and device number (8 or 9) for the delivered file? → A7

New from this PRD (not yet asked; batch into the next note to the stakeholder):
- [ ] Q7. Could the team get time on the museum's C128 during the prototype phase, or is there another C128 we can test on? → A12
- [ ] Q8. Is there a target date or event (for example VCF East)?
- [ ] Q9. Who at the museum will own the exhibit after handover (name and contact)? → Section 11
- [ ] Q10. Should the finished tribute be shared publicly (for example csdb.dk, GitHub), or kept as a museum exhibit only?
- [ ] Q11. Any volume or sound constraints on the museum floor?
- [ ] Q12. Is it all right to set the 1571 to device 8 for autoboot? → TR-6
- [ ] Q13. Rule checks: are FR-2.2, FR-4.3, FR-4.4 and FR-4.5 what you remember from the arcade? (Best asked alongside the M2 mock.)

Team-internal:
- [ ] Q14. Watch the reference video and check Pinwiki/StrategyWiki for the table feature list and arcade rules before M2.
- [ ] Q15. Check Volley For Two in VICE x128 to see how it drives both screens.
- [ ] Q16. Retrieve the Wiebo de Wit VDC examples and the PETSCII Robots dual-monitor notes (Scott Robison) as references.

---

## 10. Milestones (proposed)

No calendar dates until Q8 is answered. Each milestone has an exit gate.

| M | Name | Contents | Exit criteria |
|---|---|---|---|
| **M1** | **Prototype both screens** | Toolchain picked; one build driving both screens at once in VICE: a sprite moving in a test maze on the VIC, a custom-charset ball bouncing on the VDC. Cycle-budget measurement (R2). **Early real-hardware smoke test** of VDC writes and the dual display if A12 holds; this is a deliberate addition to the ordering, because R1 is the biggest unknown. | Both screens live together in VICE; VDC write test passes on real hardware (or the gap is flagged); V1, V4, V5 measured |
| **M2** | **Pinball mock for the stakeholder** | VDC table layout at full size with side panels, colors and the ball shape; a playable flipper-and-ball demo; the redrawn maze shown on the VIC. Screenshots/video sent to the stakeholder with the rule questions (Q13) in one email. | the stakeholder approves the layout and look (S8), or the requested changes are listed; screen-real-estate verdict confirmed (V2/V3 if hardware is available) |
| **M3** | **Full game** | Complete maze and pinball rules, handoffs both ways, attract mode, high scores, sound, idle and stuck-ball handling, disk build. Test plan from QA. | All FR acceptance criteria pass in VICE; QA gate passes; release candidate disk image |
| **M4** | **Real-hardware test and acceptance** | On the museum machine: load from the 1571 (timing S3), 8-hour soak test (S2), visitor hallway test (S4), color check (S1), the stakeholder's play-through. | S1–S5 and S8 met; any hardware-only defects fixed and re-tested |
| **M5** | **Handover to the museum** | Section 11 package delivered and walked through with the museum owner and at least one docent. | S6 and S7 met; sign-off from the museum owner |

---

## 11. Operational Handover (ownership transfer to the museum)

The project requires that operational ownership passes to the actual users; the maintainer in the loop forever counts as failure. The users here are the museum staff, not the maintainer and not the stakeholder personally.

### 11.1 Owner
- A named museum owner (Q9), with a named backup docent. They own the exhibit, the disks, the operating card and future decisions.

### 11.2 Handover package
1. **Operating card** (one page, laminated, kept by the computer): power-on order, the exact load command (or "just power on" if autoboot), what each screen and controller does, the docent key chord, how to recover (power-cycle, reload), a checklist for when it won't load (disk, device switch, cables, monitor input), and where the spares are.
2. **Three write-protected copies** of the game disk, labeled with name, version and date, plus disk images (`.d64`/`.d71`/`.prg`) on a USB stick or SD card kept with the DualMon2 floppy.
3. **Docent walkthrough**: a 15-minute session at M5 where a docent does the load and a forced recovery themselves (S6).
4. **Source archive**: the full repo (source, build instructions, disk images, this PRD and later design docs), handed over as an archive the museum keeps, and hosted where VCF volunteers can reach it, subject to Q10. The README explains how any C128-literate volunteer can rebuild and change it.
5. **Known limitations sheet**: color clash, RAM-only high scores, single player, and anything left from M4.
6. **Support path after handover**: the museum owner decides changes. Requests go to whoever the museum chooses (a VCF volunteer, or the community via the public repo if Q10 says public). the maintainer is not the default support contact. Any short warranty period offered by the team (for example 30 days of fixes for defects) is time-boxed and stated in writing at M5.

### 11.3 Handover sign-off
Owner named; package received; docent completed load and recovery unaided; owner confirms no open item depends on the maintainer.

---

## 12. Handoffs to the team (structured summary)
- **Software architecture:** Section 5 facts table (verify every [Unconfirmed] row), 5.4 memory budget, R1/R2/R4, the V1–V6 checklist, A1/A4 parameterization (16K baseline, NTSC with PAL-ready timing).
- **UX design:** 6.3 color requirements, 6.4 layout band and side panels, FR-1.3 paused/active cues, the redrawn maze (FR-2.7), the operating card (11.2).
- **Dev planning:** milestones M1–M5 with exit gates, and the early hardware smoke test in M1.
- **QA strategy:** S1–S6 metrics, soak test, stuck-ball and idle cases, real hardware as the acceptance environment, the hallway test.
- **Marketing:** not needed for v1 beyond optional exhibit signage; revisit if Q10 says public release.

---

## 13. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-10-27 | the maintainer DeMarco with AI assistance | Initial draft from the stakeholder's email and the research brief; assumptions A1–A14 stand in for unanswered questions Q1–Q6 |
