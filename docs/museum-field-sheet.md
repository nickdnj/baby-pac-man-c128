# Baby Pac-Man on the real C128 - Museum Field Sheet (28 Oct 2026)

Print this. Tester: ____________  Helper: ____________  Time in: ____  Out: ____

**First: turn BOTH monitors' volume DOWN before the first run.** The new disk makes sound and nobody has heard it on a real machine yet. Turn it up slowly later.

## 0. Setup (5 min, computer OFF)

- Joystick in **port 2**. Paddles (the pair with fire buttons) in **port 1**. Plug and unplug only with the computer OFF.
- Drive is a **1571 set to device 9**. Disk in, label up.
- Power on: monitors, drive, then computer. For every new program, the cleanest start is **power off, wait 5 seconds, power on**.
- Take the setup photos now (section 4) and fill in the "Write down" boxes (section 5).

## 1. The disk and the order

Use the disk **art3-sound** (disk name on screen: "BABY PAC-MAN SND"). It holds four programs: VDCTEST, DUALDEMO, PINBALL, BABY PAC-MAN. Check it first:

    DIRECTORY U9

You should see 4 names. If the drive is on 8 instead, use `U8` everywhere below.

**Load each program the same way (type exactly, press RETURN after each line):**

| Step | Type | Then |
|---|---|---|
| 1. VDCTEST | `DLOAD "VDCTEST",U9` | `RUN` |
| 2. DUALDEMO | `DLOAD "DUALDEMO",U9` | `RUN` |
| 3. PINBALL | `DLOAD "PINBALL",U9` | `RUN` |
| 4. BABY PAC-MAN | `DLOAD "BABY PAC-MAN",U9` | `RUN` |

Start a stopwatch when you press RETURN on DLOAD and stop it when the program appears. Write the time down. BABY PAC-MAN is the biggest (114 blocks): give it up to a minute. Do not touch anything while the drive light is on.

**How to get out:**
- VDCTEST and DUALDEMO: hold RUN/STOP and tap RESTORE, or press reset.
- PINBALL and BABY PAC-MAN (and every game on every art or tier disk): **only the RESET button works.** RUN/STOP+RESTORE does nothing on purpose.
- After reset, power-cycle (off 5 s, on) before the next load if anything looked odd.

**If something fails, go down this list (same commands, different disk):**
1. `art2-pinball` (same game, no sound)
2. `art-babypac` (older art; BABY PAC-MAN + PINBALL) or `art-pinball` (PINBALL only)
3. Stable disks, plainest and safest: `tier3-babypac` (BABY PAC-MAN), `tier2-pinball` (PINBALL), `tier1-diag` (VDCTEST, DUALDEMO)

All disks use the same commands. The program names are always `VDCTEST`, `DUALDEMO`, `PINBALL`, `BABY PAC-MAN` (tier1-diag has only the first two; art-pinball and tier2-pinball have no BABY PAC-MAN).

## 2. What each screen should look like

Left monitor = 80-column (RGBI colour). Centre monitor = 40-column.

**VDCTEST** (let it run at least 10 minutes)
- Both screens show the same text report. Look for: video **NTSC**, "VDC RAM: **16K** or **64K**", speed numbers, 16 colour bars (the first, black, looks empty: that is right).
- A "ROUND" counter goes up about every 15 seconds. Border is **green** while OK, turns **red** at the first error.
- Bottom line green "ALL VDC CHECKS OK SO FAR" is good. Red "VDC RAM ERRORS SEEN" is bad: photograph it.
- Left screen bottom: 16 colour bars numbered 0-15 in order: black, dark grey, dark blue, light blue, dark green, light green, dark cyan, light cyan, dark red, light red, dark purple, light purple, dark yellow/brown, light yellow, light grey, white.

**DUALDEMO**
- Both screens in colour at once, a frame counter that keeps counting on both, a ball bouncing on each screen and changing colour. Centre screen bottom says "80-COL SCREEN SHOULD SHOW A 2ND BALL".
- Test the controls here: a word turns **white** while pressed. Push joystick (port 2) up/down/left/right and fire. Press each paddle button in turn (PADDLE-1, PADDLE-2) and note which physical paddle is PADDLE-1 (it is the LEFT flipper). Turning the paddle knobs should change the X/Y numbers (255 with nothing plugged in is normal).

**PINBALL**
- Left (80-col) screen: the pinball table with blue walls, bumpers, targets, yellow flippers and the "BABY PAC-MAN" sign. Score on the right.
- Centre (40-col) screen: text only: "THE PINBALL IS ON THE 80-COLUMN SCREEN", score, ball number, status (GET READY / BALL IN PLAY / DRAINED), and a performance line **PINBALL MAX / PEAK / SLOW FRAMES**.
- "GET READY" for 1 second, then the ball drops in by itself. It plays balls forever (no game over). A stuck ball is nudged and then drained automatically.

**BABY PAC-MAN**
- Title: maze on the centre screen with a "PRESS FIRE TO PLAY" prompt; table (dimmed) on the left screen. Press joystick FIRE (or a paddle button) to start. "READY!" then play (new disk plays a short fanfare).
- Steer Pac-Man, eat dots. The two gaps in the bottom wall with yellow arrows are **chutes**: steer Pac-Man down into one. The centre maze dims, the left table lights up, and the ball drops in. When the ball drains, the maze comes back with "GO!" and the chutes are shut for a while (red bars) - that is normal.
- 3 lives, then GAME OVER and back to the title. If nobody touches anything for 60 seconds the game ends by itself.

