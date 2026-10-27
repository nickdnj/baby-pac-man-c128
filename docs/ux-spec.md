# UX Design Specification: Baby Pac-Man for the Commodore 128

**Version:** 0.1 (draft, not reviewed)
**Last Updated:** 2026-10-27
**Author:** the maintainer DeMarco, with AI assistance (ux-design agent)
**Status:** Draft. Builds on PRD v0.1, whose assumptions A1-A14 are still unconfirmed by the stakeholder.
**PRD Reference:** `docs/PRD.md` (v0.1)
**Architecture Reference:** none yet. Every hardware statement here is marked, and the architecture team must verify the [Unconfirmed] ones.

**Confidence markers** (same convention as the PRD)
- **[Confirmed]**: stated by the project owners, or well-known and stable (for example the VIC-II palette).
- **[Unconfirmed]**: from memory. Verify in the C128 Programmer's Reference Guide, in VICE x128, or on the museum machine before building on it.
- **[Proposal]**: a UX decision made here. Nobody has approved it. the project owners may overrule it.

All wireframes are character-grid ASCII, one character per 8x8 cell. A stand-in character is used for graphics (legend under each wireframe). They show layout and intent, not final art. All screens are shown in their NTSC/4:3 form.

---

## 1. Executive Summary

### 1.1 Design vision
Two monitors, one game. The visitor sees a bright, moving screen and a dim, still one, and always knows which is which: the live screen is bright and has a flashing GO!, the frozen screen is dimmed and carries an arrow toward the live one. Everything a first-time visitor needs is written on the screens. Nobody needs a manual, a menu or a keyboard.

