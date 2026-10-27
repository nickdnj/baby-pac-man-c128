# Test Plan: Baby Pac-Man for the Commodore 128

**Version:** 0.1 (draft, not reviewed)
**Last Updated:** 2026-10-27
**Author:** the maintainer DeMarco, with AI assistance (qa-strategy agent)
**Status:** Draft
**PRD Reference:** `docs/PRD.md` v0.1
**Architecture Reference:** `docs/architecture.md` v0.2 (Sections 9.4, 9.5, 13, 15)
**UX Reference:** `docs/ux-spec.md` v0.1 (Sections 6, 8, 10, 11, 12)

**Precedence rule:** where the PRD and the UX spec disagree on anything a visitor or docent sees, the UX spec wins (architecture v0.2 header). This plan follows UX/architecture on: two held docent chords (CTRL+C=+F1 keeps scores, CTRL+C=+F7 clears), RUN/STOP and RESTORE disabled for everyone, 45 s idle warning / 60 s abandon, 1.5 s ghost hold with blinking ghosts (no READY text), missing-VDC error-and-stop.

**Confidence markers:** **[Unconfirmed]** = depends on a hardware fact nobody has verified yet (taken from the architecture's own [Unconfirmed] list). A test that depends on one says so, and the first run of that test is also the verification of the fact. **[Provisional]** = depends on a file I could not read (the tier demo READMEs, see Section 11).

---

## 1. Executive Summary

### 1.1 Test objectives
1. Show that the game is correct (rules, handoffs, timing) in VICE x128, cheaply and repeatably, on every change.
2. Show that it works on the **museum's real C128, real 1571, real monitors**. Per TR-3, a VICE pass is **not** acceptance. VICE VDC timing is not authoritative (R1).
3. Show that it survives unattended: 8-hour soak, 3 museum days, idle and stuck inputs, docent recovery.
4. Give a non-programmer (the maintainer on site, or a docent) a way to run the hardware tests and return evidence, without a programmer present.

### 1.2 Scope
**In scope:** the 8502 program (maze, pinball, attract, input, sound, VDC layer, watchdog), the VDCTEST diagnostic, the disk images and load procedure, the operating card, the tier 1-3 demo disks, controllers, both monitors.
**Out of scope:** arcade accuracy (non-goal), IP review (decided), two-player, C64 mode, PAL build (A4 says NTSC; PAL cases are listed in 4.9 as "only if a PAL variant is ever built").

### 1.3 Quality goals
| Metric | Target | Source |
|---|---|---|
| Lockups / garbage / corruption in soak | 0 in 8 h, then 0 in 3 museum days | S2, NFR-5 |
| Watchdog `fault_counter` after soak | 0 | Arch 5.2 |
| Load time from 1571 | < 60 s, target < 30 s | S3 |
| Flipper start latency | <= 1 frame (17 ms NTSC) | S5 |
| Maze->pinball GO! visible | <= 0.5 s | FR-4.2 |
| Ball auto-launch | <= 1.5 s from switch, no input | FR-3.2 |
| Stuck ball resolves | <= 40 s | FR-3.7 |
| Max pinball frame cost | <= 14,500 cycles (60 Hz) | V1 |
| Open P0/P1 defects at M4 exit | 0 | 8.3 |
| Visitor comprehension (hallway) | 4 of 5 within 30 s | S4 |
| Docent self-sufficiency | Load plus forced recovery unaided | S6 |

---

## 2. Test Strategy

### 2.1 Levels and where each runs
| Level | What | Where | Automation |
|---|---|---|---|
| L0 Build | `make`, `make check-repro` (identical bytes twice), charset <= 256 glyphs (V4), VDC map no overlap (V5), PRG ends <= $CFFF | Dev Mac | 100% (build fails) |
| L1 Unit (assembly) | Multiply tables, sin/cos, collision normals, flipper capsule cases | VICE, `UNITTEST` build | 100% |
| L2 Replay regression | Deterministic input replay, CRC16 of state at fixed frames (Section 3) | VICE x128 headless (`make test`) | 100% |
| L3 Visual | Screenshots of both VICE windows at fixed replay frames, compared by eye | VICE | Capture automated, judgment manual |
| L4 Accelerated soak | 8 h-equivalent attract in warp | VICE | Automated |
| L5 Hardware diagnostic | VDCTEST on the museum machine | Real C128 | Semi (run by a person) |
| L6 Hardware acceptance | Section 6 checklist, soak (Section 7), hallway test | Real C128 | Manual, scripted by form |
| L7 Field demo | Tier 1-3 disks (Section 11) | Real C128, tomorrow | Manual, one page |

### 2.2 What each environment can and cannot prove
| Claim | VICE | Real hardware |
|---|---|---|
| Game logic, rules, handoff order, timers | Authoritative | Spot check |
| Replay determinism | Authoritative | Not applicable |
| VDC write timing, busy-flag behavior, tearing | Provisional only | **Only here** |
| VDC corruption over time (R1/V6) | Cannot show | **Only here** |
| RGBI colors, overscan, ball roundness (V2, V3) | Cannot show | **Only here** |
| Paddle line mapping, joystick quirks | Emulated, optimistic | **Only here** |
| Keyboard chord ghosting, RESTORE behavior (UV8, UV10) | Partial | **Only here** |
| 1571 load time, device numbers, autoboot | Rough | **Only here** |
| Audio level and SID model | Not meaningful | **Only here** |

### 2.3 Risk-based priorities
In order: (1) dual display works at all and stays clean (A8, R1); (2) VDC throughput (R2/V1); (3) handoff correctness; (4) unattended recovery (idle, stuck ball, watchdog, chords); (5) controllers; (6) everything else. Test effort and early hardware time go in that order.

### 2.4 Test environment matrix
| ID | Environment | Purpose |
|---|---|---|
| E1 | VICE 3.10 x128, NTSC, 16K VDC, 1571 as drive 9 | Primary regression (matches A1 baseline) |
| E2 | VICE x128 NTSC, 64K VDC | Confirm the 16K map runs unchanged on a DCR-like config |
| E3 | VICE with true drive emulation on | Load-time estimate, `DLOAD ...,U9`, autoboot on device 8 |
| E4 | Museum C128 + 1571 + both monitors (**acceptance**) | Section 6, 7 |
| E5 | Any other real C128 (a second model if obtainable) | Model sensitivity (A1, R7). Optional, valuable |

Record on every hardware run: C128 model (flat / D / DCR; photo of the label), VDC RAM size from VDCTEST, SID model if known, monitor makes, cable types, disk label and build version, date, tester.

### 2.5 Test data
No user data exists. Test data is: replay files (`tests/replays/*.rpl`: seed + input stream), expected CRC logs (`tests/expected/*.crc`), and the default high-score table. Reset hardware state by power cycle (clears RAM scores).

---

## 3. VICE Regression via Deterministic Input Replay

Basis: ADR-007 (fixed-step simulation, integer math, frame-count timers, seeded 16-bit LFSR) and Arch 13.1. A `TEST` build reads controller and key-matrix state from a RAM table instead of CIA1; at listed frames the game writes CRC16 of each state struct to a RAM log; `tools/vice_harness.py` runs `x128 -warp`, reads the log via the binary monitor, and diffs against `tests/expected/*.crc`. The harness options (`-warp`, `-limitcycles`, `-console`, `-binarymonitor`, `-debugcart`) are [Unconfirmed]; fix this section when P0 captures `x128 -help`.

### 3.1 Rules for the harness
- R-1 A replay is (seed, frame-stamped input events, CRC checkpoints). No wall-clock input.
- R-2 Same replay twice in a row must give identical logs (flakiness check; run in CI as `make test-twice`). A mismatch is a **determinism bug** (uninitialized RAM, wall-clock use, VICE-timing dependence) and is a P1 defect, because attract mode depends on it.
- R-3 Expected CRCs are regenerated only by a deliberate `make rebless`, reviewed in the diff, with the reason in the commit message. A rule change (for example FR-4.5 energizer cap) legitimately changes CRCs; an unexplained change is a regression.
- R-4 Every defect found by a human gets a replay that reproduces it before it is fixed ("bug becomes a test").
- R-5 The attract-mode demo input stream is itself a replay: it must reach a chute and the game must reach the pinball in the same frame every run (RP-01 doubles as the attract regression).
- R-6 Run on E1 and E2; CRCs must match between 16K and 64K VDC (the logic does not depend on VDC size).
- R-7 CRC checks cover game state, not the VDC picture. Picture checks are L3 and the hardware checklist.

### 3.2 Replay catalog
| ID | Replay | Checks (state CRC unless noted) | Req | Pri |
|---|---|---|---|---|
| RP-01 | Attract demo stream: start to first chute, pinball rally, drain, resume | Chute triggers at expected frame; pinball active; drain at expected frame; maze resumes | FR-6.2, 3.4, 3.5 | P0 |
| RP-02 | Chute -> pinball -> drain -> resume | Maze frozen exactly (CRC of maze state equal before/after pinball except awards); chutes closed after return; Pac-Man at chute exit facing up | FR-4.1, 4.4, 2.4 | P0 |
| RP-03 | Entering a **closed** chute | Nothing happens; acts as wall | FR-2.4 | P0 |
| RP-04 | Handoff timing | GO! flag set <= 30 frames after chute entry; launch <= 90 frames after switch; asserts frame numbers, not just CRC | FR-4.2, 3.2 | P0 |
| RP-05 | Energizer awards 0, 1, 4, 5 targets | Placement order TL, TR, BL, BR; cap 4; extra converts to points | FR-4.5, UX 4.6 | P0 |
| RP-06 | Ghost hold after return | Ghosts do not move and do not kill for 90 frames, resume on frame 91; Pac-Man movable from frame 1; ghost frozen next to chute does not kill | FR-4.4 (UX C3) | P0 |
| RP-07 | Death with lives remaining; lives 3->2->1->0 | Chutes reopen on death; game over at 0; lives never lost on pinball drain | FR-2.6, 4.3, 2.4 | P0 |
| RP-08 | Board clear | Next board, chutes reopen, pinball tally/targets reset | FR-2.4 | P1 |
| RP-09 | Frozen timers | Energizer, fruit, ghost-mode timers do not advance during pinball (CRC of timers equal across a 20 s pinball visit) | FR-4.1 | P0 |
| RP-10 | Auto-launch variation | Different seeds give different launch velocities; same seed identical | FR-3.2 | P1 |
| RP-11 | Flipper input | Press at frame N: flipper angle step recorded at frame N (S5); hold keeps up; release drops in 3 frames; rise in 2 frames | FR-3.3, S5 | P0 |
| RP-12 | Ball never tunnels | Fuzz: 1,000 random launches x 2,000 frames with random flipper mashing; assert ball position always inside table and never inside a solid cell | FR-3.4 | P0 |
| RP-13 | Drain is the only exit | Same fuzz: the only exit event is `drain`; no other transition out of pinball | FR-3.5 | P0 |
| RP-14 | Stuck ball | Test table with a trap: nudge at frame 600 after last hit, 3 nudges, forced drain by about frame 2,400; total <= 40 s | FR-3.7 | P0 |
| RP-15 | Idle warning (maze) | No input: warning at frame 2,700, abandon at 3,600, back to attract | FR-6.5 | P0 |
| RP-16 | Idle warning (mid-pinball) | Same, ball in play; game ends at 3,600; no hang | FR-6.5 | P0 |
| RP-17 | Idle with qualifying score | Abandoned game inserts score with initials `???`; non-qualifying inserts nothing | UX 9.4 | P0 |
| RP-18 | Held (stuck) input is not activity | Fire held from frame 0 for 5,000 frames: `stuck` flag at frame 300, idle timer not reset, abandon at 3,600; stuck fire does not start a game from attract | UX 10.3, Arch 9.4 | P0 |
| RP-19 | Fresh press resets idle | Press edge at frame 2,800 clears warning | FR-6.5 | P1 |
| RP-20 | Game start edge rule | Fire held through game over does not restart; needs 18 frames released then a press | UX 9.2 | P1 |
| RP-21 | Initials entry | Up/down, fire, left-back; 20 s timeout restarts on input; timeout fills `?` | FR-6.4 | P1 |
| RP-22 | Score cap | Force score to 999,990, add points: caps at 999,999, no wrap, no lives bug | NFR-6 | P1 |
| RP-23 | Chord F1 (keep scores) | Matrix injected CTRL+C=+F1 for 120 frames: SOFT_RESTART with scores kept, lands in ATTRACT | FR-7.2, Arch 9.5 | P0 |
| RP-24 | Chord F7 (clear scores) | As RP-23 with scores reset to defaults | same | P0 |
| RP-25 | Chord early release | Released at frame 119: nothing happens, message clears | Arch 9.5 step 4 | P0 |
| RP-26 | Chord no double fire | Keys held 300 frames: exactly one restart; re-arms only after full release | Arch 9.5 step 6 | P0 |
| RP-27 | Chord blocked by controller | Chord keys plus a paddle line active: never fires; `chord_frames` stays 0 | Arch 9.5 step 1 | P0 |
| RP-28 | Chord during idle abandon | Abandon at 3,600 while chord held: chord still completes, one attract screen | Arch 9.5 | P1 |
| RP-29 | Chord is not activity | Chord held 40 s then released: idle timer not reset | Arch 9.4 | P1 |
| RP-30 | Partial chords | CTRL+C= only; F1+F7 together; CTRL+F1 only: none fire | Arch 9.5 step 3 | P1 |
| RP-31 | RESTORE / RUN/STOP | NMI injected 1,000 times in attract, maze, pinball: state CRC unchanged, no restart | UV10, ADR-005 | P0 |
| RP-32 | Watchdog | Test hook wedges main loop without kick: SOFT_RESTART within 125 frames, scores kept, `fault_counter` = 1 | Arch 5.2 | P0 |
| RP-33 | VDC fault boot | VDC status never ready (test hook): VIC shows `80-COLUMN SCREEN NOT RESPONDING`, no game, no restart loop | Arch 5.1, UX C9 | P0 |
| RP-34 | VDC fault mid-game | Ready flag stops after 30 s: SOFT_RESTART, then error screen | Arch 5.2 | P1 |
| RP-35 | Joystick fallback flippers | Pinball driven by joystick left/right only: both flippers act | FR-5.4 | P0 |
| RP-36 | Paddle-only start | Attract started by each paddle button and by joystick fire | FR-5.5 | P0 |
| RP-37 | Simultaneous L+R in maze | Last direction wins | UX 10.3 | P2 |
| RP-38 | Turn buffering | Direction pressed 7 frames before junction is taken; 9 frames before is not | FR-5.1 | P1 |
| RP-39 | Multi-hour state growth | 8 h-equivalent random-seed attract and play: stack pointer stable at frame boundary, zero-page and struct CRC cycle, `fault_counter` 0 | NFR-6 | P0 |
| RP-40 | Determinism (R-2) | Every replay above run twice | ADR-007 | P0 |

### 3.3 Unit tests (L1)
Quarter-square multiply table versus reference for all 8x8 pairs; sin/cos tables for the 4 flipper angles; collision normal table; flipper capsule: ball at tip, mid, pivot, moving and dead flipper; swept-angle placement; ghost target-tile selection (4 ghost rules, tie-break order); PRNG period and seed behavior; score BCD add and cap. Exit code through the debug cart register, else a result byte read via the monitor.

### 3.4 Accelerated soak in VICE (L4)
Attract plus scripted play (RP-01 repeated with varied seeds) in warp for the equivalent of 8 h of frames (1,728,000 frames NTSC). Pass: `fault_counter` = 0; stack pointer identical at every frame boundary checkpoint; no unexpected state-CRC divergence on repeated seeds; static VDC regions (font, panels) checksum unchanged via VDCTEST's peek routine. This catches software leaks only; it says nothing about hardware drift (that is Section 7).

### 3.5 Visual capture (L3)
Fixed-frame screenshots of both windows for: title, maze (chutes open), maze (chutes closed), maze paused palette, pinball live, pinball paused palette, GET READY, GO! flash, tally, idle warning, game over, initials, docent restart message, VDC error screen. Reviewed by eye against UX Sections 4, 6, 7 and the cue table (UX 6.2). Checks UX 12.3 "color is never the only signal": convert each screenshot to grayscale and confirm every state is still distinguishable by text or shape.

---

## 4. Test Cases (functional, by feature)

Format: ID, case, priority, how (A = replay/automated in VICE, H = hardware, M = manual in VICE). Full step detail for hardware cases is in Section 6; this section is the catalog.

### 4.1 Maze
| ID | Case | Pri | How |
|---|---|---|---|
| TC-M01 | 60 Hz maze, 5 sprites + fruit, no flicker (frame-step) | P0 | M, H |
| TC-M02 | Ghost colors distinguishable (red, light red, cyan, orange) on the museum monitor | P1 | H |
| TC-M03 | Pac-Man in a corridor with thin walls: 12 px sprite overhang does not hide wall lines (UV6) | P1 | M, H |
| TC-M04 | Tunnel wrap works both ways for Pac-Man and ghosts | P1 | A |
| TC-M05 | Open chute triggers handoff for both chutes (columns 5 and 34) | P0 | A (RP-02) |
| TC-M06 | Closed chute is a wall, drawn as red gate, text shown for 4 s | P0 | A, M |
| TC-M07 | Energizer behaviour: ghost eaten scores escalate; frightened blue; white flash near end | P1 | A, M |
| TC-M08 | Extra life at threshold | P2 | A |
| TC-M09 | Dot count: board clears only when all dots eaten | P1 | A |
| TC-M10 | Ghost AI sanity: no ghost enters a dead end or stalls for > 5 s over 10 boards of AI replay | P1 | A |

### 4.2 Pinball
| ID | Case | Pri | How |
|---|---|---|---|
| TC-P01 | Auto-launch from the mouth matching the chute used | P0 | A, M |
| TC-P02 | Flipper responds within 1 frame | P0 | A (RP-11), H (slow-motion video, 6.9) |
| TC-P03 | Left button = left flipper, right = right (paddle orientation) | P0 | H |
| TC-P04 | Each target class awards correctly: energizer targets, fruit lanes, bumpers, spinner, slingshots | P0 | A |
| TC-P05 | Tally panel matches awards, resets at next chute entry | P1 | A, M |
| TC-P06 | Ball white, wins color; no persistent wrong-colored cells after ball passes | P1 | M, H |
| TC-P07 | No torn ball cells over 5 min play (V1) | P0 | M, H |
| TC-P08 | Drain with ball at various speeds and angles: always returns to maze | P0 | A (RP-13) |
| TC-P09 | Drain width 3/4/5 playtest feel (tuning, not pass/fail) | P2 | M |
| TC-P10 | Flippers snap to rest at pause | P2 | M |
| TC-P11 | Ball cannot get trapped under or behind a flipper, in a bumper cluster, or on a slingshot at rest | P0 | A (RP-12/14), M |

### 4.3 Handoffs
| ID | Case | Pri | How |
|---|---|---|---|
| TC-H01 | Maze->pinball timeline per UX 8.1: maze dims at 0.1-0.25 s, GO! by 0.3 s, GET READY banner, launch at 1.3 s | P0 | A, H (video) |
| TC-H02 | Pinball->maze timeline per UX 8.2: OUT flash, tally, border flash, G O !, awards appear 0.15 s apart, ghost hold 1.5 s | P0 | A, H |
| TC-H03 | Frozen screen stays visible and stable (no blank, no garble) for 60 s while the other runs | P0 | H |
| TC-H04 | Paused cue text and direction correct on both screens | P0 | M, H |
| TC-H05 | 500 consecutive round trips in replay: no drift, no glyph or attribute leftovers (VDC static region checksum) | P0 | A |
| TC-H06 | Handoff while energizer active and fruit on screen: all timers resume at same remaining values | P0 | A (RP-09) |
| TC-H07 | Maze keeps input ignored during pinball and vice versa (joystick fire in pinball does nothing) | P1 | A |

### 4.4 Attract, start, game over, high scores
| ID | Case | Pri | How |
|---|---|---|---|
| TC-A01 | Boot goes straight to attract; labeled "DEMO", "PRESS FIRE TO PLAY" on both screens | P0 | M, H |
| TC-A02 | Attract loop (about 45 s) cycles all four segments with no corruption over 30 min | P0 | M, H |
| TC-A03 | Start from joystick fire, left paddle button, right paddle button, at every attract segment | P0 | A, H |
| TC-A04 | Game state does not leak from attract into the game (fresh maze, score 0, 3 lives) | P0 | A |
| TC-A05 | Game over screens, 3 s hold, then PRESS FIRE TO PLAY AGAIN, then attract after 8 s | P1 | M |
| TC-A06 | High score table: top 5, ordering, tie rule, default names, highlight on VDC | P1 | A |
| TC-A07 | Scores RAM-only: after power cycle, defaults return; no disk access during play (drive LED stays off, NFR-8) | P0 | H |
| TC-A08 | Score display identical on both screens | P2 | M |

### 4.5 Idle and stuck-input cases (hardware versions in 6.7)
| ID | Case | Expected | Pri |
|---|---|---|---|
| TC-I01 | No input 45 s in maze | `STILL THERE? PRESS A BUTTON nn` flashing 1 Hz on both screens, counting 15 to 1; game keeps running | P0 |
| TC-I02 | No input 60 s | Game ends, attract starts, no initials prompt | P0 |
| TC-I03 | Fresh input at 50 s | Warning clears, timer resets, game continues | P0 |
| TC-I04 | No input mid-pinball, ball in play | Warning appears, ball keeps moving; at 60 s attract (ball drain does not matter) | P0 |
| TC-I05 | Fire button taped down from attract | Never starts a game; `stuck` after 5 s | P0 |
| TC-I06 | Fire taped down **during** a game | Does not count as activity; abandon at 60 s | P0 |
| TC-I07 | Joystick held fully left/up (stuck contact) in maze | Pac-Man does what the direction says; idle still triggers | P0 |
| TC-I08 | Paddle button held (stuck) during pinball | Flipper stays up; ball may trap; idle abandon at 60 s; stuck-ball watchdog works | P0 |
| TC-I09 | Joystick left+right both held in pinball | Both flippers up, no crash | P2 |
| TC-I10 | Keyboard mashing (all keys, RUN/STOP, RESTORE, HELP, ESC, ALT, NO SCROLL, 40/80 DISPLAY) in attract, maze, pinball | Nothing changes; no crash; no restart | P0 |
| TC-I11 | Docent restart message appears when chord is held; cancels when released early | P0 | |
| TC-I12 | Idle abandon of a qualifying score | Stored as `???` on next high score view | P1 |
| TC-I13 | Stuck controller line blocks chord (Arch 9.5): chord ignored while a button is stuck | Documented behaviour; docent lets go of controllers first | P0 |
| TC-I14 | Stuck ball 10 s | Visible ball jump and tick; after 3 nudges drain, back to maze within 40 s | P0 |
| TC-I15 | Start edge: holding fire through GAME OVER does not auto-restart | P1 | |

### 4.6 Docent chord cases (hardware versions in 6.6)
| ID | Case | Expected | Pri |
|---|---|---|---|
| TC-D01 | CTRL+C=+F1 held 2 s in attract | `DOCENT RESTART IN 2...1...`, then attract; scores kept | P0 |
| TC-D02 | Same during maze play and during pinball (controllers released) | Same; game abandoned, back to attract, scores kept | P0 |
| TC-D03 | CTRL+C=+F7 held 2 s | Restart and scores reset to defaults | P0 |
| TC-D04 | Early release at 1.5 s | No restart | P0 |
| TC-D05 | Keys still held after restart | No second restart | P0 |
| TC-D06 | Chord attempted while holding the joystick fire / paddle button | Ignored (gate); this is the documented behaviour | P0 |
| TC-D07 | Ghosting: each of the 4 keys alone, each pair, each triple on the real keyboard | Only the two exact chords fire; no false trigger from pairs | P0 |
| TC-D08 | Paddle line aliasing: hold left paddle button, then right; check no half-chord display or restart | P0 | |
| TC-D09 | Both chords on both C128 keyboard types if more than one machine (flat vs D) | P1 | |
| TC-D10 | Chord when 40/80 DISPLAY key is in the other position | Still works (the key affects KERNAL screen output only) [Unconfirmed] | P2 |
| TC-D11 | Wrong chord (CTRL+C=+F3) | Nothing (unless U3 test pattern is adopted: then color bars, and this case changes) | P2 |

### 4.7 Controller fallback cases (hardware)
| ID | Case | Expected | Pri |
|---|---|---|---|
| TC-C01 | Normal: joystick port 2, paddles port 1 | Per FR-5.3 | P0 |
| TC-C02 | Paddles unplugged | Pinball playable with joystick left/right; no stuck-flipper, no crash | P0 |
| TC-C03 | Paddle plugged in port 2 and joystick in port 1 (swapped by a visitor) | Document actual behaviour. Expected [Unconfirmed]: maze unresponsive to stick, attract still starts via buttons only if lines map; game must not crash. If unplayable, card must say "do not swap ports" and the result is a Known Limitation | P1 |
| TC-C04 | Joystick unplugged | Paddle buttons start game; maze cannot be steered; idle abandon works; no crash | P1 |
| TC-C05 | Both controllers unplugged | Attract runs; no game start; no phantom input; no phantom idle activity | P0 |
| TC-C06 | Paddle X/Y orientation: which physical paddle is left flipper | Matches the card; if swapped, config constant flips it (rebuild) | P0 |
| TC-C07 | One dead paddle fire button | The other flipper works; joystick fallback covers the dead one | P1 |
| TC-C08 | Joystick with intermittent contact (wiggle the cable) | No restart, no hang, no spurious chord | P1 |
| TC-C09 | Hot-plug during power on | **Do not test on the museum machine** (can damage CIA); documented only. Plug and unplug with the computer off | - |
| TC-C10 | Optional A5 fallback: two arcade buttons on a DB9 | Same as paddles | P2, only if built |
| TC-C11 | Paddle knobs turned during play | No effect (pots not read) | P1 |
| TC-C12 | Port 1 input does not corrupt chord reading or keyboard (FR-5.7 / UV8) | See TC-D06, TC-D08 | P0 |

### 4.8 Missing-monitor and wrong-model cases
| ID | Case | Expected | Pri |
|---|---|---|---|
| TC-X01 | 80-column monitor **off**, cable connected | Game runs normally on VDC invisibly (software cannot tell). The center screen shows nothing wrong. **Record only.** Card must tell docent to check it | P0 record |
| TC-X02 | 80-column cable **disconnected** at the computer end | Same as TC-X01 | P0 record |
| TC-X03 | 80-col monitor connected on the **composite/mono** pin instead of RGBI | Monochrome VDC. Game readable via text and shape cues (NFR-11). Colors goal G1 not met; flag | P0 |
| TC-X04 | 40-column monitor off or on wrong input | VDC pinball visible; docent can see something is missing. Record | P1 |
| TC-X05 | VDC dead/unresponsive (E1 hook; on hardware only if a faulty unit is available) | `80-COLUMN SCREEN NOT RESPONDING - SEE OPERATING CARD` on VIC; stops; power-cycle recovers | P0 (VICE), P2 (hw) |
| TC-X06 | Monitors swapped in position (VDC monitor in the center) | Cue directions are wrong but game plays; build constant swaps arrows. Record | P1 |
| TC-X07 | **Wrong C128 variant**: DCR with 64K VDC; flat C128 with 16K | Both: VDCTEST reports size; game runs on the 16K map; 0 errors in soak | P0 |
| TC-X08 | Machine in 40-column mode on 40/80 key down at boot | Card states key position; verify card text; if the wrong position hides the BASIC prompt, the docent sees nothing. Verify what is shown while loading | P0 |
| TC-X09 | **C64 mode** (GO 64 / C64 key held at boot) | Program not run; document. If the load command is typed in C64 mode, document what happens | P1 |
| TC-X10 | **PAL machine** loading an NTSC disk | `PAL MACHINE: USE PAL DISK` error on both screens and stop (Arch 5.1 step 4) | P1 (VICE PAL config) |
| TC-X11 | BASIC start moved to $4001 by a `GRAPHIC` command before DLOAD | Program prints `POWER OFF, ON, AND LOAD AGAIN` and returns to BASIC (Arch 12.1) | P0 (VICE) |
| TC-X12 | Wrong load command (`LOAD` instead of `DLOAD`, device 8 default, misspelled name, `.PRG` suffix on a real disk) | Docent-level: record what the C128 prints and whether the card covers it (TR-5, R8) | P0 |
| TC-X13 | Disk write-protected, disk absent, drive off at load | Normal CBM errors. Card troubleshooting step must match. Write-protect must not affect running (NFR-8) | P1 |
| TC-X14 | Disk removed after load | Game continues (FR-7.3) | P0 |
| TC-X15 | Unknown SID model (6581 vs 8580): volume and filter-free sound acceptable | P1 | H |
| TC-X16 | No RAM expansion; machine with cartridge in expansion port | Record; unknown carts may conflict | P2 |

### 4.9 PAL (only if a PAL variant is built)
Repeat RP-15..RP-18 with PAL frame counts (2,250 / 3,000 frames), load time, flicker. Not in v1 gates.

### 4.10 Non-functional
| Area | Cases |
|---|---|
| Performance | V1 measurement: DEBUG HUD max cycles/frame over a 10 min pinball session ( <= 14,500 ); handoff latency <= 0.5 s by video; transitions finish in UX 8 timelines |
| Memory | `build/vdcmap.txt` and linker map checks; PRG ends <= $CFFF; no growth (RP-39) |
| Security | Visitor cannot exit to BASIC by any key sequence (TC-I10), cannot write disk (TC-A07), cannot reach any setting |
| Accessibility | UX 12.3 checklist: grayscale screenshot test; no flash faster than 2 Hz (count in video); no flashing area > 1/4 screen; text uses only light colors; fully playable muted; fully playable with joystick only (RP-35); text legible at 1.5 m on both monitors (NFR-12) |
| Audio | Every cue has a visual twin (UX 13); level acceptable on the floor (Q11); attract is quieter than play |
| Usability | Hallway test (Section 8) |
| Compatibility | Section 2.4 matrix; monitors: record make and model, color or mono |

---

## 5. Verification Items V1-V6: Pass Criteria

Owner column is the person who signs the item off. "Gate" is the first milestone where it must be closed. Passing in VICE alone never closes V1, V2, V3, V6.

| # | What | Method | Pass criteria | Evidence | Gate |
|---|---|---|---|---|---|
| **V1** Ball and flipper at 30-60 Hz without tearing | P2 primitive costs, P3 full-frame cost; frame-step in VICE; DEBUG HUD on hardware; 5 min play on hardware with a phone video at 60 fps or better | (a) Max pinball frame <= 14,500 cycles on the DEBUG HUD in VICE **and** on hardware (at 60 Hz), or the 30 Hz render fallback is selected and measured <= 29,000 per 2 frames. (b) The ball-colour model (UX D8: ball always white) is included in the measurement, because it adds about 840 cycles to the VDC budget (Arch 19.3). (c) No torn ball visible in 5 minutes of play on hardware. (d) Flipper first-motion frame = press frame (S5) | HUD photo, P2 results table `docs/notes/vdc-speed.md`, video clip | M1 measured in VICE; **hardware by M2, final M4** |
| **V2** Ball looks round on the museum 80-col monitor | DEBUG calibration screen: ball shapes 6x3, 6x4, 8x4 (and 10x4 per UX C6) plus a "square" box. Person on site photographs the screen from where a visitor stands | A shape is chosen by the project owners as "round"; `ASPECT_Y` and ball size constants set to match; the square box is visibly square (within judgment). Record the chosen values | Photo + chosen constants in the results form | M2 |
| **V3** Overscan safe area | DEBUG calibration screen with numbered ruler for columns 0-79 and rows 0-24 | All table columns 20-59 and all panel text columns 2-77, rows 1-23 visible with >= 2 columns margin. Record first and last visible column/row on both monitors (the VIC screen too: UX 4.1 asks for rows 0 and 24) | Photo of ruler, numbers on form | M2 |
| **V4** Glyph budget <= 2x256 (or 512) | Build check in `mkcharset.py` | Build passes with final table art, all flipper frames, 24 ball glyphs (3x2 ball), big font. Report counts per charset | CI log | M2 (art complete) and M3 |
| **V5** VDC map fits 16K | `build/vdcmap.txt`; run in VICE with 16K VDC; VDCTEST on hardware | No overlap or overflow reported by the tool; game plays correctly on E1; VDCTEST on the museum machine reports the VDC RAM size; the 16K map works regardless | `vdcmap.txt`, VDCTEST screen photo | M1 (VICE), M4 (hardware) |
| **V6** VDC write behavior, no corruption on the actual model | VDCTEST loop mode (CPU writes, plus block ops "for information") >= 2 h on the museum machine; then the 8 h game soak with DEBUG static-region checksum | 0 errors in CPU-write mode over >= 2 h. Block-op result recorded either way (game does not use them). 0 faults and static region checksum unchanged through the 8-hour soak | VDCTEST screen photos at start, hourly, end; soak log (Section 7) | **Hardware smoke at M1 if A12 holds (30 min minimum), full at M4** |

**Cross-checks** that ride along: UV1 (RGBI colour order against a color-bar), UV2 (attribute bits, blink rate), UV3 (VDC border colour), UV4 = V2, UV5 = V3, UV7 (recolor writes finish in 0.25 s), UV8 (chords/paddle aliasing), UV9 (40/80 key, reset button position), UV10 (RESTORE), UV11 (ball travel time vs paddles), UV12 (mono readability). Each is a line on the hardware checklist (Section 6).

---

## 6. Real-Hardware Checklist (for a person on site)

**Who this is for:** the maintainer, a docent, or any volunteer. No programming knowledge needed. You do not need to understand what each step proves. Do it, tick the box, write what you see, take the photo.

**How to use it:**
1. Print Section 6.10 (the results form). One copy per visit.
2. Work through 6.1 to 6.9 in order. Each step says **DO**, **EXPECT**, and **WRITE DOWN**.
3. If something does not match EXPECT, do not fix it. Write what you saw, take a photo or a short phone video, and carry on to the next step. The programmers will use your notes.
4. If anything smells hot, makes a popping noise or smokes: switch off at the wall and stop.
5. **Never plug or unplug a joystick, paddle, or monitor cable while the computer is on.** Switch the computer off first.

**Photo rule:** hold the phone steady, both screens in one shot if possible, then one close-up of each. Name each photo by its step number in your phone (e.g. "6.3-A.jpg"), or write the photo count on the form. Short videos: hold 10 seconds, start before you press.

**Photo naming:** `HW<step>-<letter>` e.g. HW6.3-A. Record the same name on the form.

**Equipment to bring** (tick on the form): C128 as installed, 1571, the BABY PAC-MAN disk(s) (release candidate + two spares), the VDCTEST disk (or the same disk, which carries VDCTEST), joystick and paddle pair, phone with camera, stopwatch (phone is fine), printed form and a pen, this checklist, the draft operating card, a small piece of tape, a flashlight (for reading the labels on the back).

### 6.1 Record the setup (10 min)
| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.1.1 | Photograph the back of the C128: the label with the model name/number, all cables | Label legible | Model text; photo HW6.1-A |
| 6.1.2 | Photograph both monitor fronts and their rear input labels/ports | Legible | Make, model; photo HW6.1-B |
| 6.1.3 | Look at the cable that goes to the left monitor. Is the plug a 9-pin RGBI (digital) plug, or a single yellow/RCA composite plug? | 9-pin | Which type |
| 6.1.4 | Look at the **40/80 DISPLAY** key on the keyboard (top row). Is it pressed in (down) or out (up)? | Note position | Up / Down (card says: ____ ) |
| 6.1.5 | Which controllers are present and where plugged? | Joystick port 2, paddles port 1 | What you see; photo HW6.1-C |
| 6.1.6 | Disk drive device number switch / label on the 1571 (rear) | 8 or 9 | Number; photo |
| 6.1.7 | Find the reset button on the C128 (small button, often on the side or underneath) | Found or not | Where; photo (needed for card, UV9) |

### 6.2 Load test (V3 loading, S3)
Start from fully powered off. Both monitors on, drive on, disk in the drive.

| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.2.1 | Switch the computer on. | BASIC banner appears on the screen the 40/80 key selects. | Which screen shows it; photo HW6.2-A |
| 6.2.2 | Type exactly the load command from the draft card, then RETURN. Start the stopwatch at RETURN. | Drive light on, disk reads | The exact text typed |
| 6.2.3 | When `READY.` appears, stop the stopwatch. | Under 60 s (target under 30 s) | Seconds |
| 6.2.4 | Type `RUN` + RETURN. Start the stopwatch. | Both screens show the title/attract picture | Seconds from RUN to first picture |
| 6.2.5 | Look at both screens. | Left (80-col) screen shows the pinball table in **colour**. Centre screen shows the maze/title. No random characters on either. | Colour yes/no; garbage yes/no; photo HW6.2-B (both screens) |
| 6.2.6 | Is the drive light off? | Off after load | Yes/no |
| 6.2.7 | Eject the disk. Keep watching for 2 minutes. | Game keeps running | Yes/no (TC-X14) |
| 6.2.8 | Repeat 6.2.1-6.2.5 from power-off, **three** times in total. | Same each time | Times for all three loads |
| 6.2.9 | Try the wrong command on purpose once (without the U9, or with a typo). | Normal CBM error text | Exactly what it said; photo (TC-X12) |
| 6.2.10 | Optional: set the 1571 to device 8 (only if Q12 is agreed) and power on with the boot disk. | Autoboots into attract | Yes/no |

### 6.3 Look at the screens (V2, V3, UV1, UV12)
Load VDCTEST (or the DEBUG calibration build) following its README. [Provisional: exact screen names depend on the build.]

| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.3.1 | Run the **color bars** on the left (80-col) screen. | 16 distinct bars, none missing | Which colors look wrong or identical; photo HW6.3-A |
| 6.3.2 | Run the **ruler** screen. Read the first and last numbers you can see at the left and right edges, top and bottom. | All of columns 2-77 visible | First/last visible column, first/last row, both monitors; photo HW6.3-B |
| 6.3.3 | Look at the **ball shapes** screen from where a visitor stands (about 1 m away). Which of the shapes looks most like a round ball? | One looks round | The shape number; photo HW6.3-C from standing position |
| 6.3.4 | Look at the square box. Is it a square? | Roughly | Yes/tall/wide |
| 6.3.5 | Is the text easy to read from about 1.5 m? | Yes | Yes/no; which text is hard |
| 6.3.6 | Look at the centre (VIC) screen: any colors missing, picture blurry, picture shifted off the edges? | Clean | Notes; photo |
| 6.3.7 | Is there a visible border color on the left screen? | Probably none (UV3) | Description |

### 6.4 Dual-screen stability (A8, V6 smoke)
| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.4.1 | Leave attract mode running for 30 minutes. Photograph both screens every 10 minutes. | No flicker, tearing, garbage, colour changes, reboot | Time of any glitch and what it looked like; photos HW6.4-A..D |
| 6.4.2 | Run VDCTEST in loop mode for at least 30 minutes now (2 h later on a full test). | `ERRORS 0` | Elapsed time; error count; photo |
| 6.4.3 | Press every key on the keyboard, including RUN/STOP, RESTORE, ESC, HELP, 40/80 DISPLAY, ALT, CAPS LOCK. | Nothing changes at all | Anything that changed (TC-I10, UV10) |
| 6.4.4 | Press RUN/STOP+RESTORE, 10 times. | Nothing changes | Result |
| 6.4.5 | With the 40/80 DISPLAY key, switch it up/down once. | Game does not care (record) | What happened |

### 6.5 Play test: the full loop
| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.5.1 | Press **joystick fire**. | Game starts: `READY!` over the maze about 2.5 s | Yes/no |
| 6.5.2 | Steer Pac-Man with the joystick. | Smooth, no flicker | Notes |
| 6.5.3 | Steer to a chute at the bottom left or right (marked with a yellow v). | Centre screen dims and shows `<< PINBALL IS ON THE LEFT SCREEN`. Left screen shows GO! and GET READY. | Seconds from chute to GO! (video if possible); photo HW6.5-A |
| 6.5.4 | Do not touch anything for 2 seconds. | The ball appears at the top and drops by itself | Seconds from switch to launch |
| 6.5.5 | Press the **left paddle button** and the **right paddle button**, one at a time. | Left button moves the left flipper, right moves the right | **Which button moves which flipper** (TC-P03, TC-C06); video HW6.5-B |
| 6.5.6 | Play the ball until it drains between the flippers. | Back to maze; "G O !" flashes; border flashes; ghosts blink about 1.5 s | Notes; photo HW6.5-C |
| 6.5.7 | Look at the chute you used. | Closed (red gate) | Yes/no |
| 6.5.8 | Repeat steps 6.5.3-6.5.7 five times in a row. | Same every time | Count of times anything differed |
| 6.5.9 | Let a ball drain while holding **both** paddle buttons down (do not release). | Still returns to the maze | Yes/no |
| 6.5.10 | Lose all 3 lives (let a ghost catch Pac-Man). | `GAME OVER`, then initials screen if it is a high score; use the joystick up/down and fire | Notes |
| 6.5.11 | Look at both screens in grayscale mode on the phone camera or just compare. | Every state also has words or shapes | Anything only readable by colour |

### 6.6 Docent chord test (UV8, TC-D01..D08)
Everything in this section: **let go of the joystick and paddles first.**

| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.6.1 | In attract mode, hold **CTRL + C= (Commodore key) + F1** together. | After about 2 s, `DOCENT RESTART IN 2...1...` counts down, then attract restarts | Seconds to restart; photo of message HW6.6-A |
| 6.6.2 | Before this, set a recognisable high score (initials "TST"). Repeat 6.6.1. | TST is **still** in the table | Yes/no |
| 6.6.3 | Hold **CTRL + C= + F7** for 2 s. | Restart and table back to default names | Yes/no |
| 6.6.4 | Start a game. Go into pinball. Let go of everything. Hold CTRL + C= + F1 for 2 s. | Restart to attract | Yes/no |
| 6.6.5 | Hold the chord for only 1 second, then release. | Nothing happens; message goes away | Yes/no |
| 6.6.6 | Hold the chord long after the restart (5 s). | Only one restart | Yes/no |
| 6.6.7 | Hold CTRL alone; C= alone; F1 alone; F7 alone; CTRL + F1; C= + F1; F1 + F7 together; each for 4 s. | Nothing happens | Any that did something |
| 6.6.8 | Hold the chord while someone holds the joystick fire button or a paddle button. | **Nothing** (this is by design) | Result |
| 6.6.9 | Hold the left paddle button for 5 seconds, then the right. Watch the screens. | No restart message, no strange behaviour | Result |
| 6.6.10 | Does the keyboard feel/respond the same in the middle of other keys (e.g. press SHIFT too)? | Does not matter; record if it fails | Notes |

### 6.7 Idle and stuck-input tests
Use a stopwatch. Both screens in view.

| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.7.1 | Start a game. Do not touch any controller. | At 45 s: `STILL THERE? PRESS A BUTTON nn` flashes on both screens, counting down from 15. At 60 s: attract | Time of warning; time of attract |
| 6.7.2 | Start a game, wait for the warning, press fire. | Warning vanishes, game continues | Yes/no |
| 6.7.3 | Start a game, go into pinball with the ball in play. Do not touch anything. | Warning at 45 s; attract at 60 s. No freeze | Times |
| 6.7.4 | In attract, tape the joystick fire button down (or hold it). Wait 90 s. | No game starts, or at most one start; the game must not keep restarting | What happened; photo |
| 6.7.5 | Start a game, then tape fire down. Wait 90 s. | Game still abandons at 60 s | Time |
| 6.7.6 | In pinball, keep one paddle button held (tape) and let the ball sit. Wait up to 90 s. | Ball resolved within 40 s or the game abandoned at 60 s; never frozen | Time; photo |
| 6.7.7 | Remove the tape. Press fire. | Normal | |
| 6.7.8 | Start a game and let the game get into a long pinball ball without drain (play well, 40 s+). | Keeps playing | Notes |

### 6.8 Controller fallback tests
Switch the computer **off** before each plug change.

| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.8.1 | Unplug the paddles (power off, replug nothing, power on, load). Start with joystick, play pinball with joystick left/right. | Flippers work | Yes/no |
| 6.8.2 | Swap: paddles in port 2, joystick in port 1. Load and try. | Record exactly what happens. Probably unplayable | What happened |
| 6.8.3 | Joystick unplugged: try starting with a paddle button. | Starts | Yes/no |
| 6.8.4 | No controllers: watch attract for 5 minutes. | Runs normally, no game starts | Yes/no |
| 6.8.5 | Joystick left and right pressed together in pinball. | Both flippers up, no crash | |
| 6.8.6 | Wiggle each controller cable while idle. | No game start or restart | |
| 6.8.7 | Turn each paddle knob fully. | No effect | |
| 6.8.8 | Return to normal plugging (joystick port 2, paddles port 1). | | Confirm on form |

### 6.9 Flipper speed, sound, power recovery
| Step | DO | EXPECT | WRITE DOWN |
|---|---|---|---|
| 6.9.1 | **Flipper latency (S5).** With a phone in slow-motion mode (240 fps if available), film the left screen and the fingertip pressing the paddle button together. Press 5 times. | Flipper starts moving within 1 frame of the click. Judge as "instant" | 5 clips, "instant / slight lag / obvious lag" |
| 6.9.2 | Listen to the sound at normal volume. Is it too loud or too quiet for the room? Does attract sound quieter than play? | | Notes |
| 6.9.3 | Switch the computer off at the power switch while in pinball. Wait 10 s. Switch on, load again. Time from "switch off" until attract is running. | Under 2 minutes (NFR-7) | Seconds |
| 6.9.4 | Press the reset button, then load again. | Back to BASIC, load works | Seconds; any difference |
| 6.9.5 | Run through the draft operating card word for word. Mark any step that is unclear or wrong. | Card works | Marked-up copy photographed |

### 6.10 Results form (print this page)

```
BABY PAC-MAN FOR C128 - HARDWARE TEST RESULTS            Form v0.1
Date: ____/____/______   Location: ___________________   Tester: ______________
Build/disk label (version/date): ______________   Disk copy: [ ] RC  [ ] spare 1  [ ] spare 2
Start time: ______  End time: ______

SETUP (6.1)
C128 model text: ___________________   [ ] flat  [ ] D (plastic)  [ ] DCR (metal)
VDC RAM size shown by VDCTEST: ______   SID: [ ] 6581 [ ] 8580 [ ] don't know
Left monitor (80-col): make/model ____________  Cable: [ ] 9-pin RGBI  [ ] RCA/composite
Centre monitor (40-col): make/model ____________  Cable: ____________
40/80 DISPLAY key at power on: [ ] up  [ ] down      1571 device number: ____
Reset button location: ______________________   Photos: HW6.1-A __ B __ C __

RESULT CODES: P = passed as expected   F = failed (describe)   S = skipped (why)   ? = unsure
-----------------------------------------------------------------------------------
STEP     RESULT   VALUE / WHAT YOU SAW                                   PHOTO / VIDEO
6.2.3    __       Load time (seconds): ______  ______  ______
6.2.4    __       RUN to picture (seconds): ______
6.2.5    __       Left screen colour? [ ]Y [ ]N  Garbage? [ ]Y [ ]N
6.2.7    __       Runs after disk removed? [ ]Y [ ]N
6.2.9    __       Text shown for wrong command: ______________________
6.3.1    __       Colours wrong/missing: ______________________________
6.3.2    __       Visible cols ____ to ____   rows ____ to ____   (left)
                  Visible cols ____ to ____   rows ____ to ____   (centre)
6.3.3    __       Round ball = shape no. ____    6.3.4 box: [ ]square [ ]tall [ ]wide
6.4.1    __       Any glitch (time, what): ______________________________
6.4.2    __       VDCTEST elapsed ______  errors ______
6.4.3-4  __       Keys that changed anything: ___________________________
6.5.3    __       Chute to GO! (s): ____   6.5.4 switch to launch (s): ____
6.5.5    __       Left button moves: [ ]left flipper [ ]right flipper [ ]none
                  Right button moves: [ ]left flipper [ ]right flipper [ ]none
6.5.6-8  __       Return to maze OK x5? [ ]Y [ ]N  Chute shut? [ ]Y [ ]N
6.5.9    __       Drain with buttons held OK? [ ]Y [ ]N
6.6.1    __       Restart after ___ s; score kept (6.6.2) [ ]Y [ ]N
6.6.3    __       Scores cleared with F7? [ ]Y [ ]N
6.6.5-6  __       Early release safe [ ]Y [ ]N   Single restart [ ]Y [ ]N
6.6.7    __       Partial chords that did something: ____________________
6.6.8-9  __       Chord blocked by held controller [ ]Y [ ]N  Paddles false trigger [ ]Y [ ]N
6.7.1    __       Warning at ____ s   Attract at ____ s
6.7.3    __       Pinball idle: warning ____ s   attract ____ s   Froze? [ ]Y [ ]N
6.7.4-6  __       Taped fire/paddle results: ____________________________
6.8.1    __       Joystick-only flippers work? [ ]Y [ ]N
6.8.2    __       Swapped ports behaviour: ______________________________
6.8.3-4  __       Paddle-only start [ ]Y [ ]N   No-controller attract [ ]Y [ ]N
6.9.1    __       Flipper lag: [ ]instant [ ]slight [ ]obvious
6.9.2    __       Sound: [ ]too loud [ ]ok [ ]too quiet     Attract quieter? [ ]Y [ ]N
6.9.3    __       Power-cycle to attract (s): ______   6.9.4 reset+reload (s): ______
6.9.5    __       Card steps wrong/unclear: _____________________________

ANYTHING ELSE ODD (screens, sounds, smells, heat, behaviour):
_______________________________________________________________________________
_______________________________________________________________________________

PHOTOS TAKEN (list names):  ____________________________________________________
Where files were sent (email/shared folder): ____________________________________
Signature: _____________     Reviewed by (developer): ________   Date: _______
```

---

## 7. The 8-Hour Soak Test (S2, NFR-5, V6)

### 7.1 Purpose and a decision to make first
Prove no lockup, garbage or corruption over a museum day (A9: about 8 h), and that VDC memory does not drift (V6). **A human cannot play pinball for 8 hours, and attract mode alone does not exercise the handoff code**, so the soak needs three parts. Part B needs a DEBUG/SOAK build feature (replay-driven autoplay) that the architecture has only as the `TEST` build; dev planning must decide whether `SOAK=1` is a supported release-candidate build option. If not, Parts A and C only, and the handoff stress is covered by TC-H05 in VICE. **Flag: this is a dependency on the Software Developer.**

| Part | What | Duration | Build |
|---|---|---|---|
| A. Attract-only | Attract loop with its built-in demo (includes a replayed chute handoff each 45 s loop) | 8 h continuous | **Release build** (the real thing) |
| B. Autoplay stress | Replay-driven games with varied seeds, including drains, deaths, idle abandon, stuck-ball | 2 h at start of Part A or separate | `SOAK=1` DEBUG build, if available |
| C. Human intermittent play | A person plays for 5 minutes at the top of each hour | During Part A | Release build |

Pre-requisite: V6 loop-mode VDCTEST >= 2 h with 0 errors on the same machine. Do that first on the same day.

### 7.2 Setup
- The exact museum configuration: same machine, drive, cables, monitors, desk, room (not the dev bench). Machine at room temperature (cold start) and left in place with normal ventilation. No fan blowing on it that the museum will not have.
- Brightness on both monitors at museum setting. Sound at the museum volume.
- Disk in drive or removed (record which; remove for the 3-day test since that is the plan).
- Phone on a stand, timelapse of both screens or a photo every 30 minutes (`HW7-xx` names).
- A log sheet (below). A volunteer checks and fills it at least hourly. If nobody can be present for 8 h, a timelapse video plus an overnight check is acceptable but the result is "unwitnessed" on the form, and a witnessed run is still required before M5 sign-off.
- Debug HUD is on in the DEBUG build only. For the release-build run (Part A), the check is by eye plus a final VDCTEST peek (7.5).

### 7.3 Procedure
1. Cold start. Record machine surface temperature by touch (warm/hot) and room temperature if a thermometer exists.
2. Load, `RUN`, note the time = T0.
3. Hourly (T0+1h ... +8h): look at both screens, photograph, play five minutes by hand (Part C): at least two chute round-trips, one drain, one deliberate game over, and each hour a different test of idle/abandon (alternate: let the game idle to abandon; hold CTRL+C=+F1; do nothing).
4. At T0+4h: one soft restart by the F1 chord, scores kept, all fine.
5. At T0+8h: stop, photograph, run the end-of-soak check (7.5).
6. Keep going if the machine and the volunteer allow, to 12 h; the extra hours are information.

### 7.4 Hourly log sheet
```
SOAK LOG   Date: ______  Tester: ______  Build: ______  T0 (load complete): ______
Hour  Clock   Left screen OK?  Centre screen OK?  Sound OK?  Played 5 min?  Notes / glitch / photo no.
1     ____    [ ]Y [ ]N        [ ]Y [ ]N          [ ]Y [ ]N   [ ]Y [ ]N      _________________
2 ... 8 (same)
Machine warm to touch? (hourly) ____  Any smell/noise? ____
Fault counter (DEBUG build HUD) at each hour: ____
```
**Glitch definition** (any one = record, photograph, note time): wrong or random characters on either screen; a flipper, ball or wall piece left behind; colour changes on part of a screen; either screen blank, rolling or shifted; sound stuck or silent; a restart (the title appears when nobody asked); the game does not respond to a button press; any "NOT RESPONDING" message.

### 7.5 End-of-soak checks
- VDCTEST (static-region checksum) or the DEBUG HUD: static VDC regions unchanged; fault counter 0; max frame cycles still <= budget.
- Force full redraw by the F1 chord: confirms that any "soft corruption" the eye could not catch would have been scrubbed; compare before/after photos for differences (any difference = latent corruption, record).
- Power cycle and cold-start again to confirm reload works after a long run.

### 7.6 Pass / fail
- **Pass:** 0 lockups, 0 glitches, `fault_counter` = 0, static-region checksum unchanged, all hourly checks done, 5-minute plays all normal.
- **Marginal:** 1-2 cosmetic glitches that vanish after the next restart (corruption scrub): classify P2 and root-cause before M5; rerun soak.
- **Fail:** any lockup, any restart not caused by the tester, any repeating corruption, any fault_counter > 0 (reason: the watchdog fired). Fix and rerun the full 8 h; do not "continue" the same run.
- Then S2 requires 3 consecutive museum days: daily docent log (Section 9.4): same 4 questions each day; pass = 3 clean days; the clock restarts after any fix.

---

## 8. Hallway Test (S4)

5 untutored people, mixed ages, not told anything. Observer notes: seconds to first fire press; whether they pick the right controller on the first switch to the pinball (joystick for maze, paddle or stick for pinball); seconds from screen switch to first correct flipper input; did they look at the right screen; did the `STILL THERE?` warning make sense; did anyone try the keyboard. Pass: >= 4 of 5 start a game and use the correct controller within 30 s of the first screen switch. Record the 3-second GET READY problem (UV11/U1): if 2 of 5 miss the first ball, raise U1 (extra first-visit grace) to the maintainer. Observer must not coach. Also record each person's age bracket and anything they said aloud.

---

## 9. Quality Gates by Milestone

Every gate has three parts: **must pass**, **evidence**, **who signs**. A gate is only closed when evidence is attached. "VICE only" means hardware evidence is explicitly deferred and listed as an open risk.

### 9.1 M1: Prototype both screens
| # | Must pass |
|---|---|
| G1.1 | `make` from a clean checkout produces PRG and `.d64`; `make check-repro` passes (P0) |
| G1.2 | Every Arch 3.2 [Unconfirmed] VICE flag corrected; `x128` boots with ROMs; `DLOAD "BABY PAC-MAN",U9` + `RUN` loads in VICE with drive 9 as a 1571; directory name exact |
| G1.3 | P1: both VICE windows animate together for 10 min with no corruption (a moving sprite on the VIC and a bouncing glyph-slot ball on the VDC) |
| G1.4 | Arch 17.1 facts closed or updated: MMU `$FF00`/`$3E`, VIC bank 1 custom charset visible, VDC R28, VDC attribute bit order, status bits |
| G1.5 | P2 results table for VICE 16K and 64K: cycles/op, busy rate; 6.3 budget confirmed or revised |
| G1.6 | P3: V1 measured in VICE (cycles/frame HUD), V4 counted, V5 map built |
| G1.7 | UV6 sprite-in-corridor, UV2 attribute bits, UV7 recolor timing measured in VICE |
| G1.8 | **Hardware smoke (if A12):** VDCTEST on the museum machine >= 30 min, 0 errors, model, VDC RAM, NTSC confirmed, write throughput recorded, dual display visible together (A8, Q5), and the form 6.1 completed. If A12 fails, record "R1/R2/R4 unretired" and schedule it |
| Evidence | CI log, `docs/notes/vdc-speed.md`, screenshots, hardware form if done |
| Sign | Software Developer + the maintainer |

### 9.2 M2: Pinball mock for the stakeholder
| # | Must pass |
|---|---|
| G2.1 | Table at full size with side panels, final-style colors, ball and flippers; playable demo (flip, bounce, drain) in VICE |
| G2.2 | V4 passes with final art; V5 passes |
| G2.3 | V1 at P3 level on the DEBUG build in VICE; **and** first hardware measurement if A12 |
| G2.4 | Redrawn maze (UX 4.4) shown; M2 screenshots/video include the ball clash (UX D8) and the paused/active looks |
| G2.5 | V2 and V3 closed on the museum monitor (photos from Section 6.3) **or** explicitly listed as open with date |
| G2.6 | RP-11, RP-12 (ball/flipper) green; L1 unit tests green |
| G2.7 | Rule questions Q13 (FR-2.2, 4.3, 4.4, 4.5) sent to the stakeholder with the mock; reference video watched (Q14) |
| G2.8 | S8 (first half): the stakeholder's reply recorded, requested changes logged as defects or change requests |
| Sign | the stakeholder (look and rules), the maintainer (quality) |

### 9.3 M3: Full game (release candidate disk image)
| # | Must pass |
|---|---|
| G3.1 | All replay cases RP-01..RP-40 green; determinism check (R-2) green twice in a row |
| G3.2 | All P0 and P1 cases in Section 4 marked "A" or "M" passed in VICE, evidence logged. FR acceptance criteria in PRD 3.2-3.5 checked off one by one |
| G3.3 | L4 accelerated soak (8 h-equivalent) passed: fault_counter 0, stack stable |
| G3.4 | Build is reproducible; V4, V5 pass; PRG <= $CFFF |
| G3.5 | Handoff timelines meet FR-4.2 (<= 30 frames to GO!) and FR-3.2 (<= 90 frames to launch) in the replay logs (RP-04) |
| G3.6 | Accessibility checklist (UX 12.3) pass in VICE: flash rate, grayscale distinction, text colors |
| G3.7 | Operating card draft exists and its commands match the built disk exactly (name, device, syntax). Disks (.d64, .d71, boot .d64) are produced |
| G3.8 | 0 open P0, 0 open P1; P2s listed; known limitations list started |
| G3.9 | Code coverage statement: not a number. Instead **requirement coverage**: every FR/NFR in PRD maps to at least one case (matrix in Section 12) |
| G3.10 | Tier 1-3 demo field results (Section 11) reviewed and their defects triaged into this gate |
| Sign | Software Developer (builds), QA (this plan), the maintainer |

### 9.4 M4: Real-hardware acceptance
| # | Must pass |
|---|---|
| G4.1 | **Hardware checklist Section 6 complete** on the museum machine with the release-candidate disk; every F resolved or accepted by the maintainer in writing |
| G4.2 | Load time S3 measured on 3 cold starts (< 60 s) |
| G4.3 | V1 (hardware part), V2, V3, V5 (hardware), V6 (VDCTEST >= 2 h, 0 errors) closed |
| G4.4 | S1: both screens in colour, observed and photographed (A3 is confirmed, or the maintainer accepts the mono outcome in writing) |
| G4.5 | S2: 8-hour soak passed (Section 7), then 3 consecutive museum days clean (docent log below) |
| G4.6 | S4: hallway test passed (Section 8) |
| G4.7 | S5: flipper responsiveness by slow-motion video, no "obvious lag" and a frame count recorded |
| G4.8 | All chord, idle, stuck, controller-fallback and missing-monitor cases (6.6, 6.7, 6.8, TC-X) executed on hardware with results recorded; P0 ones pass |
| G4.9 | the stakeholder's play-through done; S8 final approval (email reply) |
| G4.10 | 0 open P0/P1 defects; P2s have owner and decision; known limitations list complete |
| G4.11 | Reproducible retest: after any fix, the affected checklist sections re-run; soak re-run if the VDC layer, IRQ, input or main loop changed |
| Sign | the maintainer + the stakeholder (S8) |

**Docent daily log (3-day S2 test):** each day record: switched on at ____; screens OK at open? [ ]Y [ ]N; any restart by hand? [ ]Y [ ]N (how); anything odd? ____; switched off at ____. Pass = 3 consecutive days with no manual recovery needed and no unexplained restart.

### 9.5 M5: Handover
| # | Must pass |
|---|---|
| G5.1 | Museum owner named (Q9), backup docent named |
| G5.2 | Docent who has not seen the game loads it from the card alone, then recovers from a forced crash (S6). Observer times it and records every hesitation. Pass: load < 60 s; recovery < 2 minutes (NFR-7); no help given |
| G5.3 | Forced crash methods used: power switch; CTRL+C=+F1; also unplug a controller and replace it with the power off |
| G5.4 | Operating card final: every step tested by the docent; contains exact command, device, name, chords, "let go of controllers first", the `80-COLUMN SCREEN NOT RESPONDING` line, photo of reset button, contacts |
| G5.5 | 3 write-protected disks labelled with version and date, each loaded once successfully on the museum machine; images on USB/SD |
| G5.6 | Source archive handed over; a second person (not the maintainer) has built it from a clean checkout following the README (`make` works) |
| G5.7 | Known-limitations sheet delivered: colour clash, RAM-only scores, single player, any hardware-only issues |
| G5.8 | Owner confirms no open item depends on the maintainer (S7); support path in writing; any warranty period stated |
| G5.9 | Physical disk writing capability documented (Arch 12.4): who can make new copies |
| Sign | Museum owner |

---

## 10. Defect Management

### 10.1 Severity
| Severity | Definition | Examples | Response |
|---|---|---|---|
| P0 Critical | Exhibit down or data/hardware risk; no workaround without the maintainer | Lockup, load fails, restart loop, VDC corruption, keyboard escape to BASIC, disk write | Immediate; blocks any gate |
| P1 High | Core feature broken | Handoff fails, ball tunnels, drain missing, flipper wrong, chord does not work, idle never abandons | Fix before next gate; blocks M3/M4 |
| P2 Medium | Impaired, workaround exists | One glitchy animation, wrong cue text, colour clash worse than agreed | Tracked; owner and decision before M5 |
| P3 Low | Cosmetic | Typo, minor timing | Backlog |

### 10.2 Bug report minimum
Build/disk version, environment (VICE config or hardware model), steps, expected, actual, photo or clip, replay file if reproducible (R-4), frequency. GitHub issue label `bug` plus severity `P0..P3`; hardware findings labelled `hw-only`.

---

## 11. "Tomorrow at the Museum": Field Test Sheet

**Date:** 2026-10-28.
**Superseded:** the one-page sheet that used to be here (written before the disks existed) is replaced by the standalone, printable **[`docs/museum-field-sheet.md`](museum-field-sheet.md)**. It was checked against `release/README-*.txt`, `docs/dev-notes.md` and the c1541 listings of the disks. Use that file at the museum. It uses the `art3-sound` disk first (VDCTEST, DUALDEMO, PINBALL, BABY PAC-MAN) with `art2-pinball`, `art-babypac`/`art-pinball` and the stable `tier1-diag`/`tier2-pinball`/`tier3-babypac` disks as fallbacks.

### 11.1 What to record, in order of value
1. **Exact on-screen words** for any error (photograph). 2. **Which screen** was wrong (left, centre, both) and **when** (at load, at start, after N minutes, at a particular action). 3. **Colour or black-and-white** on each screen. 4. **Model label** and monitor cable type. 5. **Times** (load, switch, launch). 6. Clips beat descriptions: a 10-second video of any glitch.

### 11.2 What each failure likely means
These are hypotheses to guide the first look, not diagnoses. Basis in brackets.

| What you see | Most likely meaning | Check / consequence |
|---|---|---|
| Load fails or `FILE NOT FOUND` | Wrong name typed (case, spaces, `.PRG` suffix on a real disk), wrong device number, SD drive vs 1571 confusion | TR-5, R8. Check the disk directory (`DIRECTORY U9`). Not a software bug |
| `?DEVICE NOT PRESENT` or drive light never comes on | Drive off, disk not seated, wrong device number switch | Hardware/operator |
| Loads but BASIC returns immediately / garbage after RUN | Disk loaded at the wrong address (BASIC start moved to $4001 by a prior `GRAPHIC`; the machine was not freshly powered) | Arch 12.1. Power off, on, load again. If the message says `POWER OFF, ON, AND LOAD AGAIN`, that is the designed behaviour |
| Left screen black, centre fine | 80-col monitor off / wrong input / cable; or the 40/80 key; or VDC not responding (if the centre shows the NOT RESPONDING text, this is the VDC check working) | Check cable and input first. If the cable is good and the text appears: VDC or model issue (V6, A1) |
| Left screen shows monochrome (green/amber/white) | Monitor on composite/mono input or composite-only monitor | A3/R6. G1 cannot be met in software; museum needs an RGBI monitor or adapter |
| Left screen has wrong colours (all one colour, colours swapped) | Monitor RGBI mode/switch, or VDC colour order differs from assumed | UV1. Photograph the colour bars |
| Left screen columns missing at the edges / text cut off | Overscan on the monitor | V3. Not a bug; layout margins adjust |
| Left screen wavy, shifted or unlocked | VDC timing/monitor sync (the program does not touch R0-R8) or cable | Try the monitor's H/V hold, other input; a monitor issue is likely |
| Left screen: random characters, specks, wrong tiles appearing over time | **VDC write corruption** (R1) or throughput trouble | This is the key finding. Photograph the time. Report model and VDC RAM size. High priority |
| Left screen: ball leaves trail, flickers or half-draws | VDC update too slow/torn (V1/R2) | Record how often. May force 30 Hz render fallback |
| Ball looks like a flat oval or a tall egg | Pixel aspect differs (V2) | Not a bug; constant to tune. Photo it |
| Ball falls through the flipper or leaves the table | Physics/tunnelling | P1 bug. Note where on the table |
| Ball stuck for a long time | Stuck-ball watchdog (10 s nudge, 40 s max) | Normal if it resolves; a bug if > 40 s |
| Left button moves the right flipper, or only one flipper works | Paddle orientation reversed (TC-C06), or a dead button | A build constant swaps them. Note which button/paddle |
| Neither paddle works but joystick works | Paddle line mapping wrong (FR-5.2, UV8) or paddles in the wrong port | Check port; if correct, a software mapping issue |
| Paddle press makes odd behaviour on the keyboard (strange key actions) | Port 1 aliasing with the keyboard (FR-5.7) | Record exactly |
| Centre screen garbled, blank or rolling while the left screen runs | 2 MHz / CPU-speed or VIC bank problem (R4, ADR-002) | High priority; photograph |
| Centre screen shows ROM characters instead of the game font | VIC bank / charset ROM shadow problem (Arch 4.4) | Report. Memory-map issue |
| Maze sprites flicker | Raster timing | Record when (only with pinball? always?) |
| Maze looks wrong after returning from pinball | Freeze/resume state bug | P1. Note the sequence |
| Centre screen does not dim on switch / left does not light | Handoff problem or paused-palette timing | Record seconds |
| Sound very loud or harsh | SID model differences (6581/8580) | Note volume setting; not a defect by itself |
| Machine restarts to the title by itself | Watchdog firing (a hang in the main loop) | Record when and what you were doing; this is the fault counter in action |
| Hard freeze, power cycle needed | IRQ itself dead (watchdog cannot recover, Arch 5.2) | P0. Record time and last action |
| Nothing changes when a key is pressed | Correct (keyboard is dead by design) | Not a bug |
| Reload after power off fails the 2nd time | Disk or drive problem, or write-protect/dirty disk | Try a spare copy |
| Works for 5 minutes then fails | Heat, VDC memory drift, or leak | Record time; try again after 10 min cool-down |

### 11.3 After the visit
Photograph the filled sheet and send it with all photos/clips; do not fix anything on site; if a disk misbehaves, mark it "failed" with tape and keep it untouched. Developer triages every F into a defect (Section 10) within a day.

---

## 12. Requirement Coverage Matrix (summary)

| Requirement | Cases |
|---|---|
| FR-1.1-1.3 screens/roles/cues | TC-H03, TC-H04, TC-A01, 6.5.3-6.5.6 |
| FR-2.x maze | TC-M01-M10, RP-02, 03, 05, 07, 08 |
| FR-3.x pinball | TC-P01-P11, RP-10..14 |
| FR-4.x handoff | TC-H01-H07, RP-02, 04, 06, 09 |
| FR-5.x controls | TC-C01-C12, RP-35, 36, 38, 6.8 |
| FR-6.x flow/attract/idle | TC-A01-A08, TC-I01-I15, RP-01, 15-21, 6.7 |
| FR-7.x operations | TC-A07, TC-D01-D11, RP-23-30, 6.6 |
| NFR-1..4 performance | V1, 6.9.1, RP-04, RP-11 |
| NFR-5..9 reliability | Section 7, RP-32, 39, TC-X05 |
| NFR-10..12 usability | Section 8, 6.3.5, 6.5.11, UX 12.3 |
| S1..S8 | 9.4, 9.5 |
| V1..V6 | Section 5 |
| TR-4..TR-7 delivery | 6.2, TC-X11..X14, G3.7, G5.5 |
| R1..R12 | R1: V6; R2: V1; R4: 6.5 stability, tier 3; R6: TC-X03; R8: TC-X12, G5.2; R10: TC-I14, RP-14/15 |

---

## 13. Roles and Schedule

| Role | Responsibility |
|---|---|
| Software Developer | Unit and replay tests, `make test`, DEBUG/SOAK builds, fix defects, supply README-TIER*.txt |
| QA (this plan) | Plan, replays catalog, gate decisions, hardware form |
| the maintainer or a docent on site | Section 6, 7 (witness), 11, photos |
| the stakeholder | M2 and M4 approvals, monitor/model answers |
| Museum owner | M5 sign-off, docent log |

Schedule: tied to milestones (no dates, Q8). Hardware time requested: **M1 30-min smoke; M2 1-h look/photo visit; M4 one full day (load tests + 2 h VDC loop + 8 h soak, can run concurrently) plus 3 museum days; M5 1 h.**

---

## 14. Risks to the Test Effort

| Risk | Impact | Mitigation |
|---|---|---|
| No real hardware until M4 (A12) | R1/R2/R4 found late | Tomorrow's tier disks are the first hardware data; request Q7 now; budget a fix cycle after M4 |
| VICE headless harness flags differ from assumed (`-limitcycles`, `-console`, `-debugcart`) | `make test` slower to build | P0 captures real flags; fallback: monitor-script based harness, screenshots |
| Determinism bug (uninitialized RAM, VICE timing) | Replay flakiness, attract mode varies | R-2 twice-run check, R-4 |
| Non-programmer cannot reproduce a hardware step | Missing evidence | Photo-first form, short steps, video |
| Soak cannot be witnessed 8 h | Unwitnessed result | Timelapse, hourly volunteer; M5 requires a witnessed run |
| Hot-plugging controllers | Hardware damage | Rule in 6 header; TC-C09 not tested |
| Chord keys or paddle lines alias on the real keyboard (UV8) | Docent cannot restart | TC-D06-D08 early, at M1 hardware if possible; fallback is the power switch (already on the card) |
| Hardware differs per model (flat vs D vs DCR) | Pass on one model only | E5 if a second machine is reachable; record model on every form |

---

## 15. Open Questions
- [ ] Is `SOAK=1` autoplay a supported build? (Section 7.1)
- [ ] Tier README contents (Section 11): confirm load commands, controls and success screens.
- [ ] Who writes physical disks for the 3 spares (Arch 12.4) and tomorrow's tier disks? (affects tomorrow's spare copy)
- [ ] Is the F3 docent test-pattern chord adopted (U3)? If yes, TC-D11 changes to a pass criterion.
- [ ] Is there a second C128 for E5?
- [ ] Architecture Section 18 still cites the old 28x25 maze layout; test cases follow UX 4.1 (38 x 21). Architecture should be corrected.
- [ ] PRD FR-4.4 "READY" wording and FR-5.6, FR-7.2 conflict with UX; this plan uses the UX versions (C1-C3).

---

## 16. Revision History
| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-10-27 | the maintainer DeMarco with AI assistance | Initial test plan from PRD v0.1, Architecture v0.2, UX v0.1 |