## 3. Controls

- **Joystick in port 2:** steers Pac-Man; FIRE starts a game.
- **Paddle buttons in port 1:** left paddle button = left flipper, right = right flipper. Either button also starts a game.
- **Fallback:** joystick LEFT / RIGHT also works the flippers (port 2; a joystick in port 1 works too).
- Nothing else to press. Keyboard does nothing during the game.

## 4. Photos to take (all in focus, no glare; phone video is welcome too)

1. **Setup:** the back of the C128 (model label and cables), the front of the machine (model name), both monitors side by side, the 1571, and the cable going to the 80-column monitor.
2. **VDCTEST:** BOTH screens, after at least 10 minutes if you can. Capture the whole report including "VDC RAM", the speed numbers, ROUND/PASS/FAIL and the colour bars.
3. **DUALDEMO:** both screens **while you hold the controls down**: one photo with the joystick pushed and fire pressed, one with a paddle button pressed.
4. **PINBALL:** after a few minutes of play, a clear photo of the 40-column screen showing **PINBALL MAX, PEAK and SLOW FRAMES**. Also a photo of the 80-column table.
5. **BABY PAC-MAN:** a photo with the game running on both monitors at the same time (maze centre, table left), once during the maze and once during a pinball visit.
6. Anything odd, at the moment it happens.

## 5. Write down

| Item | Answer |
|---|---|
| C128 model (C128, C128D, C128DCR? from label) | |
| VDC RAM (from VDCTEST) | 16K / 64K / unclear |
| NTSC or PAL | |
| Left monitor cable/input: RGBI (colour) or not? Does the left screen show colour? | |
| Load times: VDCTEST ___ DUALDEMO ___ PINBALL ___ BABY PAC-MAN ___ (seconds) | |
| PINBALL MAX ___ PEAK ___ SLOW FRAMES ___ (after ___ min) | |
| Which paddle is PADDLE-1 / left flipper? | |
| Flippers feel (instant / delayed), ball looks round? | |
| Exact words of any error message | |
| Anything odd (noise, flicker, colours, freezes) and when | |

## 6. If it goes wrong

| Symptom | Likely cause | Try | Tell Claude |
|---|---|---|---|
| `?FILE NOT FOUND` | Typo, wrong disk, wrong device | `DIRECTORY U9`; retype exactly, quotes included; try `U8` | What DIRECTORY showed |
| `?DEVICE NOT PRESENT`, drive light never on | Drive off or wrong device number | Check power and cable; try U8 | Message and drive switch setting |
| Load takes very long | Big file (BABY PAC-MAN is 114 blocks) | Wait up to a minute | The real load time |
| Stuck on "STARTING..." (VDCTEST/DUALDEMO) | 80-col chip not answering | Note the **border colour** (blue, cyan, purple, green) | The border colour and photo |
| "VDC NOT RESPONDING" / "NO REPLY" | 80-col chip problem | 40-col results are still valid | Photo; run VDCTEST |
| Left screen black or rolling, centre fine | Monitor input, cable, or not in RGBI mode | Check input switch and cable; power-cycle | Photo of centre screen; monitor model |
| Left screen not in colour | Monitor on wrong/composite input | Switch to RGBI/digital input | Monitor model, photo of colour bars |
| Left colours in the wrong order | RGBI palette different from expected | Do not change anything | Photo of the numbered bars (VDCTEST) |
| Left screen letters scrambled or wrong shapes | VDC memory/font problem | Run VDCTEST | Photo of both screens |
| VDC red border / FAIL above 0 | VDC RAM errors | Let it keep running | Photo incl. "LAST ERROR" line, run time |
| PINBALL: red/black flashing border, "80-COL CHIP (VDC) IS NOT RESPONDING" | VDC not answering | Run VDCTEST | Photo |
| Game screen: ball leaves trails or flickers badly | VDC too slow | Note SLOW FRAMES number | Photo of MAX/PEAK/SLOW FRAMES; if SLOW FRAMES climbs fast, drop to tier2-pinball |
| [LEFT]/[RIGHT] never light up on centre screen | Paddle buttons not reaching the computer | Use joystick left/right in port 2; check DUALDEMO | Photo of DUALDEMO with buttons pressed |
| Flippers swapped (left button moves right flipper) | Paddle order reversed (a one-line software change) | Just play on; do not rewire | Which button moves which flipper |
| Maze garbage, no sprites (BABY PAC-MAN) | VIC memory problem | Try tier3-babypac, then art-babypac | Photo; which disk |
| Entering a chute does nothing | Chutes are shut after a pinball visit (intended) | Lose a life or clear the board | What was on the bottom row |
| Handoff happens but left table stays dark | Handoff/VDC problem | Reset | Photo of both screens |
| Sound very loud, harsh, or none | New, never heard on real SID | Turn monitor volume down | What you heard, volume setting |
| Freeze: nothing moves anywhere | Hang | Photo, note what you were doing, press RESET, power-cycle | What was on both screens; time since start |
| Game restarts to title by itself | Idle timeout (60 s) or watchdog | Normal if nobody touched it | When and what you were doing |
| Works, then fails after several minutes | Heat or memory drift | Let it cool 10 min, retry | Time of first glitch |

## 7. Send back

This sheet (photographed, filled in) plus all photos and clips, to the maintainer the same day, who gives them to Claude. Nothing on these disks writes to the disk, so the disks are safe to reuse.