### 1.2 Key design decisions
| # | Decision | Choice | Rationale |
|---|---|---|---|
| D1 | How the inactive screen shows it is paused | Recolor to a dim palette (blue walls instead of light blue, dark gray dots, and so on), plus an arrow message in the bottom row pointing at the live monitor. Never blanked (FR-1.2). | Cheap (only color memory changes), keeps the frozen position readable, works on a mono monitor through the text cue (NFR-11). |
| D2 | How the active screen shows it is live | Bright palette, flashing "GO!" for 1 s, VIC border flashes white for the same second. | The VIC border is the only peripheral-vision cue the hardware allows (the VDC border probably shares the background color, 7.5). |
| D3 | Same HUD on both screens | Score, high score, lives and fruit appear on both screens. | A visitor looking at either screen sees the score. Only changed values are rewritten, so VDC cost is small. |
| D4 | Maze layout | Redrawn 38x21-cell maze, 4 rows of HUD and messages. Section 5. | Fits 40x25 with no scrolling. |
| D5 | Pinball table | 40x25-cell table in the middle of the 80x25 VDC screen, funneled sides, 7-cell flippers, 4-cell center drain. Section 7. | Fits (answers the stakeholder's question). The drain width is a tuning knob, 3 to 5 cells. |
| D6 | Where the ball enters | The ball emerges from the top mouth that matches the maze chute Pac-Man used, after the GET READY beat. | Reinforces cause and effect (UX-5) and gives the player 2+ s of ball travel to reach the paddles. |
| D7 | Big text on the VDC | Headlines use a 2-cells-wide x 1-cell-tall glyph pair. Body text uses a bold 1-cell font. | VDC cells are tall and narrow (about 1:2.4 on a 4:3 monitor), so a 2x1 pair is nearly square. [Unconfirmed: computed from 4:3.] |
| D8 | Ball vs. color limit | The ball is always white and always wins: any cell the ball touches is drawn white for that frame. | One foreground color per cell makes any other rule produce a wrong-colored ball. Side effect: walls and bumpers "flash" as the ball passes. |
| D9 | Joystick works the flippers | Hint text says "PADDLE BUTTONS (OR JOYSTICK LEFT/RIGHT)". | The visitor does not have to switch controllers in a hurry (FR-5.4). It is also the one-handed way to play (Section 12). |
| D10 | Keyboard lockout | Keyboard dead during attract and play, RUN/STOP and RESTORE disabled in software. Docent soft restart is a held three-key chord. | Visitors cannot break the exhibit. Section 11. |
| D11 | Unattended behavior | 45 s idle warning, 60 s abandon (FR-6.5). A held-down input does not count as activity. | Stuck or taped buttons cannot hold the game open forever. Section 12. |

### 1.3 Design principles
1. **Look here.** At any instant, exactly one screen is obviously "the live one".
2. **Say it in words and shapes, not color alone.** Every state has a text or shape cue (NFR-11).
3. **Forgiving.** Draining a ball costs nothing but time. A closed chute explains itself.
4. **Never trapped.** No state can last forever without either input or a timeout.
5. **Hardware honesty.** If the chip cannot do it in one cell, we design the art so it does not need to (Sections 4.3, 7.4).

---

## 2. Visitors and Docents (from the PRD)

No new personas. The design drives from the PRD's users (1.4):
- **Visitor:** walks up, no instructions read, 1-5 minute sessions, mixed ages. May be standing, may be a child. Has exactly one thing to learn: which screen is live, and which controller to use on it.
- **Docent:** non-programmer, loads the game by typing one command, needs a one-page card (Section 11).

Physical setup the UX relies on [Confirmed, brief]: VIC (40-column) monitor front and center, VDC (80-column) monitor on the left. The "pointing" arrows follow this (<< toward the left screen, >> toward the center). The direction is a build-time setting in case the monitors move (A2).

---

## 3. Screen Roles and Hardware Facts This Spec Relies On

| Fact | Status | Used for |
|---|---|---|
| VIC 40x25 text, 8x8 cells, one foreground color per cell from 16, one global background | [Confirmed] | Maze and HUD |
| VIC multicolor character mode: 4 colors per cell (two global, one background, one per-cell color limited to colors 0-7), but pixels are doubled in width | [Confirmed, well known] | Optional only. Not used in v1 wireframes. |
| VIC: 8 sprites, 24x21 pixels, individual color plus two shared colors in multicolor sprites | [Confirmed] | Pac-Man, 4 ghosts, fruit = 6 |
| VIC palette (0-15): black, white, red, cyan, purple, green, blue, yellow, orange, brown, light red, dark gray, medium gray, light green, light blue, light gray | [Confirmed] | Section 4.2 |
| VDC 80x25 text, 8x8 cells in the standard mode, per-cell foreground (16 RGBI colors) and **one global background** | [Unconfirmed, PRD 5.1] | Table and panels |
| VDC attribute bits per cell: foreground color, plus blink, underline, reverse and alternate-character-set flags | [Unconfirmed, memory] | Glyph budget, hardware blink, solid art |
| VDC RGBI palette order (0-15): black, dark gray, dark blue, light blue, dark green, light green, dark cyan, light cyan, dark red, light red, dark purple, light purple, dark yellow (shows as brown on many monitors), light yellow, light gray, white | [Unconfirmed, memory]. The order differs from the VIC's. | Section 7.3. Verify with a color-bar test on the real monitor. |
| VDC has no sprites | [Unconfirmed, PRD 5.1] | Ball and flippers drawn in software |
| VDC border color equals the global background color | [Unconfirmed, memory] | The VDC cannot signal "live" with its border |
| VDC hardware blink rate for the blink attribute | [Unconfirmed] | Used only if the rate is 2 Hz or slower |
| On a 4:3 monitor, an 8x8 VDC cell is physically about 1 wide : 2.4 tall; a 40x25 block is 2:3 | Computed. [Unconfirmed on the real monitor (V2)] | Ball and big-text shape |
| Paddle fire buttons read as the left/right lines of the control port | [Unconfirmed, PRD FR-5.2] | Controls |

---

## 4. The VIC Screen (40 columns, the maze, front and center)

### 4.1 Grid
Rows are numbered 0-24, columns 0-39.

| Rows | Content |
|---|---|
| 0 | HUD labels: `1UP`, `HIGH SCORE`, `LIVES`, `FRUIT` |
| 1 | HUD values |
| 2-22 | Maze (21 rows, columns 1-38). The bottom wall (row 22) holds the two chute mouths. |
| 23 | Chute arrow glyphs under the mouths. Otherwise empty. |
| 24 | Message row: cues, hints, GO!, game over, idle warning |

Safe area: nothing a visitor must read goes in column 0 or 39. The maze's tunnel mouths use columns 1 and 38. Columns 0 and 39 are left empty. Row 0 and row 24 text should be checked on the real monitor (some CRTs overscan) [Unconfirmed].

### 4.2 VIC palette (all 16 colors, with assignments)

| # | Color | Active use | Paused use |
|---|---|---|---|
| 0 | Black | Background, border (normal) | same |
| 1 | White | Labels, GO! text, border flash, energizers' blink phase, frightened ghosts' end-flash | labels stay |
| 2 | Red | Ghost "Blinky"; closed chute gate | frozen |
| 3 | Cyan | Ghost "Inky"; energizers | frozen |
| 4 | Purple | Not used | |
| 5 | Green | Fruit stems (sprite color) | |
| 6 | Blue | Frightened ghost body | **Maze walls (paused)** |
| 7 | Yellow | Pac-Man, lives icons, open-chute arrow, hint text | Pac-Man frozen yellow |
| 8 | Orange | Ghost "Clyde"; orange fruit | frozen |
| 9 | Brown | Not used | |
| 10 | Light red | Ghost "Pinky" (pink is approximated), paused-cue message text | message text |
| 11 | Dark gray | | **Dots (paused)**; border (paused) |
| 12 | Medium gray | Not used | |
| 13 | Light green | Not used | |
| 14 | Light blue | **Maze walls (active)** | |
| 15 | Light gray | **Dots (active)**; score digits | digits stay |

Notes:
- Walls are light blue when active and blue when paused. This differs from the PRD's plain "blue maze walls" (UX-2) because plain blue is dark on many monitors. The dimmer blue becomes the "paused" look [Proposal].
- Ghost "pink" and "orange" are approximations [Unconfirmed on the monitor, PRD UX-2].
- Ghost colors are used only for sprite bodies. Ghost eyes use the two shared multicolor sprite colors (white and blue) [Proposal for the art team].

### 4.3 How the maze art copes with the VIC's color limits
- **One color per 8x8 cell.** Walls, dots, text and energizers each occupy their own cells, so no cell needs two colors. A dot sits in a corridor cell (the cell holds only the dot). A wall cell holds only wall.
- **Everything with more than one color is a sprite.** Pac-Man, ghosts (body + eyes) and fruit (stem + body) are sprites, so they can overlap any cell without breaking its color. Fruit in the HUD is a single-color glyph per fruit; the in-maze fruit sprite is multicolor. 6 of 8 sprites are used (PRD 5.1).
- **Walls are thin line glyphs, 2 cells thick where the layout allows**, drawn so that the 12-pixel-wide Pac-Man/ghost sprites in an 8-pixel corridor overhang only the blank margin of the wall cell, not the wall line. This is the single biggest visual risk of the 1-cell-corridor maze. It must be checked in the M1 prototype [Unconfirmed]. Fallback: 8-pixel sprites (smaller, plainer) or a larger sprite overhang with solid-wall art.
- **Multicolor character mode** (four colors per cell, double-width pixels) could give two-tone walls. It is optional and not drawn here, because it limits the cell's own color to colors 0-7 and coarsens the pixels.
- The dim "paused" palette is a recolor of color RAM (about 1000 bytes, a few milliseconds) plus the border register. Sprite colors are not changed on pause.

### 4.4 VIC wireframe: maze, play state, chutes open
Legend: `#` wall, `.` dot, `-` ghost-house door, `=` (on row 12) tunnel mouth (wraps to the other side), `v` open chute, `B P I C` ghosts (Blinky, Pinky, Inky, Clyde) in the house, `@` Pac-Man at his start cell, `@@@` lives, `c s` fruit icons (cherry, strawberry). The four blank corner cells (rows 3 and 21, columns 2 and 37) are the energizer slots: empty at the start of a board, filled by pinball (FR-2.2).

```
    0         1         2         3         
    0123456789012345678901234567890123456789
 0   1UP         HIGH SCORE    LIVES  FRUIT 
 1     001250        020400    @@@    c s   
 2   ###################################### 
 3   # ................##................ # 
 4   #.#####.#####.###.##.###.#####.#####.# 
 5   #.#####.#####.###.##.###.#####.#####.# 
 6   #....##....##.....##.....##....##....# 
 7   #.##.##.##.######.##.######.##.##.##.# 
 8   #.##.##.##.######.##.######.##.##.##.# 
 9   #.##..............................##.# 
10   #.##.#####.##.####--####.##.#####.##.# 
11   #.##.#####.##.#   BP   #.##.#####.##.# 
12   =.......##....#   IC   #....##.......= 
13   #.#####.##.##.#        #.##.##.#####.# 
14   #.#####.##.##.##########.##.##.#####.# 
15   #.......##........@.........##.......# 
16   #.#####.##.##.###.##.###.##.##.#####.# 
17   #.#####.##.##.###.##.###.##.##.#####.# 
18   #....##....##.....##.....##....##....# 
19   #.##.##.#####.###.##.###.#####.##.##.# 
20   #.##.##.#####.###.##.###.#####.##.##.# 
21   # .................................. # 
22   ####v############################v#### 
23       v                            v     
24    JOYSTICK STEERS  -  TAKE A CHUTE (v)
```

This draft was generated and checked by script for these properties: left/right symmetric, every corridor intersection has at least 2 exits (no dead ends), every corridor is reachable from every other, and it contains 312 dots plus 4 energizer slots [computed from this draft only; the dot count is not an arcade figure]. The architecture team may treat the topology as a starting point. The wall art (thin lines versus filled blocks) is the art task.

Maze notes:
- **Grid:** corridors are 1 cell wide on a 3-cell pitch (1 corridor + 2 wall cells), with the horizontal pitch widening to 4 near the center for the ghost house. The tunnel is on row 12 (maze row 10), the wrap cells are the `=` at columns 1 and 38.
- **Ghost house:** rows 10-14, columns 15-24. Door at columns 19-20, row 10.
- **Pac-Man start and fruit position:** row 15, columns 19-20 (same cell for both, as in the arcade [Unconfirmed]).
- **Chutes:** the two bottom-wall mouths at columns 5 and 34 on row 22, with arrow glyphs in row 23.

### 4.5 Chute states (shape + color + text)

| State | Row 22 mouth | Row 23 | Row 24 message |
|---|---|---|---|
| Open | Gap in the wall, edges drawn as an inverted funnel | Yellow `v`, blinking at 2 Hz | `TAKE A CHUTE (v) FOR PINBALL` |
| Closed (after a pinball visit) | Wall cells with a red gate glyph (`=` bars), no gap | Empty | `CHUTES SHUT - CLEAR THE MAZE TO REOPEN` (shown for 4 s after returning, then a normal hint) |
| Reopening | Gate glyph animates open over 0.5 s | `v` appears | Normal hint |

Entering a closed chute does nothing (it is a wall; FR-2.4).

### 4.6 Energizer slots and awards (maze side)
- A slot is an empty cell at the start of a board. When an award arrives, the energizer glyph (light cyan, a larger dot, 2 Hz blink) appears in that slot as part of the return transition (Section 8.3).
- Award order: corner slots, filled in the order top-left, top-right, bottom-left, bottom-right; cap of 4 (FR-4.5). Extra awards convert to points; the pinball tally shows this as `+BONUS` (Section 6.2).
- Energizer glyph color: cyan on VIC, light cyan on VDC, in both places, so the two screens share one energizer look (UX-5) [Proposal; confirm at the M2 mock because Inky is also cyan].

---

## 5. The Redrawn Maze (summary of constraints and decisions)

| Item | Decision |
|---|---|
| Playfield | 38 columns x 21 rows of cells, centered in the 40-column screen |
| Why not the arcade maze | The arcade maze is about 28x31 tiles [Unconfirmed], taller than the 25 rows the VIC offers. v1 trades height for width. Flagged for the stakeholder at M2 (FR-2.7). |
| Chutes | Two, in the bottom wall, columns 5 and 34 (symmetric) |
| Tunnel | One, in the middle row, as in Pac-Man. Ghosts are not slowed in the tunnel in v1 unless rules say so (a gameplay decision for the dev plan). |
| Pac-Man chute re-entry | He reappears in the chute he entered, then moves up one cell automatically, facing up (FR-4.4). The gate closes behind him. |
| HUD rows | 2 at the top, 2 at the bottom. The trade for the HUD is the maze loses 4 rows. |
| Energizers | None at the start of a board. Four slots (FR-2.2). If the stakeholder says the arcade starts with energizers, slots become permanent energizers and the pinball awards points. |

---

## 6. Message Row and Cues (the paused / GO! system)

### 6.1 Message row (VIC row 24) priority
Highest priority wins; a lower message resumes when the higher one ends.
1. Transient (GO!, EXTRA LIFE!, GAME OVER, idle warning)
2. Paused cue
3. Contextual hint

### 6.2 Cue table

| Situation | VIC (row 24 and border) | VDC |
|---|---|---|
| Attract mode | `PRESS FIRE TO PLAY` blinking at 1 Hz, yellow | Same text in the right panel, bottom |
| Maze live, chutes open | Hint: `TAKE A CHUTE (v) FOR PINBALL`, yellow, steady. Border black. | Paused cue in panel (below) |
| Maze live, chutes closed | Hint: `CHUTES SHUT - CLEAR THE MAZE TO REOPEN`, yellow | Paused cue in panel |
| Maze just resumed | `G O !` white, flashing at 2 Hz for 1 s; border flashes white at 2 Hz for the same second. Ghosts blink white (see 8.3). | Right panel: `MAZE >>` replaced by the final tally while it lasts (0.5 s), then the paused cue |
| Maze paused (pinball live) | `<< PINBALL IS ON THE LEFT SCREEN` light red, steady. Border dark gray. Walls blue, dots dark gray. | Active |
| Pinball just started | | Left panel headline `GO!` in the 2x1 big font, white, flashing at 2 Hz for 1 s. `GET READY` banner over the center lane band (rows 14-15) for 1 s. |
| Pinball live | | Left panel hint (see 12.2). Flippers live. |
| Pinball paused (maze live) | Active | Walls dark blue, other art dimmed (7.4). Right panel, bottom: `MAZE ON CENTER SCREEN >>` |
| Idle warning | `STILL THERE? PRESS A BUTTON  nn` flashing at 1 Hz (nn counts 15 down to 1) | Same text, right panel, bottom |
| Game over | `GAME OVER` red, row 15 over the maze (dots stay), steady. Row 24: `PRESS FIRE TO PLAY AGAIN` after 3 s. | `GAME OVER` banner over the center lane band |
| High-score entry | Section 9.3 | Table plus the highlighted entry |

Pointing direction: the VIC is in the center and the VDC on the left, so the VIC cue points left (`<<`) and the VDC cue points right (`>>`). Both flip with the build-time monitor-layout setting.

### 6.3 Flash discipline (accessibility)
No element flashes faster than 2 Hz. No flashing area exceeds about a quarter of either screen. The board-clear wall flash is 2 flashes per second for 2 s [Proposal; the arcade flashes faster]. The VDC's hardware blink, if used, must be 2 Hz or slower; otherwise blinking is done in software by rewriting the attribute [Unconfirmed rate].

---

## 7. The VDC Screen (80 columns, the pinball)

### 7.1 Grid
80 columns x 25 rows.

| Columns | Content |
|---|---|
| 0-19 | Left panel: pinball status, this-ball tally, controller hint |
| 20-59 | Pinball table (40 columns x 25 rows) |
| 60-79 | Right panel: HUD (score, high, lives, fruit) and pause/idle cue |

**Safe area** (V3): critical text sits in columns 2-77 and rows 1-23. Rows 0 and 24 and columns 0-1 and 78-79 carry only decoration (the table's top wall and bottom base are inside the table block, so they are safe to lose). The table block itself, columns 20-59, is far from the edges.

### 7.2 VDC wireframe: pinball live
Legend: `|` `\` `/` `=` walls (light blue), `\v/` chute mouths at the top (the ball enters here), `|` `f` fruit lanes at the top, `/==\ \==/` pop bumpers, `(O)` energizer targets, `<~~>` spinner, `|S\` slingshots, `O===` flippers shown at rest (pivot `O`), `#` solid base, `vvvv` the center drain, `@@@` lives, `%%` fruit icons.

```
    0         1         2         3         4         5         6         7         
    01234567890123456789012345678901234567890123456789012345678901234567890123456789
 0                      ============ BABY PAC-MAN ==============                    
 1    PINBALL           |    \v/                        \v/    |  1UP               
 2                      |             |  |    |  |             |    001250          
 3    THIS BALL EARNS   |             |  |    |  |             |                    
 4                      |             f  f    f  f             |  HIGH SCORE        
 5    ENERGIZERS   0    |         /==\            /==\         |    020400          
 6    FRUIT LVL   +0    |         \==/            \==/         |                    
 7    BONUS        0    |                                      |  LIVES  @@@        
 8                      |                 /==\                 |                    
 9                      |(O)              \==/              (O)|  FRUIT  %%         
10                      |                                      |                    
11                      |(O)                                (O)|                    
12                      |                 <~~>                 |                    
13                      |\                                    /|                    
14                        \                                  /                      
15    FLIPPERS =           \                                /                       
16    PADDLE BUTTONS        \       |\            /|       /                        
17    (OR JOYSTICK            \     |S\          /S|     /                          
18     LEFT / RIGHT)           \    |SS\        /SS|    /                           
19                              \                      /                            
20                               \                    /                             
21                                \O===          ===O/            MAZE IS PAUSED    
22                      ###############===    ===###############                    
23                      #################|vvvv|#################                    
24                      ################## OUT##################                    
```

(The lower-right text is the right panel's bottom cue: `MAZE IS PAUSED` while the pinball is live, `MAZE ON CENTER SCREEN >>` while the pinball is paused.)

Table metrics (table-local coordinates, columns 0-39, rows 0-24; add 20 for VDC columns):
- **Chute mouths:** columns 5-7 and 32-34, row 1. The left mouth is fed by the maze's left chute, the right mouth by the right chute.
- **Fruit lanes:** four rollovers at columns 14, 17, 22, 25 (rows 2-4). Each lit lane raises the next fruit's value one level.
- **Pop bumpers:** three, each 4 cells wide x 2 tall (nearly round at the VDC aspect): columns 10-13 and 26-29 on rows 5-6, and 18-21 on rows 8-9.
- **Energizer targets:** four `(O)` targets, 3 cells wide x 1 tall, on the side walls, columns 1-3 and 36-38, rows 9 and 11. Unlit = dark cyan outline; lit = light cyan, solid.
- **Spinner:** columns 18-21, row 12.
- **Funnel walls:** the playfield narrows from 38 cells wide at row 13 to 18 cells at row 21 over 8 rows, so the flipper pivots (columns 11 and 28) are close enough that 7-cell flippers leave only the drain gap. There are **no outlanes** (PRD FR-3.1): the funnel wall leads straight to the flipper.
- **Slingshots:** two triangles at columns 12-15 and 24-27, rows 16-18.
- **Flippers:** pivots at columns 11 and 28 on row 21, 7 cells long each. Section 7.5.
- **Drain:** a 4-cell gap at columns 18-21 on row 22, leading to a drain pit, rows 23-24 (`vvvv` / `OUT`). The gap is a tuning knob: 3, 4 or 5 cells, set at M2/M3 playtests. Wider is easier to lose on. 4 is the default [Proposal].
- **Top wall:** carries the title in row 0.
- **Table size answer for the stakeholder:** the table fits (PRD 6.4). The funnel changes one number: the PRD estimated a 3-cell drain gap with 6-7 cell flippers. With flippers at the table's side walls that is impossible (it would need flippers about 17 cells long), so the funnel brings the pivots in. See conflicts, Section 15.

### 7.3 VDC palette (all 16 RGBI colors, with assignments)
Index order per Section 3 [Unconfirmed; verify with a color-bar test].

| # | Color | Active use | Paused use |
|---|---|---|---|
| 0 | Black | Global background | same |
| 1 | Dark gray | Unlit fruit lanes' guides; base outline | Base |
| 2 | Dark blue | Solid base under the table | **Walls (paused)** |
| 3 | Light blue | **Walls and frame (active)** | |
| 4 | Dark green | Unlit fruit lane | Fruit lane |
| 5 | Light green | Lit fruit lane | |
| 6 | Dark cyan | Unlit energizer target outline | Targets |
| 7 | Light cyan | Lit energizer target; energizer icon (matches VIC cyan) | |
| 8 | Dark red | | **Slingshots (paused)** |
| 9 | Light red | Slingshots; cue text | |
| 10 | Dark purple | | **Bumpers (paused)** |
| 11 | Light purple | Pop bumpers | |
| 12 | Dark yellow (brown) | | **Flippers (paused)** |
| 13 | Light yellow | Flippers (Pac-Man yellow); panel headings | |
| 14 | Light gray | Spinner; panel body text | |
| 15 | White | **The ball**; GO! text | text stays |

The paused look is a per-element step down from a "light" color to its "dark" sibling. Text does not dim, so it stays readable.

### 7.4 How the table art copes with the VDC's color limits
1. **One global background.** Black, so the playfield lanes are simply empty black cells.
2. **One foreground color per cell.** Each table element is built from whole cells in one color. Two-tone objects are built from adjacent cells in different colors (a bumper: purple body cells, with a white ring cell if wanted). Details inside a cell cannot differ in color.
3. **Reverse attribute for solid shapes with detail** [Unconfirmed attribute]. A reversed cell shows the glyph's pixels as black on a solid color block, so a solid-color shape can have black eyes or letters. Useful for side-panel ghost art. It adds no colors.
4. **Ball rule: the ball always wins.** The ball can touch up to 3 cells across by 2 down. The cells it touches are drawn white for that frame, including the pixels of any art in them. A ball passing a bumper makes the bumper flash white; that doubles as a hit flash. Where the ball rolls along a diagonal funnel wall, the diagonal cell flashes white as it passes. This is accepted [Proposal; visible in the M2 mock].
5. **Keep decorative color away from the lanes** (UX-4). Lanes are empty. The only colored art in the lanes' neighborhood is the elements themselves.
6. **Glyph budget** [Unconfirmed; V4]. The VDC has 256 glyphs, or 512 with the alternate character set. Rough allocation: 36 for the bold body font, 72 for the 2x1 big font (letters and digits, two glyphs each), about 90 for table art (walls, bumpers, targets, slings, spinner), about 80 for flipper states (2 flippers x 4 states x about 9 cells; the right flipper needs its own mirrored glyphs), about 24 working glyphs for the ball compositing. That is about 300, so the alternate set is required. Exceeding it means simplifying art, not dropping features.
7. **Ball rendering.** The ball is a bitmap composited into temporary glyphs each frame over whatever table art is in those cells. Size 8-10 pixels wide x 4 lines tall, to be fixed in the V2 hardware check. A round ball at the VDC's pixel aspect is wide and short: 10x4 appears round on a 4:3 monitor [computed, unconfirmed].
8. **Text.** Body text uses a bold font (strokes at least 2 pixels wide, because 1-pixel strokes are too thin at 640 pixels across). Headlines use the 2x1 big font. NFR-12 is met by cell height (about 0.3 inch on a 13-inch monitor), not width [computed, unconfirmed].

### 7.5 Flippers
- Length 7 cells, drawn in 3 or 4 pose states per flipper (rest, middle, up; optionally two middle frames).
- Wireframe of the left flipper (the right is the mirror):

```
 REST              MIDDLE            UP
 O===                 ===            (tip high)
     ===          O===                         ==
                                          ===
                                      O==
```
  (Cell rows: rest spans 2 rows, middle 2 rows, up 3 rows.)
- **Behavior:** button down: the flipper moves rest -> up in 2 frames (about 33 ms, completes within the S5 target of 1 frame to *start*). Button up: it drops up -> rest in 3 frames (about 50 ms). Holding keeps it up.
- **Which flipper is which:** left button -> left flipper, right button -> right flipper. The pivots are `O`.
- **At pause** (ball drained) the flippers snap to rest so the frozen table looks calm.
- **Responsiveness:** the first pose change is drawn on the same frame as the button read. The architecture team confirms the VDC write budget supports this (R2).

### 7.6 Left and right panels
Left panel (columns 0-19):

| Rows | Content |
|---|---|
| 1 | `PINBALL` in the big 2x1 font, light yellow (14 cells wide, columns 2-15) |
| 3 | `THIS BALL EARNS` |
| 5 | `ENERGIZERS   0` (counts up as targets light) |
| 6 | `FRUIT LVL   +0` |
| 7 | `BONUS        0` |
| 10-13 | Flashing `GO!` (big font) for 1 s after the switch. Otherwise decorative art (Pac-Man and a ghost) |
| 15-18 | Controller hint (12.2): `FLIPPERS =` / `PADDLE BUTTONS` / `(OR JOYSTICK` / ` LEFT / RIGHT)` |

Right panel (columns 60-79):

| Rows | Content |
|---|---|
| 1-2 | `1UP`, score |
| 4-5 | `HIGH SCORE`, value |
| 7 | `LIVES`, icons |
| 9 | `FRUIT`, icons |
| 13-17 | Decorative art (ghost) |
| 21 | Bottom cue: `MAZE IS PAUSED` (pinball live) or `MAZE ON CENTER SCREEN >>` (pinball paused) or `PRESS FIRE TO PLAY` (attract) |

---

## 8. Transitions

Times are from the moment of the trigger. NTSC, 60 frames/s. Targets only; the architecture team measures the real VDC write cost (V1, R2).

### 8.1 Maze -> pinball (Pac-Man enters an open chute)

| Time | VIC (maze) | VDC (pinball) | Sound |
|---|---|---|---|
| 0 | Maze logic and timers freeze (Pac-Man, ghosts, energizer, fruit timers, ghost mode). Pac-Man's sprite hides (he went down the chute). Ghosts and fruit stay visible. | | Chute "whoosh" |
| 0 - 0.1 s | Row 24 shows `<< PINBALL IS ON THE LEFT SCREEN`. Border goes dark gray. | | |
| 0.1 - 0.25 s | Color RAM recolored to the paused palette. | Begin recolor of table attributes to the active palette (about 1000 attribute writes). Right panel cue changes to `MAZE IS PAUSED`. | |
| by 0.3 s | | `GO!` appears and flashes (2 Hz). `GET READY` banner appears in rows 14-15. Flippers are live. | Short ascending blip |
| 0.3 - 1.3 s | Frozen | Banner and GO! for 1 s | |
| 1.3 s | | Banner removed. The ball appears in the mouth matching the chute taken, and is kicked down and slightly inward, with a small random variation. | Launch "thunk" |
| 1.3 - about 3 s | | Ball travels down the upper table to the flippers. This is the player's time to reach the paddles. | |

- The requirement is "visible GO! on the VDC within 0.5 s" (FR-4.2) and "ball launches within 1.5 s with no input" (3.3). This timeline meets both: 0.3 s and 1.3 s.
- **Order matters:** the VIC is dimmed first (0.1 - 0.25 s), so the visitor's eye is released from the maze before the VDC lights up.
- A first-visit grace of about 3 s instead of 1 s is a candidate if the hallway test (S4) shows visitors cannot reach the paddles. It would break the 1.5 s acceptance criterion, so it needs a PRD decision. [Open question U1].

### 8.2 Pinball -> maze (ball drains)

| Time | VDC (pinball) | VIC (maze) | Sound |
|---|---|---|---|
| 0 | Ball leaves through the drain. `OUT` flashes in the drain pit. Pinball logic freezes, flippers snap to rest. | | Drain "gulp" |
| 0 - 0.1 s | Table recolors to paused palette. Right panel cue: `MAZE ON CENTER SCREEN >>`. | | |
| 0.1 - 0.6 s | The left-panel tally (`THIS BALL EARNS`) flashes once at 2 Hz and holds, showing the final energizers, fruit level and bonus. | | Award jingle, length scales with the awards |
| 0.6 s | | Border flashes white. Color RAM returns to the active palette (about 0.2 s). Row 24: `G O !` flashing for 1 s. Awards applied: energizers appear in their slots, fruit value is raised, bonus points are added to the score (HUD updates on both screens). | Maze music resumes |
| 0.6 - 0.85 s | | Pac-Man's sprite appears in the chute he entered and moves up one cell, facing up. The gate closes behind him. | |
| 0.6 - 2.1 s | | **Ghost hold:** 1.5 s. Ghosts do not move and cannot hurt Pac-Man. They blink between their body color and white at 2 Hz. Pac-Man is controllable immediately. | |
| 2.1 s | | Ghosts resume from their frozen positions (FR-4.4). Chutes stay closed. | |

The ghost blink is a shape/state cue that replaces the word "READY" (see conflicts, Section 15).

- Pac-Man being controllable during the hold is a [Proposal]. The PRD states only that ghosts hold (FR-4.4). If Pac-Man should also be held, the "READY" text and a stationary Pac-Man are the alternative (open question U2).
- The pinball stays frozen and visible with its tally until the next visit. At the next chute entry the table is reset: tally to 0, targets unlit, fruit lanes unlit (the transition in 8.1 includes this reset before GO!).

### 8.3 Energizer arrival (inside 8.2)
The slots fill one by one, 0.15 s apart, each with a short blip, so the visitor sees what the pinball earned. Maximum 4 slots, 0.6 s total.

### 8.4 Death and board clear (maze-only, for completeness)
- **Life lost:** Pac-Man animation, 1.5 s. Lives icon decrements. Chutes reopen (the gate raises over 0.5 s). Ghosts and Pac-Man return to start positions. If lives remain, a 1.5 s "GO!"-less pause then play. Nothing happens on the VDC.
- **Board clear:** walls flash white at 2 Hz for 2 s. Chutes reopen. Next board starts after the flash. Nothing happens on the VDC, except the table is reset.

---

## 9. Game Flow

### 9.1 Attract mode (the loop)

A loop of about 45 s; every segment is labeled so nobody mistakes it for a live game (project rule: no demo fallback). `PRESS FIRE TO PLAY` is on both screens at all times (Section 6.2). Any start input (joystick fire, or either paddle button) ends attract immediately.

| Segment | Length | VIC | VDC |
|---|---|---|---|
| A. Title | 8 s | Logo, ghost parade chasing Pac-Man across row 8 | Big title in the center band, table preview behind it |
| B. Maze demo | 15 s | AI-driven Pac-Man plays; row 24 flashes `DEMO` alternately with `PRESS FIRE TO PLAY` | Table at rest; right panel shows the high-score table |
| C. Chute demo | 10 s | AI Pac-Man takes a chute; same transition as 8.1 | AI plays a short pinball rally, then drains; transition back (8.2); `DEMO` label stays |
| D. How to play | 12 s | `JOYSTICK = MOVE PAC-MAN`, `TAKE A CHUTE (v) = PINBALL` | `PADDLE BUTTONS = FLIPPERS`, `BALL DRAINS = BACK TO MAZE` |

VIC title screen (segment A). The logo characters are the art task; a placeholder is shown.

```
    0         1         2         3         
    0123456789012345678901234567890123456789
 0   1UP         HIGH SCORE    LIVES  FRUIT 
 1     000000        020400                 
 2                                          
 3                                          
 4                                          
 5            B A B Y   P A C - M A N       
 6                                          
 7           for the  C O M M O D O R E  128
 8      @ <   B   P   I   C                 
 9                                          
10                                          
11          HIGH SCORES                     
12          1  AAA   020400                 
13          2  BBB   015200                 
14          3  CCC   009800                 
15                                          
16                                          
17                                          
18                                          
19            [CREDIT LINE - TBD with the stakeholder] 
20                                          
21                                          
22                                          
23                                          
24            PRESS FIRE TO PLAY            
```

- The credit line (who made it, whether it names the original) is for the project owners to write. Not drafted here.
- The default high-score names are "tribute names" (PRD FR-7.1), to be chosen by the maintainer.
- High scores are RAM-only. After a power cycle the default table returns.

VDC attract: the table drawn in the live (bright) palette but with no ball, left panel shows `BABY PAC-MAN` and the controller picture, right panel shows the high-score table in rows 4-12.

### 9.2 Start of game
1. Visitor presses fire (joystick) or either paddle button. A press must be a fresh edge: the button must have been released for at least 0.3 s first.
2. VIC: attract content clears. Score zero. `1UP` blinks. `READY!` in red over the maze below the ghost house (row 15, columns 17-22) for 2.5 s with the start jingle.
3. VDC: table reset, bright palette stays, right panel updates, left panel shows `GAME ON`.
4. Pac-Man appears at the start cell. Play begins. The first message is the chute hint.

### 9.3 Game over and high-score entry
- **Trigger:** last life lost in the maze (lives are lost only there, FR-4.3).
- **Game over:** `GAME OVER` (red) over the maze at row 15 and a banner over the table's center lane band on the VDC. Final score on both screens. Held for 3 s.
- **If the score is not on the table (high-score list of 5):** row 24 changes to `PRESS FIRE TO PLAY AGAIN` for 8 s, then attract.
- **If the score qualifies:** initials entry follows.

VIC initials entry:

```
    0         1         2         3         
    0123456789012345678901234567890123456789
10                                          
11           NEW HIGH SCORE!                
12                                          
13            000000 ... 028450             
14                                          
15            ENTER YOUR INITIALS           
16                                          
17                  [A] _ _                 
18                  ^                       
19                                          
20       JOYSTICK UP/DOWN = LETTER          
21       FIRE = OK    LEFT = BACK           
22                                          
23                                          
24                        15                
```

- Controls: joystick up/down cycles letters (A-Z, then a few symbols, wrapping). Fire accepts a letter and moves right. Left backs up one letter.
- Row 24 counts the 20 s timeout down (`20` .. `1`). It restarts on any input. On timeout: unfilled letters become `?`, the entry is stored, flow continues (FR-6.4).
- The VDC shows the high-score table with the new entry highlighted (light yellow) and a hint `LOOK AT THE CENTER SCREEN >>`.
- Entry runs on the VIC only because that is where the joystick the visitor is holding is used.
- After entry or timeout: high-score table for 6 s on both screens, then attract.

### 9.4 Abandoned game
At 60 s without a fresh input (Section 12.1) the game ends. If the score qualifies it is stored as `???`. No initials prompt. Attract starts.

---

## 10. Controls

### 10.1 Mapping

| Control | Port | Attract | Maze | Pinball |
|---|---|---|---|---|
| Joystick up/down/left/right | 2 | none | Steer Pac-Man (turns buffered, FR-5.1) | Left = left flipper, right = right flipper (fallback, FR-5.4). Up/down ignored. |
| Joystick fire | 2 | Start game | none | none |
| Paddle button, left paddle | 1 | Start game | none | Left flipper |
| Paddle button, right paddle | 1 | Start game | none | Right flipper |
| Paddle knobs | 1 | not read | not read | not read |
| Keyboard | - | ignored | ignored | ignored (docent chord excepted, Section 11) |

[Unconfirmed: that the paddle buttons read as the left/right lines of the port and that port 1 input can disturb the keyboard scan. Both are architecture items, FR-5.2 and FR-5.7.]

### 10.2 Handedness and physical flow
- The joystick and the paddle pair sit side by side on the desk. The visitor can leave the joystick in one hand and play both halves with it, using joystick left/right as the flippers. The paddles are for visitors who want the arcade-like two-button feel (the stakeholder's request, G3).
- The hint text says both (12.2).
- The pinball switch is the first moment of confusion. The ball needs about 1.7 s from launch to reach the flippers (1.3 s to launch plus travel; travel time is a physics output [Unconfirmed until built]).

### 10.3 Input hygiene
- **Edge detection:** actions use button presses, not levels, for starting a game.
- **Stuck input:** any input that stays unchanged for more than 5 s is treated as held, not activity (Section 12.1). A stuck fire button cannot restart attract into a game over and over.
- **Simultaneous left+right on the joystick** (physically possible on cheap sticks): in the maze, the last direction pressed wins. In pinball, both flippers rise, which is the normal two-flipper press.

---

## 11. Docent Experience

### 11.1 Key combo
The PRD suggests CTRL+SHIFT+F1, "to be defined" (FR-7.2).

**[Proposal] two chords**, both held for 2 s (a progress message appears, so a bumped key does nothing):
| Chord | Result |
|---|---|
| Hold **CTRL + C= + F1** | Docent soft restart: back to the title/attract. High scores are kept. |
| Hold **CTRL + C= + F7** | As above, and the high-score table is reset to the default names. |

- Both screens show `DOCENT RESTART IN 2...1...` as the chord is held. Releasing early cancels.
- **Why not one chord for both** (conflict with FR-7.2, Section 15): the soft restart is the common recovery and should not delete the day's high scores. Clearing scores is a deliberate separate act.
- The chords use only main-matrix keys. The C128's extra keys (HELP, ESC, TAB, ALT and so on) are scanned by a different register (via the VIC's extended keyboard register) and are avoided on purpose [Unconfirmed]. Whether a three-key chord works without matrix ghosting must be tested on the real keyboard, and the paddle button lines in port 1 must not be mistaken for keys while the chord is read [Unconfirmed, FR-5.7].
- The chord is written only on the operating card (Section 11.3).

### 11.2 Recovery ladder (for the card)
| Step | Action | When |
|---|---|---|
| 1 | Soft restart chord (11.1) | The game runs but looks wrong or is stuck on a screen |
| 2 | Power-cycle the computer, then load again | Nothing responds to the chord, or the screen is corrupt |
| 3 | Check cables and monitor inputs; use a spare disk | It does not load |
| 4 | Call the museum owner | Still broken |

- **The C128 RESET button is not part of the visitor-proof design.** The program disables RUN/STOP and RESTORE (D10), so those cannot be used by anyone. The reset button, if reachable, returns to BASIC and the game must be reloaded. Where it is on the case depends on the model [Unconfirmed]; the card shows a photo.
- **Self-recovery [Proposal, for architecture to confirm feasibility]:** a heartbeat watchdog. If the main loop does not report for 2 s, the raster interrupt (if still running) performs a soft restart to the title. If the interrupt itself is dead, only a power-cycle recovers it.
- **Chip-fault message:** if the VDC does not answer its status flag at start-up, the VIC screen shows `80-COLUMN SCREEN NOT RESPONDING - SEE OPERATING CARD` and stays there (no demo fallback; also not VIC-only play, since the chutes need the pinball). A missing monitor or cable cannot be detected from software, so the card's checklist covers it.
- **Optional (not in the PRD): docent test pattern** on a third chord (CTRL + C= + F3): color bars on both screens, plus the version number, to check monitor color, cable and input. It helps with the PRD's color risk (A3, R6) and helps a docent tell "monitor problem" from "game problem". Cheap to add. Decide at dev planning [Open question U3].

### 11.3 Operating card: draft content (one page, laminated)

> **BABY PAC-MAN (Commodore 128)** - Operating card, version [x.y], [date]
>
> **What it is:** a two-screen game. The center screen is the maze (joystick). The left screen is the pinball (paddle buttons, or joystick left/right).
>
> **Start the day**
> 1. Turn on both monitors and the disk drive.
> 2. Check the **40/80 DISPLAY key is [UP/DOWN - to be confirmed]** so the computer's own messages appear on the center screen [Unconfirmed].
> 3. Put the BABY PAC-MAN disk in the drive. Turn on the computer.
> 4. If it starts by itself (autoboot, if the drive is set to device 8): wait. Done.
> 5. Otherwise type **`DLOAD "[EXACT NAME]",U9`** and press RETURN. When it says READY, type **`RUN`** and press RETURN. [Exact name and syntax to verify on the delivered disk.]
> 6. Within 30 s both screens should show the title, then a demo. If not, go to "It won't start".
>
> **Controllers**
> - Joystick plugged into **port 2**. Paddles plugged into **port 1**. Leave both plugged in.
>
> **During the day**
> - Nothing to do. The game restarts itself after a visitor leaves (about 1 minute).
> - If a screen looks wrong or stuck: hold **CTRL + C= + F1** for 2 seconds. High scores stay.
> - To clear the high scores on purpose: hold **CTRL + C= + F7** for 2 seconds.
> - If nothing responds: turn the computer off, wait 10 seconds, turn on, and load again from step 3.
>
> **It won't start**
> - Is the disk fully in and the drive light ok? Try a spare disk (in the sleeve by the computer).
> - Is the drive set to the device number the card says? [9, or 8 if autoboot.]
> - Are both monitors on, and on the right input? The left screen needs the 80-column (RGBI) input.
> - If the left screen is black but the center works: check its cable. The center screen will show a message if the computer cannot find the 80-column display.
>
> **End of the day:** turn off the computer, then the monitors and drive. Return the disk to its sleeve.
>
> **Do not:** write to the disk, press RUN/STOP or RESTORE (they do nothing), or swap the controller ports.
>
> **Contact:** [Museum owner name, phone, email] - [backup docent]. Spares: [location]. Source and notes: [location].

Items in brackets are filled in at handover (M5). The 40/80 key statement is [Unconfirmed] and depends on the machine.

---

## 12. Accessibility and Unattended-Museum Behavior

### 12.1 Idle handling (FR-6.5, extended)
- **What counts as activity:** a joystick or paddle input that changed state. An input that has held the same state for more than 5 s is not activity (stuck switch, taped button, a leaning elbow).
- **At 45 s of no activity:** both screens show `STILL THERE? PRESS A BUTTON  nn` (message row on the VIC, right panel bottom on the VDC), flashing at 1 Hz, counting 15 down to 1. The game keeps running; a pinball ball is still in play.
- **At 60 s:** the game ends; attract starts (Section 9.4).
- **Any fresh input during the warning** clears it and resets the timer.
- **Attract mode itself never times out.** There is no screen saver in v1. [Open question U4: the monitors are probably CRTs and a static bright HUD for 8 hours can burn in. Attract mode keeps motion on both screens, and the table and the panels are not static for long. A dim-and-wait mode after a long idle is an option if the museum sees burn-in.]

### 12.2 Visitor-facing hints (copy)
| Where | Copy | Notes |
|---|---|---|
| VIC row 24 in the maze, chutes open | `TAKE A CHUTE (v) FOR PINBALL` | |
| VIC row 24, chutes closed | `CHUTES SHUT - CLEAR THE MAZE TO REOPEN` | 4 s after return, then back to a hint |
| VIC row 24, first 8 s of each game | `JOYSTICK STEERS PAC-MAN` | Then the chute hint |
| VIC row 24, maze paused | `<< PINBALL IS ON THE LEFT SCREEN` | |
| VDC left panel, rows 15-18 | `FLIPPERS =` / `PADDLE BUTTONS` / `(OR JOYSTICK` / ` LEFT / RIGHT)` | PRD NFR-10's "PADDLE BUTTONS = FLIPPERS" plus the joystick option |
| VDC left panel, GO! | `GO!` | 1 s |
| VDC right panel bottom | `MAZE IS PAUSED` or `MAZE ON CENTER SCREEN >>` | |
| Both screens, attract, how-to-play | 9.1, segment D | |

Language: short words, no jargon, no acronyms except the ones on the machine ("1UP"). Text in upper case, as the character set provides.

### 12.3 Accessibility checklist
- **Color is never the only signal** (NFR-11):
  | State | Color | Also shown by |
  |---|---|---|
  | Screen live vs. paused | brighter vs. dimmer palette | text cue, GO! flash, VIC border, arrow |
  | Chute open vs. closed | yellow arrow vs. red gate | arrow glyph present/absent, gap vs. bars, hint text |
  | Frightened ghost | blue body | shape: a frightened face, plus white flashing near the end |
  | Energizer slot filled | cyan | glyph present vs. empty cell, blink |
  | Fruit lane / target lit | brighter color | solid vs. outline glyph |
  | Ghost identity | four colors | ghosts differ only by color (as in the arcade); this is the one exception. Not a state signal, and ghost behavior is the same either way. |
- **Mono monitor:** the game still reads, because every state has a text or shape cue (NFR-11, A3). The VDC dimming cue is invisible on mono; the text cues and the flipper/ball shapes remain.
- **Contrast:** text uses only light colors: white, light gray, yellow, light cyan, light red (VIC and VDC). No dark blue, dark red or dark gray text. Dark colors are for art that is meant to recede (paused states). Contrast ratios are not computed for a CRT; they are judged on the real monitors at M4 [Unconfirmed].
- **Flicker and photosensitivity:** no flash above 2 Hz (6.3); no full-screen flash.
- **Sound:** every sound has a visual twin. The game is fully playable muted (the museum may mute it, Q11).
- **One-handed play:** the whole game, including pinball, is playable with the joystick alone (D9).
- **Reach and posture:** controllers should sit at the table edge within reach of a seated or standing user, and the monitor center should be at a seated eye height. This is the museum's setup and not software; one line goes on the card [Proposal].
- **Reading level:** every line a visitor must read is 5 words or fewer where possible.
- **Time pressure:** the only timed demand on a visitor is the 1.3 s GET READY plus the ball's travel before the paddles matter, then the ball may drain. A drained ball costs no life (FR-4.3).

### 12.4 No keyboard escape (summary)
- The program owns the keyboard from the first frame after RUN. RUN/STOP and RESTORE are disabled in software [Unconfirmed that the C128 can fully ignore them: architecture to confirm. Fallback: the program re-enters its own start on RESTORE].
- Only the docent chords (11.1) respond.
- The disk is never needed after load (FR-7.3). The program never writes to it (NFR-8).
- No setting is visitor-reachable (2.2 of the PRD).

### 12.5 Other unattended behavior
- **Stuck ball** (FR-3.7): 10 s without a hit starts a nudge sequence; the visitor sees a quick shake of the ball (a one-cell jump) and hears a "tick". After 3 nudges the ball counts as drained (about 40 s at most). Display: nothing to read.
- **Soft corruption scrub:** each time the game returns to attract mode the VDC screen and attribute memory are fully redrawn from the program's own copy, so any single stray write is wiped at least once per game [Proposal; supports R1/NFR-5].
- **Score overflow:** the score caps at 999,999 and stays there (NFR-6). The display never wraps.
- **Soak screen:** none. The 8-hour soak (S2) is observed by QA.

---

## 13. Sound Cues (brief, intent only)
SID. The PRD sets the scope (3.8 and Section 2); this lists what each cue does, not the music.

| Cue | When | Visual twin |
|---|---|---|
| Waka | Dots eaten | none |
| Chute whoosh | Maze -> pinball | row 24 text |
| Blip + launch thunk | GO!, ball launch | GO! flash |
| Bumper, target, flipper, spinner tones | Pinball events | white flash on hit |
| Drain gulp | Ball drains | `OUT` flash |
| Award jingle | Return, with tally | tally flash |
| Death, board clear, extra life, game over | Maze | per 8.4 |
| Idle warning tick | Last 5 s of the warning | counter |
| Volume | Moderate default, build-time setting (FR-7.4) | |

---

## 14. Things To Verify (each is a UX assumption on [Unconfirmed] hardware)

| # | Item | Why it matters to the UX | When |
|---|---|---|---|
| UV1 | VDC RGBI color order and how each color looks on the museum's monitor (dark yellow = brown?) | Sections 7.3 and 3 | M1, color-bar test |
| UV2 | VDC attribute bits: blink, reverse, alternate charset; blink rate | Glyph budget, hardware blink, solid shapes with detail | M1, VICE |
| UV3 | VDC border color is the background color | Section 6.2 (the VDC has no border cue) | M1 |
| UV4 | Real aspect ratio of the 80-column display; ball shape and size | Sections 7.2, 7.4 (V2) | M2, real monitor |
| UV5 | Overscan on both monitors | Safe areas, 4.1 and 7.1 (V3) | M2, real monitor |
| UV6 | 12-pixel sprites in 8-pixel corridors with thin walls | Section 4.3 | M1 prototype |
| UV7 | VIC color RAM recolor and VDC attribute rewrite (about 1000 bytes each) finish within the 0.3 s of the transition | Section 8 timelines | M1, measure |
| UV8 | Paddle fire lines, port 1 vs. keyboard scan, three-key chord ghosting | Sections 10 and 11 | M1, hardware |
| UV9 | 40/80 DISPLAY key behavior at boot; where the reset button is | Operating card | M1, hardware |
| UV10 | Disabling RUN/STOP and RESTORE fully | Section 12.4 | M1 |
| UV11 | Ball travel time from launch to flippers; whether visitors reach the paddles | Section 8.1 | M3 and the S4 hallway test |
| UV12 | Mono VDC readability | Section 12.3 | M4 |

---

## 15. Conflicts With The PRD (v0.1) and Deviations

| # | PRD text | This spec | Why | Needs |
|---|---|---|---|---|
| C1 | FR-5.6: "RUN/STOP+RESTORE and the reset button are the docent's hard recovery." | RUN/STOP and RESTORE are disabled for everyone. Hard recovery = power-cycle (or the reset button, then reload). | Anything a docent can press, a visitor can press. | PRD wording change; architecture feasibility (UV10) |
| C2 | FR-7.2: one chord returns to title **and** resets high scores | Two chords: restart keeps scores, a separate chord clears them | Restart is the common recovery and should not erase the day's scores | PRD decision |
| C3 | FR-4.4: ghosts hold still for 1.5 s ("READY") | Ghosts blink at 2 Hz and are harmless for 1.5 s; no "READY" text; Pac-Man is controllable at once | A text label over the maze would cover dots, and a visible blink is a shape cue (NFR-11) | the project owners (U2) |
| C4 | NFR-10 / 6.1: hint `PADDLE BUTTONS = FLIPPERS` | Adds `(OR JOYSTICK LEFT/RIGHT)` | Reduces the controller switch under time pressure (FR-5.4 already allows it) | PRD wording; the stakeholder may prefer paddles-only |
| C5 | 6.4: drain gap about 3 cells, flippers 6-7 cells | Default drain 4 cells (tunable 3-5), flippers 7, with funnel walls that bring the pivots to columns 11 and 28 | Flippers at the full table width would be about 17 cells long | PRD 6.4 update; playtest |
| C6 | 6.4: ball 6-8 pixels wide x 4 lines; pixels "about twice as tall as wide" | Ball 8-10 x 4; pixel aspect 2.0-2.4 | Arithmetic from 4:3; the PRD figure is a rounded one | V2 on the real monitor |
| C7 | UX-2: "blue maze walls" | Light blue active, blue paused | Plain blue is dark and weak on many monitors; the dimmer blue then serves as "paused" | the stakeholder, via the M2 mock |
| C8 | 3.3 / FR-3.2: ball "launches by itself after a 1 s GET READY beat" | Ball emerges from the chute mouth Pac-Man used, then is kicked down | Cause-and-effect continuity (UX-5); no plunger in the art | the stakeholder, via M2 mock |
| C9 | 6.5: "If the 80-column screen is unexpectedly absent, the game still runs" | A missing monitor can't be detected; a non-responding VDC chip shows an error and stops | The chutes need the pinball; a VIC-only game is a non-goal (1.3) | PRD wording |
| C10 | FR-1.3: "dimmed or flashing banner" | Both: dim palette and the message row | | none (satisfied) |
| C11 | FR-6.5: idle 60 s | 45 s warning and 60 s end; held inputs do not count as activity | Prevents stuck buttons keeping the game open | PRD addition |
| C12 | NFR-12 text legibility | VDC text legibility relies on cell height and a bold font | 1-pixel strokes are too thin at 640 px | Verify on hardware |

---

## 16. Open Questions

- [ ] **U1.** Give a first pinball visit of each game extra time (about 3 s) before the ball launches? It breaks the 1.5 s acceptance criterion. Decide after the hallway test (S4).
- [ ] **U2.** After a pinball return, is Pac-Man free to move during the 1.5 s ghost hold (this spec), or held with a "READY" label?
- [ ] **U3.** Include a docent color-bar and version test chord (not in the PRD)?
- [ ] **U4.** Is burn-in on the museum's monitors a concern? Do they want a screen-saver mode after long idle?
- [ ] **U5.** Which tribute names for the default high-score table, and what credit line on the title screen?
- [ ] **U6.** Energizer, fruit and bonus rules for the pinball targets. This spec gives only the display: 4 energizer targets, 4 fruit lanes, bumpers and a spinner for points (FR-3.6). The scoring and the number of energizers awarded per target are for the dev plan, checked against the reference video (Q13, Q14).
- [ ] **U7.** The cue text names "LEFT SCREEN" and "CENTER SCREEN". If the museum moves the monitors, the text and arrows change at build time. Confirm that this is acceptable instead of neutral wording.

---

## 17. Handoff Summary

- **To architecture:** every [Unconfirmed] row in Section 3 and the checks in Section 14; the VDC glyph budget (7.4 item 6); VDC attribute rewrite timing (UV7); keyboard and watchdog items (11.2, 12.4).
- **To dev planning:** the screen grids (4.1, 7.1), the transition timelines (8), the message and cue table (6.2), the game-flow screens (9), the controls table (10.1), the docent chords (11.1), the idle rules (12.1). Art tasks: wall glyphs, ghost/Pac-Man/fruit sprites, big font, flipper poses, table glyphs.
- **To QA:** the timelines in Section 8 are testable (GO! within 0.5 s, launch within 1.5 s, ghost hold 1.5 s); the cue table; the idle rules (45 s, 60 s, held input); stuck-ball; the accessibility checklist (12.3); the verification list (14).

---

## 18. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-10-27 | the maintainer DeMarco with AI assistance | Initial draft from PRD v0.1 |
