; maze.s - VIC maze engine (Tier 3, art pass)
; VIC bank 3: screen $C000, charset $C800 (256 glyphs: 0-63 our bold font,
; 64.. maze art, all from tools/mkmaze.py), sprites $E000 (pointers $80+).
; Pac-Man (hi-res) and 4 multicolour ghosts (MC0 white = eye whites, MC1
; blue = pupils) are 14-px shapes centred on the 8x8 cell grid; actors move
; 1 px per step. Sprites 5/6 = fruit (body + detail) or the GO! banner
; (6/7, expanded). Simple target-tile ghost AI.

.include "hw/c128.inc"
.include "hw/scr.inc"
.include "lib/macros.inc"
.include "maze_data.s"

.export mz_init_gfx, mz_new_game, mz_new_board, mz_reset_actors, mz_frame
.export mz_freeze, mz_resume, mz_set_chutes, mz_hud, mz_paint, mz_show_sprites
.export mz_hide_pac, mz_msg_clear, mz_death_anim, mz_flash_walls, mz_go_show
.export mz_sprites_off, mz_title_draw, mz_title_anim, mz_title_fade
.export mz_siren_off, mz_jingle_start, mz_jingle_tick
.exportzp mz_chute, mz_lives, mz_dotsleft, mz_hold, mz_hiscore
.export VSCR

.importzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.importzp num, tmp, frame, joy2, port1, pb_score, pb_fruit
.import scr_at, set_color, print, printi, putc, fmt_dec
.import row40lo, row40hi, pb_add_score, pb_sfx

VSCR    = $C000
VSPR    = $E000
VCHR    = $C800
SPRPTR  = VSCR + $3F8
SPRBASE = (VSPR - VSCR) / 64    ; $80
FR_X    = 19*8 + 21             ; fruit sprite position (Pac-Man's start cell)
FR_Y    = 15*8 + 47
FR_TIME = 570                   ; fruit stays 9.5 s
GO_X    = 156                   ; GO! banner (expanded) over the ghost house
GO_Y    = 136

T_OPEN  = 0
T_WALL  = 1
T_DOOR  = 2
T_CHUTE = 3
T_TUN   = 4

D_RIGHT = 0
D_LEFT  = 1
D_UP    = 2
D_DOWN  = 3

; events returned by mz_frame
EV_NONE  = 0
EV_CHUTE = 1
EV_DEATH = 2
EV_CLEAR = 3

.segment "ZEROPAGE"
ax_lo:      .res 5
ax_hi:      .res 5
ay:         .res 5
adir:       .res 5
gstate:     .res 5      ; ghosts: 0 in house, 1 active
grel:       .res 5      ; release countdown (frames/4)
want:       .res 1
mz_chute:   .res 1
mz_lives:   .res 1
mz_dotsleft: .res 2
.ifdef AUTOTOUR
tp:         .res 2      ; tour table pointer
tour_c:     .res 1      ; cell of the last tour step
tour_r:     .res 1
tour_done:  .res 1      ; 1 when the whole tour has been walked
tour_boards: .res 1     ; boards started (2 = the first one was cleared)
tour_wr:    .res 1      ; tunnel crossings
.endif
mz_hold:    .res 1      ; ghost hold frames after resume
mz_hiscore: .res 3
fright:     .res 2      ; frightened frames left
chutes_open: .res 1
mode_t:     .res 2      ; scatter/chase timer
chase:      .res 1
eatcount:   .res 1
mp:         .res 2
mi:         .res 1
rcnt:       .res 1      ; choose_random tries left
wantage:    .res 1      ; frames since a joystick direction was held
mcol:       .res 1
mrow:       .res 1
best:       .res 2
bestd:      .res 1
tgt_c:      .res 1
tgt_r:      .res 1
cand:       .res 1
mev:        .res 1
mtmp:       .res 2
awards:     .res 1

.segment "BSS"
dots:       .res 1000   ; 0 none, 1 dot, 2 energizer
gblue:      .res 5      ; ghost is frightened (cleared when eaten / at the end)
pmoved:     .res 1      ; Pac-Man moved this frame
pac_ph:     .res 1      ; chomp phase (advances only while moving)
fr_t:       .res 2      ; fruit frames left (0 = no fruit)
fr_shown:   .res 1      ; fruits shown this board (max 2)
fr_kind:    .res 1      ; fruit level 0-3 (cherry, strawberry, orange, apple)
mz_gob:     .res 1      ; GO! banner up (fruit waits)
chase_x:    .res 2      ; title chase: Pac-Man x + 100 (ghosts follow)
sir_on:     .res 1      ; siren (SID voice 2) running
sir_ph:     .res 1
jn_i:       .res 1      ; start jingle (SID voice 3): note index
jn_t:       .res 1      ; frames left on this note

.segment "CODE"

; ------------------------------------------------------------------------
; mz_init_gfx: VIC bank 3, our charset (256 glyphs) + sprites.
mz_init_gfx:
.ifdef AUTOTOUR
        lda #0                  ; zero page is not cleared at power-up
        sta tour_boards
        sta tour_done
        sta tour_wr
.endif
        ldx #0
:       lda vcharset,x
        sta VCHR,x
        lda vcharset+$100,x
        sta VCHR+$100,x
        lda vcharset+$200,x
        sta VCHR+$200,x
        lda vcharset+$300,x
        sta VCHR+$300,x
        lda vcharset+$400,x
        sta VCHR+$400,x
        lda vcharset+$500,x
        sta VCHR+$500,x
        lda vcharset+$600,x
        sta VCHR+$600,x
        lda vcharset+$700,x
        sta VCHR+$700,x
        inx
        bne :-
        ; sprites: NSPRITES*64 bytes, whole pages
        lda #<spr_data
        sta mtmp
        lda #>spr_data
        sta mtmp+1
        lda #<VSPR
        sta mp
        lda #>VSPR
        sta mp+1
        ldx #(NSPRITES*64+255)/256
        ldy #0
:       lda (mtmp),y
        sta (mp),y
        iny
        bne :-
        inc mtmp+1
        inc mp+1
        dex
        bne :-
        lda CIA2_PRA
        and #$FC                ; bank 3 ($C000)
        sta CIA2_PRA
        lda #$02                ; screen +$0000, charset +$0800
        sta VIC_MEMPTR
        lda #$1B
        sta VIC_CR1
        lda #$08
        sta VIC_CR2
        lda #0
        sta VIC_SPRXEXP
        sta VIC_SPRYEXP
        sta VIC_SPRPRI
        sta VIC_BG0
        sta VIC_BORDER
        sta mz_gob
        lda #$1E                ; ghosts are multicolour
        sta VIC_SPRMC
        lda #COL_WHITE
        sta VIC_SPRMC0
        lda #COL_BLUE
        sta VIC_SPRMC1
        lda #>VSCR
        sta vicscr
        rts

; ------------------------------------------------------------------------
mz_new_game:
        lda #3
        sta mz_lives
        lda #0
        sta fr_kind
        jsr mz_sprites_off      ; (the title used all eight sprites)
        lda #$1E                ; ghosts multicolour; Pac-Man, fruit, GO! hi-res
        sta VIC_SPRMC
        jsr mz_new_board
        rts

; mz_new_board: dots, screen, colours, chutes open
mz_new_board:
.ifdef AUTOTOUR
        lda #$FF
        sta tour_c
        sta tour_r
        lda tour_boards
        bne @t2
        lda #<tour_table        ; first board: eat every dot
        sta tp
        lda #>tour_table
        sta tp+1
        jmp @tb
@t2:    lda #<tour_table2       ; second board: the tunnel both ways
        sta tp
        lda #>tour_table2
        sta tp+1
@tb:    inc tour_boards
.endif
        ldx #0
:       lda mz_dots,x
        sta dots,x
        lda mz_dots+250,x
        sta dots+250,x
        lda mz_dots+500,x
        sta dots+500,x
        lda mz_dots+750,x
        sta dots+750,x
        inx
        cpx #250
        bne :-
        lda #<NDOTS
        sta mz_dotsleft
        lda #>NDOTS
        sta mz_dotsleft+1
        lda #0
        sta fr_shown
        jsr fruit_hide
        ; screen codes rows 2..23 from mz_codes
        ldx #0
:       lda mz_codes+80,x
        sta VSCR+80,x
        lda mz_codes+80+220,x
        sta VSCR+80+220,x
        lda mz_codes+80+440,x
        sta VSCR+80+440,x
        lda mz_codes+80+660,x
        sta VSCR+80+660,x
        inx
        cpx #220
        bne :-
        lda #1
        jsr mz_set_chutes
        lda #0
        jsr mz_paint
        rts

; mz_set_chutes: A = 1 open, 0 closed
mz_set_chutes:
        sta chutes_open
        ldx #CHUTE_L
        jsr chute_cell
        ldx #CHUTE_R
        jsr chute_cell
        rts
chute_cell:
        lda chutes_open
        beq @closed
        lda #$20
        sta VSCR+CHUTE_ROW*40,x
        lda #G_ARROW
        sta VSCR+(CHUTE_ROW+1)*40,x
        lda #COL_YELLOW
        sta COLRAM+(CHUTE_ROW+1)*40,x
        rts
@closed:
        lda #G_GATE
        sta VSCR+CHUTE_ROW*40,x
        lda #COL_RED
        sta COLRAM+CHUTE_ROW*40,x
        lda #$20
        sta VSCR+(CHUTE_ROW+1)*40,x
        rts

; mz_paint: colour RAM for rows 2-23 from the screen codes. A=1 paused look.
mz_paint:
        sta mtmp
        lda #<(VSCR+80)
        sta mp
        lda #>(VSCR+80)
        sta mp+1
        lda #<(COLRAM+80)
        sta mtmp+1              ; (low byte only; high tracked in tmp+1)
        lda #>(COLRAM+80)
        sta tmp+1
        lda #<(COLRAM+80)
        sta tmp
        lda #4                  ; 4 x 220 = 880 cells
        sta mi
@pg:    ldy #0
@l:     lda (mp),y
        tax
        lda vclass,x            ; colour class of the glyph
        tax
        lda mtmp
        beq :+
        lda ccol_paused,x
        jmp :++
:       lda ccol_active,x
:       sta (tmp),y
        iny
        cpy #220
        bne @l
        lda mp
        clc
        adc #220
        sta mp
        bcc :+
        inc mp+1
:       lda tmp
        clc
        adc #220
        sta tmp
        bcc :+
        inc tmp+1
:       dec mi
        bne @pg
        ; chute gates keep their red
        lda chutes_open
        bne :+
        lda #COL_RED
        sta COLRAM+CHUTE_ROW*40+CHUTE_L
        sta COLRAM+CHUTE_ROW*40+CHUTE_R
:       rts

; ------------------------------------------------------------------------
; mz_reset_actors: Pac-Man to start, ghosts into the house
mz_reset_actors:
        lda #<(PAC_COL*8)
        sta ax_lo
        lda #>(PAC_COL*8)
        sta ax_hi
        lda #PAC_ROW*8
        sta ay
        lda #D_LEFT
        sta adir
        sta want
        ldx #1
:       lda start_x,x
        sta ax_lo,x
        lda #0
        sta ax_hi,x
        sta gstate,x
        sta gblue,x
        lda start_y,x
        sta ay,x
        lda #D_LEFT
        sta adir,x
        lda rel_time,x
        sta grel,x
        inx
        cpx #5
        bne :-
        lda #0
        sta fright
        sta fright+1
        sta mz_hold
        sta mode_t
        sta mode_t+1
        sta chase
        sta pac_ph
        jsr fruit_hide
        jsr mz_show_sprites
        rts

; mz_show_sprites: Pac-Man + ghosts (+ the fruit if it is out)
mz_show_sprites:
        lda VIC_SPREN
        and #$E0
        ora #$1F
        sta VIC_SPREN
        jsr draw_sprites
        rts

mz_hide_pac:
        lda VIC_SPREN
        and #$FE
        sta VIC_SPREN
        rts

; mz_sprites_off: everything off (title screen, game over)
mz_sprites_off:
        jsr mz_siren_off
        lda #0
        sta VIC_SPREN
        sta VIC_SPRXEXP
        sta VIC_SPRYEXP
        sta mz_gob
        sta fr_t
        sta fr_t+1
        rts

; ------------------------------------------------------------------------
; mz_frame: one maze frame. Returns event in A.
mz_frame:
        lda #EV_NONE
        sta mev
        ; joystick -> want
        lda joy2
        and #$0F
        beq @idle
        ldx #3
:       lda joybit,x
        and joy2
        bne :+
        dex
        bpl :-
        bmi @nojoy
:       stx want
        lda #0
        sta wantage
        beq @nojoy
@idle:  lda wantage             ; stick released: keep the wish for 24 frames
        cmp #24                 ; (contact bounce), then Pac-Man just carries on
        bcs :+
        inc wantage
        bne @nojoy
:       lda adir
        sta want
@nojoy:
.ifdef AUTOPLAY
        jsr autopilot
.endif
        ; frightened timer; at the end every ghost is normal again
        lda fright
        ora fright+1
        beq :+
        lda fright
        bne @fd
        dec fright+1
@fd:    dec fright
        lda fright
        ora fright+1
        bne :+
        sta gblue+1
        sta gblue+2
        sta gblue+3
        sta gblue+4
:       lda #0
        sta pmoved
        jsr blink_ener
        jsr siren_tick
        ; scatter/chase: 7 s scatter, 20 s chase
        inc mode_t
        bne :+
        inc mode_t+1
:       jsr mode_check
        ; Pac-Man
        ldx #0
        jsr move_pac
        lda mev
        bne @done
        jsr fruit_tick
        ; ghosts
        lda mz_hold
        beq :+
        dec mz_hold
        jmp @col
:       ldx #1
@g:     stx mi
        jsr ghost_step
        ldx mi
        inx
        cpx #5
        bne @g
@col:   jsr collide
@done:  jsr draw_sprites
        lda mev
        rts

mode_check:
        lda chase
        bne @c
        lda mode_t+1
        cmp #>(7*60)
        bcc @x
        lda mode_t
        cmp #<(7*60)
        bcc @x
        lda #1
        bne @flip
@c:     lda mode_t+1
        cmp #>(20*60)
        bcc @x
        lda mode_t
        cmp #<(20*60)
        bcc @x
        lda #0
@flip:  sta chase
        lda #0
        sta mode_t
        sta mode_t+1
        ; reverse all active ghosts
        ldx #1
:       lda gstate,x
        beq :+
        lda adir,x
        eor #1
        sta adir,x
:       inx
        cpx #5
        bne :--
@x:     rts

; tile_of: X = actor -> mcol, mrow ; Z/C: A = (ax|ay)&7 (0 = centre)
tile_of:
        lda ax_hi,x
        lsr
        lda ax_lo,x
        ror
        lsr
        lsr
        sta mcol
        lda ay,x
        lsr
        lsr
        lsr
        sta mrow
        lda ax_lo,x
        ora ay,x
        and #7
        rts

; cell_type: (mcol + dc, mrow + dr) for dir A -> A = type, Y = col
; returns type of the neighbour cell in direction A
neighbour:
        tay
        lda mcol
        clc
        adc dxtab,y
        sta tgt_c
        lda mrow
        clc
        adc dytab,y
        sta tgt_r
        ; fall into cell_at
cell_at:                        ; tgt_c/tgt_r -> A = type, mp -> cell offset
        ldy tgt_r
        lda row40lo,y
        clc
        adc tgt_c
        sta mp
        lda row40hi,y
        adc #0
        sta mp+1
        lda mp
        clc
        adc #<mz_type
        sta mtmp
        lda mp+1
        adc #>mz_type
        sta mtmp+1
        ldy #0
        lda (mtmp),y
        rts

; pac_legal: A = dir -> C=1 if Pac-Man may go that way from (mcol,mrow)
pac_legal:
        sta cand
        jsr neighbour
        cmp #T_OPEN
        beq @y
        cmp #T_TUN
        beq @y
        cmp #T_CHUTE
        bne @n
        lda chutes_open
        beq @n
        lda cand
        cmp #D_DOWN
        beq @y
@n:     clc
        rts
@y:     sec
        rts

; ghost_legal: A = dir -> C=1 if a ghost may go that way
ghost_legal:
        jsr neighbour
        cmp #T_OPEN
        beq @y
        cmp #T_TUN
        beq @y
        clc
        rts
@y:     sec
        rts

; move_pac: X = 0
move_pac:
        ; reverse at any time
        lda want
        eor #1
        cmp adir
        bne :+
        lda want
        sta adir
:       jsr tile_of
        bne @move
        ; at a tile centre: eat, chute, tunnel, turn
        jsr eat
        lda mev
        beq :+
        rts
:       lda mrow
        cmp #CHUTE_ROW
        bne @noch
        lda #EV_CHUTE
        sta mev
        ldy #0
        lda mcol
        cmp #CHUTE_L
        beq :+
        iny
:       sty mz_chute
        rts
@noch:  jsr fruit_eat
        ldx #0
        jsr tunnel
        ldx #0
        lda want
        jsr pac_legal
        bcc :+
        lda want
        sta adir
        jmp @move
:       lda adir
        jsr pac_legal
        bcs @move
        rts                     ; blocked: stand still
@move:  lda #1
        sta pmoved
        ldx #0
        jmp step

; tunnel: wrap actor X at the tunnel mouths
tunnel:
        lda mrow
        cmp #TUN_ROW
        bne @x
        lda mcol
        cmp #TUN_L
        bne :+
        lda adir,x
        cmp #D_LEFT
        bne @x
        lda #<(TUN_R*8)
        sta ax_lo,x
        lda #>(TUN_R*8)
        sta ax_hi,x
        .ifdef AUTOTOUR
        inc tour_wr
        .endif
        rts
:       cmp #TUN_R
        bne @x
        lda adir,x
        cmp #D_RIGHT
        bne @x
        lda #<(TUN_L*8)
        sta ax_lo,x
        lda #>(TUN_L*8)
        sta ax_hi,x
        .ifdef AUTOTOUR
        inc tour_wr
        .endif
@x:     rts

; step: move actor X one pixel in adir
step:
        lda adir,x
        cmp #D_RIGHT
        bne :+
        inc ax_lo,x
        bne @x
        inc ax_hi,x
        rts
:       cmp #D_LEFT
        bne :+
        lda ax_lo,x
        bne @d
        dec ax_hi,x
@d:     dec ax_lo,x
        rts
:       cmp #D_UP
        bne :+
        dec ay,x
        rts
:       inc ay,x
@x:     rts

; eat: dot / energizer at Pac-Man's tile (mcol, mrow)
eat:
        lda mcol
        sta tgt_c
        lda mrow
        sta tgt_r
        jsr cell_at             ; mp = offset
        lda mp
        clc
        adc #<dots
        sta mtmp
        lda mp+1
        adc #>dots
        sta mtmp+1
        ldy #0
        lda (mtmp),y
        beq @x
        pha
        lda #0
        sta (mtmp),y
        ; blank the screen cell
        lda mp
        clc
        adc #<VSCR
        sta mtmp
        lda mp+1
        adc #>VSCR
        sta mtmp+1
        lda #$20
        sta (mtmp),y
        pla
        cmp #2
        beq @ener
        lda #10
        ldx #0
        jsr pb_add_score
        lda #5                  ; chomp
        jsr pb_sfx
        lda mz_dotsleft
        bne :+
        dec mz_dotsleft+1
:       dec mz_dotsleft
        lda mz_dotsleft
        ora mz_dotsleft+1
        bne @x
        lda #EV_CLEAR
        sta mev
@x:     rts
@ener:  lda #50
        ldx #0
        jsr pb_add_score
        lda #<360
        sta fright
        lda #>360
        sta fright+1
        lda #0
        sta eatcount
        lda #3
        jsr pb_sfx
        ; every ghost that is not just eyes turns blue; active ones reverse
        ldx #1
@g:     lda gstate,x
        cmp #2
        beq @ng
        lda #1
        sta gblue,x
        lda gstate,x
        beq @ng
        lda adir,x
        eor #1
        sta adir,x
@ng:    inx
        cpx #5
        bne @g
        rts

; ghost_step: X = ghost 1-4
ghost_step:
        lda gstate,x
        bne @act
        ; in the house: count down, then appear above the door
        lda frame
        and #3
        bne @x
        dec grel,x
        bne @x
        lda #1
        sta gstate,x
        lda #<(19*8)
        sta ax_lo,x
        lda #0
        sta ax_hi,x
        lda #9*8
        sta ay,x
        txa
        and #1
        sta adir,x              ; odd ghosts go left, even right
@x:     rts
@act:   cmp #2
        bne @live
        jsr eye_step            ; eyes: 2 px per frame back to the house
        ldx mi
        jmp eye_step
@live:  ; speed: frightened 1/2, normal 7/8
        lda gblue,x
        beq :+
        lda frame
        and #1
        beq @x
        jmp @go
:       lda frame
        and #7
        beq @x
@go:    jsr tile_of
        bne @mv
        jsr tunnel
        ldx mi
        jsr tile_of             ; after a warp: the cell on the other side
        ldx mi
        jsr choose_dir
        ldx mi
@mv:    jmp step

; eye_step: X = ghost (eyes). One pixel toward the door; on arrival above
; the door the ghost goes back into the house and comes out normal.
eye_step:
        lda gstate,x
        cmp #2
        bne @x
        jsr tile_of
        bne @mv
        lda mrow
        cmp #9
        bne @nav
        lda mcol
        cmp #19
        beq @home
        cmp #20
        beq @home
@nav:   jsr tunnel
        ldx mi
        jsr tile_of
        ldx mi
        jsr choose_dir
        ldx mi
@mv:    jmp step
@home:  lda #0
        sta gstate,x
        sta gblue,x
        lda #8                  ; out again after ~0.5 s
        sta grel,x
        lda home_x,x
        sta ax_lo,x
        lda #0
        sta ax_hi,x
        lda home_y,x
        sta ay,x
@x:     rts

; choose_dir: X = ghost at a tile centre
choose_dir:
        ; target: eyes -> the door, frightened -> random, else AI
        lda gstate,x
        cmp #2
        bne :+
        lda #19
        sta goal_c
        lda #9
        sta goal_r
        jmp @pick
:       lda gblue,x
        beq :+
        jmp choose_random
:       jsr target_of
@pick:
        lda #$FF
        sta best
        sta best+1
        sta bestd
        ldy #0
@d:     sty cand
        tya
        ldx mi
        eor #1
        cmp adir,x
        beq @next               ; no reversing
        lda cand
        jsr ghost_legal
        bcc @next
        ; dist^2 from (tgt_c, tgt_r) neighbour to target
        jsr dist2
        lda mtmp+1
        cmp best+1
        bcc @better
        bne @next
        lda mtmp
        cmp best
        bcs @next
@better:
        lda mtmp
        sta best
        lda mtmp+1
        sta best+1
        lda cand
        sta bestd
@next:  ldy cand
        iny
        cpy #4
        bne @d
        ldx mi
        lda bestd
        bpl :+
        lda adir,x              ; dead end: reverse
        eor #1
:       sta adir,x
        rts

; dist2: mtmp = (tgt_c - goal_c)^2 + (tgt_r - goal_r)^2
dist2:
        lda tgt_c
        sec
        sbc goal_c
        bcs :+
        eor #$FF
        adc #1
:       cmp #64
        bcc :+
        lda #63
:       tay
        lda sqlo,y
        sta mtmp
        lda sqhi,y
        sta mtmp+1
        lda tgt_r
        sec
        sbc goal_r
        bcs :+
        eor #$FF
        adc #1
:       cmp #64
        bcc :+
        lda #63
:       tay
        lda sqlo,y
        clc
        adc mtmp
        sta mtmp
        lda sqhi,y
        adc mtmp+1
        sta mtmp+1
        rts

choose_random:
        lda #4                  ; try up to 4 random directions
        sta rcnt                ; (not mtmp+1: ghost_legal overwrites that, and a
                                ; ghost with only "reverse" left looped forever)
@t:     lda frame
        eor ay
        eor ax_lo
        adc rcnt
        and #3
        sta cand
        ldx mi
        eor #1
        cmp adir,x
        beq @n
        lda cand
        jsr ghost_legal
        bcc @n
        ldx mi
        lda cand
        sta adir,x
        rts
@n:     dec rcnt
        bne @t
        ; fall back: first legal non-reverse in order
        ldy #0
@o:     sty cand
        ldx mi
        tya
        eor #1
        cmp adir,x
        beq @on
        tya
        jsr ghost_legal
        bcc @on
        ldx mi
        lda cand
        sta adir,x
        rts
@on:    ldy cand
        iny
        cpy #4
        bne @o
        ldx mi
        lda adir,x
        eor #1
        sta adir,x
        rts

; target_of: ghost mi -> goal_c/goal_r ; uses Pac-Man tile
target_of:
        ldx #0
        jsr tile_of
        lda mcol
        sta pac_c
        lda mrow
        sta pac_r
        ldx mi
        jsr tile_of             ; ghost tile back in mcol/mrow
        lda chase
        bne :+
        ldx mi
        lda scat_c,x
        sta goal_c
        lda scat_r,x
        sta goal_r
        rts
:       ldx mi
        cpx #2
        bne @n2
        ; Pinky: 4 tiles ahead of Pac-Man
        ldy adir
        lda dxtab,y
        asl
        asl
        clc
        adc pac_c
        sta goal_c
        lda dytab,y
        asl
        asl
        clc
        adc pac_r
        sta goal_r
        rts
@n2:    cpx #4
        bne @n4
        ; Clyde: chase when far, else scatter
        lda mcol
        sec
        sbc pac_c
        bcs :+
        eor #$FF
        adc #1
:       cmp #8
        bcs @blinky
        lda mrow
        sec
        sbc pac_r
        bcs :+
        eor #$FF
        adc #1
:       cmp #8
        bcs @blinky
        lda scat_c,x
        sta goal_c
        lda scat_r,x
        sta goal_r
        rts
@n4:    cpx #3
        bne @blinky
        ; Inky: 2 ahead, offset from Blinky (simplified: opposite side)
        ldy adir
        lda dxtab,y
        asl
        clc
        adc pac_c
        sta goal_c
        lda pac_r
        sta goal_r
        rts
@blinky:
        lda pac_c
        sta goal_c
        lda pac_r
        sta goal_r
        ldx mi
        jsr tile_of
        rts

; collide: Pac-Man vs ghosts
collide:
        lda mz_hold
        bne @x
        ldx #1
@g:     lda gstate,x
        cmp #1                  ; only ghosts out in the maze (not eyes)
        bne @n
        lda ax_lo,x
        sec
        sbc ax_lo
        clc
        adc #5
        cmp #11
        bcs @n
        lda ax_hi,x
        cmp ax_hi
        bne @n
        lda ay,x
        sec
        sbc ay
        clc
        adc #5
        cmp #11
        bcs @n
        lda gblue,x
        beq @die
        ; eat the ghost: its eyes run back to the house
        lda #2
        sta gstate,x
        lda #0
        sta gblue,x
        stx mtmp
        inc eatcount
        ldy eatcount
        lda ghostpts_lo-1,y
        ldx ghostpts_hi-1,y
        jsr pb_add_score
        lda #2
        jsr pb_sfx
        ldx mtmp
        jmp @n
.ifdef AUTOTOUR
@die:   jmp @n                  ; test tour: ghosts cannot hurt
.else
@die:   lda #EV_DEATH
        sta mev
        rts
.endif
@n:     inx
        cpx #5
        bne @g
@x:     rts

; draw_sprites: positions, shapes, colours of Pac-Man and the ghosts.
; Shapes are 14 px, centred on the actor's cell: hi-res Pac-Man at x+21,
; multicolour ghosts at x+19 (7 MC px at MC column 1), both at y+47.
draw_sprites:
        lda #0
        sta mtmp
        ldx #0
@s:     txa
        asl
        tay
        lda ax_lo,x
        clc
        adc sprxoff,x
        sta VIC_SPR0X,y
        lda ax_hi,x
        adc #0
        beq :+
        lda sprbit,x
        ora mtmp
        sta mtmp
:       lda ay,x
        clc
        adc #47
        cpx #0
        beq :+
        pha                     ; ghosts in the house bob up and down
        lda gstate,x
        bne @nb
        lda frame
        and #16
        beq @nb
        pla
        sec
        sbc #2
        pha
@nb:    pla
:       sta VIC_SPR0Y,y
        inx
        cpx #5
        bne @s
        lda mtmp                ; (sprites 5-7 always sit left of x=256)
        sta VIC_SPRXMSB
        ; Pac-Man: chomp (closed, half, wide, half) only while moving
        lda pmoved
        beq :+
        inc pac_ph
:       lda pac_ph
        lsr
        and #3
        tay
        lda mouthseq,y
        beq @pset               ; 0 = closed (SP_PAC = 0)
        cmp #1
        bne :+
        lda #SP_PAC_HR
        bne :++
:       lda #SP_PAC_WR
:       clc
        adc adir                ; R L U D order = D_RIGHT..D_DOWN
@pset:  clc
        adc #SPRBASE
        sta SPRPTR
        lda #COL_YELLOW
        sta VIC_SPR0COL
        ; ghosts
        lda frame
        lsr
        lsr
        lsr
        and #1
        sta mtmp+1              ; feet phase
        ldx #1
@g:     lda gstate,x
        cmp #2
        bne @ng
        lda adir,x              ; eyes only
        clc
        adc #SPRBASE+SP_EY_R
        sta SPRPTR,x
        lda #COL_WHITE
        jmp @setc
@ng:    lda gblue,x
        beq @norm
        lda fright+1            ; frightened: flash white in the last 2 s
        bne @fb
        lda fright
        cmp #120
        bcs @fb
        lda frame
        and #8
        beq @fb
        lda mtmp+1
        clc
        adc #SPRBASE+SP_FL0
        sta SPRPTR,x
        lda #COL_WHITE
        jmp @setc
@fb:    lda mtmp+1
        clc
        adc #SPRBASE+SP_FR0
        sta SPRPTR,x
        lda #COL_BLUE
        jmp @setc
@norm:  lda adir,x              ; looking where it goes
        ldy gstate,x
        bne @dir
        lda frame               ; in the house: looking up / down with the bob
        and #16
        beq :+
        lda #D_UP
        jmp @dir
:       lda #D_DOWN
@dir:   asl
        ora mtmp+1
        clc
        adc #SPRBASE+SP_GH_R0
        sta SPRPTR,x
        lda mz_hold             ; after a pinball visit: flash white
        beq @base
        lda frame
        and #16
        beq @base
        lda #COL_WHITE
        jmp @setc
@base:  lda gcolour,x
@setc:  sta VIC_SPR0COL,x
        inx
        cpx #5
        bne @g
        rts

; blink_ener: energizers in the four corner slots blink (cyan / off)
blink_ener:
        lda frame
        and #7
        bne @x
        ldy #COL_CYAN
        lda frame
        and #8
        bne :+
        ldy #COL_BLACK
:       sty mtmp
        ldy #3
@s:     ldx slot_off_lo,y
        lda slot_off_hi,y
        beq @lo
        lda dots+768,x
        cmp #2
        bne @n
        lda mtmp
        sta COLRAM+768,x
        jmp @n
@lo:    lda dots,x
        cmp #2
        bne @n
        lda mtmp
        sta COLRAM,x
@n:     dey
        bpl @s
@x:     rts

; fruit_tick: count the fruit down; bring one out at 70 and 170 dots
fruit_tick:
        lda fr_t
        ora fr_t+1
        beq @spawn
        lda fr_t
        bne :+
        dec fr_t+1
:       dec fr_t
        lda fr_t
        ora fr_t+1
        bne @x
        jmp fruit_hide
@spawn: lda mz_gob
        bne @x
        ldy fr_shown
        cpy #2
        bcs @x
        lda #<NDOTS             ; dots eaten = NDOTS - dots left
        sec
        sbc mz_dotsleft
        tax
        lda #>NDOTS
        sbc mz_dotsleft+1
        bne @go                 ; 256+ eaten
        txa
        cmp fr_thresh,y
        bcc @x
@go:    inc fr_shown
        lda #<FR_TIME
        sta fr_t
        lda #>FR_TIME
        sta fr_t+1
        jmp fruit_show
@x:     rts

; fruit_show: sprites 5 (body) and 6 (detail) at the start cell
fruit_show:
        lda fr_kind
        asl
        clc
        adc #SPRBASE+SP_FRUIT0
        sta SPRPTR+5
        adc #1                  ; SP_FRUITDn = SP_FRUITn + 1
        sta SPRPTR+6
        ldx fr_kind
        lda fr_body,x
        sta VIC_SPR0COL+5
        lda fr_det,x
        sta VIC_SPR0COL+6
        lda #FR_X
        sta VIC_SPR0X+10
        sta VIC_SPR0X+12
        lda #FR_Y
        sta VIC_SPR0Y+10
        sta VIC_SPR0Y+12
        lda VIC_SPRXEXP
        and #$9F
        sta VIC_SPRXEXP
        lda VIC_SPRYEXP
        and #$9F
        sta VIC_SPRYEXP
        lda VIC_SPREN
        ora #$60
        sta VIC_SPREN
        rts

fruit_hide:
        lda #0
        sta fr_t
        sta fr_t+1
        lda VIC_SPREN
        and #$9F
        sta VIC_SPREN
        rts

; fruit_eat: Pac-Man at a tile centre on the fruit cell eats it
fruit_eat:
        lda fr_t
        ora fr_t+1
        beq @x
        lda mrow
        cmp #15
        bne @x
        lda mcol
        cmp #19
        bne @x
        jsr fruit_hide
        ldx fr_kind
        lda fr_pts_lo,x
        pha
        lda fr_pts_hi,x
        tax
        pla
        jsr pb_add_score
        lda #3
        jsr pb_sfx
@x:     rts

; ------------------------------------------------------------------------
; TITLE SCREEN (VIC). Rows: 0-1 high score, 3-5 "BABY", 7-9 "PAC-MAN" (our
; logo glyphs), 11-19 character roster with the ghost sprites, 21 a row of
; dots that Pac-Man eats while three ghosts chase him, 23 PRESS FIRE,
; 24 homage line. mz_title_anim runs every frame: colour cycling on BABY,
; a white shine sweeping across PAC-MAN, blinking prompt, the chase.
T_CHASE_ROW = 21
T_CHASE_Y   = 50 + T_CHASE_ROW*8 + 4 - 7
T_CHASE_TOP = 345 + 100        ; chase_x start (Pac-Man just off the right)
T_CHASE_END = 100 - 70         ; ... until the last ghost is behind the border

mz_title_draw:
        jsr mz_sprites_off
        ldx #0
:       lda title_baby,x
        sta VSCR+3*40,x
        lda title_pac,x
        sta VSCR+7*40,x
        inx
        cpx #120
        bne :-
        MASK 1
        COLOR COL_WHITE
        PRS 0, 15, "HIGH SCORE"
        COLOR COL_LTGREY
        lda #1
        ldx #16
        jsr scr_at
        lda mz_hiscore
        sta num
        lda mz_hiscore+1
        sta num+1
        lda mz_hiscore+2
        sta num+2
        lda #7
        jsr fmt_dec
        jsr print
        COLOR COL_WHITE
        PRS 11, 10, "CHARACTER / NICKNAME"
        COLOR COL_RED
        PRS 13, 12, {"SHADOW    ", $22, "BLINKY", $22}
        COLOR COL_LTRED
        PRS 15, 12, {"SPEEDY    ", $22, "PINKY", $22}
        COLOR COL_CYAN
        PRS 17, 12, {"BASHFUL   ", $22, "INKY", $22}
        COLOR COL_ORANGE
        PRS 19, 12, {"POKEY     ", $22, "CLYDE", $22}
        COLOR COL_DKGREY
        PRS 24, 4, "A FAN-MADE HOMAGE - NOT FOR SALE"
        COLOR COL_YELLOW
        PRS 23, 11, "PRESS FIRE TO PLAY"
        ; roster ghosts: sprites 1-4 left of the names, facing right
        ldx #1
:       txa
        asl
        tay
        lda #24+9*8-5
        sta VIC_SPR0X,y
        lda t_rost_y,x
        sta VIC_SPR0Y,y
        lda gcolour,x
        sta VIC_SPR0COL,x
        inx
        cpx #5
        bne :-
        ; chase: Pac-Man (0, hi-res) and Blinky / Pinky / Inky (5-7, MC)
        lda #COL_YELLOW
        sta VIC_SPR0COL
        lda #COL_RED
        sta VIC_SPR0COL+5
        lda #COL_LTRED
        sta VIC_SPR0COL+6
        lda #COL_CYAN
        sta VIC_SPR0COL+7
        lda #T_CHASE_Y
        sta VIC_SPR0Y
        sta VIC_SPR0Y+10
        sta VIC_SPR0Y+12
        sta VIC_SPR0Y+14
        lda #$FE                ; all but Pac-Man multicolour
        sta VIC_SPRMC
        jsr t_chase_reset
        jsr mz_title_anim
        lda #$FF
        sta VIC_SPREN
        rts

; t_chase_reset: chase from the right edge, dots back on row 21
t_chase_reset:
        lda #<T_CHASE_TOP
        sta chase_x
        lda #>T_CHASE_TOP
        sta chase_x+1
        ldx #39
:       lda #$20
        sta VSCR+T_CHASE_ROW*40,x
        lda #COL_LTRED
        sta COLRAM+T_CHASE_ROW*40,x
        dex
        bpl :-
        ldx #36
:       lda #G_DOT
        sta VSCR+T_CHASE_ROW*40,x
        dex
        dex
        cpx #2
        bcs :-
        rts

mz_title_anim:
        ; BABY: colour cycle (8 colours, 6 frames each)
        lda frame
        lsr
        lsr
        lsr
        and #7
        tax
        lda t_cyc,x
        ldx #119
:       sta COLRAM+3*40,x
        dex
        bpl :-
        ; PAC-MAN: yellow with a 3-column white shine sweeping right
        lda frame
        and #63
        sec
        sbc #12                 ; shine column (starts off the left edge)
        sta mtmp
        ldx #39
@sh:    txa
        sec
        sbc mtmp
        cmp #3
        lda #COL_YELLOW
        bcs :+
        lda #COL_WHITE
:       sta COLRAM+7*40,x
        sta COLRAM+8*40,x
        sta COLRAM+9*40,x
        dex
        bpl @sh
        ; PRESS FIRE blink
        lda frame
        and #32
        beq :+
        lda #COL_YELLOW
:       ldx #17
:       sta COLRAM+23*40+11,x
        dex
        bpl :-
        ; roster feet
        lda frame
        lsr
        lsr
        lsr
        and #1
        sta mtmp+1
        clc
        adc #SPRBASE+SP_GH_R0
        sta SPRPTR+1
        sta SPRPTR+2
        sta SPRPTR+3
        sta SPRPTR+4
        lda mtmp+1
        clc
        adc #SPRBASE+SP_GH_L0
        sta SPRPTR+5
        sta SPRPTR+6
        sta SPRPTR+7
        ; Pac-Man chomping left
        lda frame
        lsr
        and #3
        tay
        lda mouthseq,y
        beq @p0
        cmp #1
        bne :+
        lda #SP_PAC_HL
        bne @p0
:       lda #SP_PAC_WL
@p0:    clc
        adc #SPRBASE
        sta SPRPTR
        ; chase positions: x = chase_x - 100 + 22*i (0 when behind the border)
        lda #0
        sta mtmp
        ldx #3
@cx:    lda chase_x
        clc
        adc t_choff,x
        sta tmp
        lda chase_x+1
        adc #0
        sta tmp+1
        lda tmp
        sec
        sbc #100
        sta tmp
        lda tmp+1
        sbc #0
        bcs :+
        lda #0                  ; left of the screen: park behind the border
        sta tmp
:       sta tmp+1
        ldy t_chspr,x
        lda tmp
        sta VIC_SPR0X,y
        lda tmp+1
        beq :+
        lda t_chbit,x
        ora mtmp
        sta mtmp
:       dex
        bpl @cx
        lda mtmp
        sta VIC_SPRXMSB
        ; Pac-Man eats the dot under his mouth: col = (chase_x - 121) / 8
        lda chase_x
        sec
        sbc #100+24-3
        sta tmp
        lda chase_x+1
        sbc #0
        bcc @ne                 ; left of column 0
        lsr
        ror tmp
        lsr tmp
        lsr tmp
        lda tmp
        cmp #40
        bcs @ne
        tax
        lda #$20
        sta VSCR+T_CHASE_ROW*40,x
@ne:    ; move; wrap when the last ghost is gone
        lda chase_x
        bne :+
        dec chase_x+1
:       dec chase_x
        lda chase_x+1
        bne @x
        lda chase_x
        cmp #T_CHASE_END
        bcs @x
        jmp t_chase_reset
@x:     rts

; mz_title_fade: A = step 0-3: everything to light grey, grey, dark grey,
; black (sprites off at step 0)
mz_title_fade:
        tax
        bne :+
        lda #0
        sta VIC_SPREN
:       lda t_fade,x
        ldx #0
:       sta COLRAM,x
        sta COLRAM+250,x
        sta COLRAM+500,x
        sta COLRAM+750,x
        inx
        cpx #250
        bne :-
        rts

; ------------------------------------------------------------------------
; SOUND (SID voices 2 and 3; voice 1 is pb_sfx). Siren: triangle on voice 2
; sweeping up and down while the maze runs; faster and higher while ghosts
; are blue. Jingle: our own short fanfare on voice 3 during READY at the
; start of a game.
siren_tick:
        lda sir_on
        bne :+
        lda #$00
        sta SID+12              ; voice 2: attack 0 decay 0
        lda #$70
        sta SID+13              ; sustain 7 (quieter than the effects)
        lda #$11
        sta SID+11              ; triangle, gate on
        sta sir_on
:       inc sir_ph
        lda sir_ph
        ldx fright
        bne @fast
        ldx fright+1
        bne @fast
        and #63                 ; normal: 64-frame sweep
        cmp #32
        bcc :+
        eor #63
:       lsr
        clc
        adc #$14
        bne @set
@fast:  asl                     ; blue ghosts: 32-frame sweep, higher
        and #63
        cmp #32
        bcc :+
        eor #63
:       clc
        adc #$22
@set:   sta SID+8
        lda #0
        sta SID+7
        rts

mz_siren_off:
        lda #$10                ; gate off (release 0: stops at once)
        sta SID+11
        lda #0
        sta sir_on
        rts

mz_jingle_start:
        lda #0
        sta jn_i
        lda #1
        sta jn_t
        lda #$00
        sta SID+16              ; voice 3 pulse width 50 %
        lda #$08
        sta SID+17
        lda #$08
        sta SID+19              ; attack 0, decay 8
        lda #$90
        sta SID+20              ; sustain 9, release 0
        lda #$0F
        sta SID_VOL
        rts

; mz_jingle_tick: call once per frame; plays jn_* (hi 0 = rest, $FF = end)
mz_jingle_tick:
        lda jn_t
        beq @x                  ; finished
        dec jn_t
        bne @x
        lda #$40                ; gate off between notes
        sta SID+18
        ldx jn_i
        lda jn_hi,x
        cmp #$FF
        beq @end
        inc jn_i
        lda jn_len,x
        sta jn_t
        lda jn_hi,x
        beq @x                  ; rest
        sta SID+15
        lda jn_lo,x
        sta SID+14
        lda #$41                ; pulse, gate on
        sta SID+18
@x:     rts
@end:   lda #0
        sta jn_t
        rts

; mz_go_show: A = colour: GO! banner (sprites 7 = "GO", 6 = "!", doubled)
; over the ghost house; A = 0 hides it.
mz_go_show:
        cmp #0
        beq @hide
        sta VIC_SPR0COL+6
        sta VIC_SPR0COL+7
        lda #SPRBASE+SP_GO
        sta SPRPTR+7
        lda #SPRBASE+SP_GOX
        sta SPRPTR+6
        lda #GO_X
        sta VIC_SPR0X+14
        lda #GO_X+50
        sta VIC_SPR0X+12
        lda #GO_Y
        sta VIC_SPR0Y+14
        sta VIC_SPR0Y+12
        lda VIC_SPRXEXP
        ora #$C0
        sta VIC_SPRXEXP
        lda VIC_SPRYEXP
        ora #$C0
        sta VIC_SPRYEXP
        lda VIC_SPREN
        ora #$C0
        sta VIC_SPREN
        lda #1
        sta mz_gob
        rts
@hide:  lda VIC_SPREN
        and #$3F
        sta VIC_SPREN
        lda VIC_SPRXEXP
        and #$3F
        sta VIC_SPRXEXP
        lda VIC_SPRYEXP
        and #$3F
        sta VIC_SPRYEXP
        lda #0
        sta mz_gob
        rts

; ------------------------------------------------------------------------
; mz_freeze: maze paused look (Pac-Man hidden, walls dim, message)
.ifdef AUTOTOUR
; autopilot (tour test build): at each new cell centre take the next
; direction of tour_table (every dot, then the tunnel both ways).
autopilot:
        ldx #0
        jsr tile_of
        beq :+
        rts
:       lda mcol
        cmp tour_c
        bne :+
        lda mrow
        cmp tour_r
        beq @x                  ; same cell: no new step
:       lda mcol
        sta tour_c
        lda mrow
        sta tour_r
        ldy #0
        lda (tp),y
        cmp #$FF
        bne :+
        lda tour_boards         ; end of a table: 1 = dots done, 2 = all done
        sta tour_done
        rts
:       sta want
        inc tp
        bne @x
        inc tp+1
@x:     rts
.include "tour_data.s"
.segment "CODE"
.else
.ifdef AUTOPLAY
; autopilot (test builds only): at tile centres, steer Pac-Man toward a
; chute (alternating left/right by board half) without reversing.
autopilot:
        ldx #0
        jsr tile_of
        beq :+
        rts
:       lda chutes_open
        beq @dots
        lda #CHUTE_ROW
        sta goal_r
        lda frame+1
        and #1
        tax
        lda chutecol,x
        sta goal_c
        jmp @pick
@dots:  lda frame+1
        and #3
        tax
        lda scat_c+1,x
        sta goal_c
        lda scat_r+1,x
        sta goal_r
@pick:  lda #$FF
        sta best
        sta best+1
        sta bestd
        ldy #0
@d:     sty cand
        tya
        eor #1
        cmp adir
        beq @nx
        lda cand
        jsr pac_legal
        bcc @nx
        jsr dist2
        lda mtmp+1
        cmp best+1
        bcc @b
        bne @nx
        lda mtmp
        cmp best
        bcs @nx
@b:     lda mtmp
        sta best
        lda mtmp+1
        sta best+1
        lda cand
        sta bestd
@nx:    ldy cand
        iny
        cpy #4
        bne @d
        lda bestd
        bmi :+
        sta want
:       rts
.endif
.endif

mz_freeze:
        jsr mz_hide_pac
        jsr fruit_hide
        jsr mz_siren_off
        lda #COL_DKGREY
        sta VIC_BORDER
        MASK 1
        COLOR COL_LTRED
        PRS 24, 1, "<< PINBALL IS ON THE LEFT SCREEN      "
        lda #1
        jmp mz_paint

; mz_resume: A = chute (0/1), X = energizers to award
mz_resume:
        sta mz_chute
        stx awards
        lda fr_kind             ; fruit lanes lit on the table: better fruit
        clc
        adc pb_fruit
        cmp #4
        bcc :+
        lda #3
:       sta fr_kind
        lda #0
        jsr mz_set_chutes
        lda #0
        jsr mz_paint
        lda #COL_BLACK
        sta VIC_BORDER
        ; energizers into empty corner slots (cap 4); extras = 500 points
@e:     lda awards
        beq @pac
        dec awards
        ldy #0
@s:     ldx slot_off_lo,y
        lda slot_off_hi,y
        beq :+
        lda dots+768,x
        jmp :++
:       lda dots,x
:       beq @put
        iny
        cpy #4
        bne @s
        lda #<500
        ldx #>500
        jsr pb_add_score
        jmp @e
@put:   lda #2
        ldx slot_off_lo,y
        pha
        lda slot_off_hi,y
        beq :+
        pla
        sta dots+768,x
        lda #G_ENER
        sta VSCR+768,x
        lda #COL_CYAN
        sta COLRAM+768,x
        jmp @e
:       pla
        sta dots,x
        lda #G_ENER
        sta VSCR,x
        lda #COL_CYAN
        sta COLRAM,x
        jmp @e
@pac:   ; Pac-Man reappears above the chute he took, facing up
        ldx mz_chute
        lda chutecol,x
        asl
        asl
        asl
        sta ax_lo
        lda #0
        rol
        sta ax_hi
        lda #(CHUTE_ROW-1)*8
        sta ay
        lda #D_UP
        sta adir
        sta want
        lda #90
        sta mz_hold
        jsr mz_show_sprites
        rts

; mz_hud: arcade-style: 1UP (blinking) and HIGH SCORE on row 0, the
; numbers on row 1, Pac-Man lives and the fruit level icon on the right.
mz_hud:
        MASK 1
        COLOR COL_WHITE
        lda frame
        and #16
        beq :+
        PRS 0, 3, "1UP"
        jmp :++
:       PRS 0, 3, "   "
:       PRS 0, 15, "HIGH SCORE"
        lda #1
        ldx #1
        jsr scr_at
        lda pb_score
        sta num
        lda pb_score+1
        sta num+1
        lda pb_score+2
        sta num+2
        lda #7
        jsr fmt_dec
        jsr print
        lda #1
        ldx #16
        jsr scr_at
        lda mz_hiscore
        sta num
        lda mz_hiscore+1
        sta num+1
        lda mz_hiscore+2
        sta num+2
        lda #7
        jsr fmt_dec
        jsr print
        ; lives icons
        COLOR COL_YELLOW
        lda #1
        ldx #30
        jsr scr_at
        ldy #0
@lv:    sty mtmp
        lda #$20
        cpy mz_lives
        bcs :+
        lda #G_LIFE
:       jsr putc
        ldy mtmp
        iny
        cpy #5
        bne @lv
        ; fruit level icon
        ldx fr_kind
        lda fr_body,x
        jsr set_color
        lda #1
        ldx #37
        jsr scr_at
        lda fr_kind
        clc
        adc #G_FRUIT0
        jmp putc

mz_msg_clear:
        MASK 1
        PRS 24, 1, "                                      "
        rts

; mz_death_anim: A = frame counter (0..89). 0-29: everything freezes;
; 30: ghosts and fruit vanish; 30-89: Pac-Man folds up (10 shapes x 6).
mz_death_anim:
        cmp #0
        bne :+
        jsr mz_siren_off
        lda #0
:       cmp #30
        bcc @x
        bne :+
        pha
        lda #$01
        sta VIC_SPREN
        lda #0
        sta fr_t
        sta fr_t+1
        pla
:       sec
        sbc #30
        ldx #$FF
:       inx
        sec
        sbc #6
        bcs :-
        cpx #NDIE
        bcc :+
        ldx #NDIE-1
:       txa
        clc
        adc #SPRBASE+SP_DIE0
        sta SPRPTR
@x:     rts

; mz_flash_walls: A = 1 white walls, 0 normal
mz_flash_walls:
        pha
        jsr mz_siren_off
        pla
        beq :+
        lda #COL_WHITE
        jmp :++
:       lda #COL_LTBLUE
:       sta ccol_active         ; class 0 = walls (RAM table)
        lda #0
        jmp mz_paint

.segment "RODATA"
dxtab:      .byte 1, $FF, 0, 0
dytab:      .byte 0, 0, $FF, 1
joybit:     .byte $08, $04, $01, $02    ; right, left, up, down
; start / home positions (pixels): Blinky starts outside above the door,
; Pinky centre, Inky left, Clyde right (all inside the house when home)
start_x:    .byte 0, 19*8, 156, 132, 180
start_y:    .byte 0, 9*8, 96, 96, 96
home_x:     .byte 0, 156, 156, 132, 180
home_y:     .byte 0, 96, 96, 96, 96
sprxoff:    .byte 21, 19, 19, 19, 19
fr_thresh:  .byte 70, 170
fr_body:    .byte COL_RED, COL_LTRED, COL_ORANGE, COL_RED
fr_det:     .byte COL_BROWN, COL_LTGREEN, COL_LTGREEN, COL_LTGREEN
fr_pts_lo:  .byte <100, <300, <500, <700
fr_pts_hi:  .byte >100, >300, >500, >700
; start jingle (our own fanfare): C5 E5 G5 C6 - A5 C6 G5 - E5 G5 C6.
; SID frequency values for NTSC (Hz x 16.404); lengths in frames
jn_lo:      .byte <8583, <10814, <12861, <17167, 0, <14436, <17167, <12861, 0
            .byte <10814, <12861, <17167, 0
jn_hi:      .byte >8583, >10814, >12861, >17167, 0, >14436, >17167, >12861, 0
            .byte >10814, >12861, >17167, $FF
jn_len:     .byte 6, 6, 6, 10, 4, 6, 6, 10, 4, 6, 6, 18, 0
; title screen
t_rost_y:   .byte 0, 50+13*8-3, 50+15*8-3, 50+17*8-3, 50+19*8-3
t_cyc:      .byte COL_LTRED, COL_ORANGE, COL_YELLOW, COL_LTGREEN
            .byte COL_CYAN, COL_LTBLUE, COL_PURPLE, COL_WHITE
t_choff:    .byte 0, 22, 44, 66         ; Pac-Man, Blinky, Pinky, Inky
t_chspr:    .byte 0, 10, 12, 14         ; VIC X register offsets (sprites 0,5,6,7)
t_chbit:    .byte $01, $20, $40, $80
t_fade:     .byte COL_LTGREY, COL_GREY, COL_DKGREY, COL_BLACK
rel_time:   .byte 0, 1, 45, 90, 135     ; x4 frames
scat_c:     .byte 0, 37, 2, 37, 2
scat_r:     .byte 0, 2, 2, 22, 22
gcolour:    .byte COL_YELLOW, COL_RED, COL_LTRED, COL_CYAN, COL_ORANGE
sprbit:     .byte 1, 2, 4, 8, 16
mouthseq:   .byte 0, 1, 2, 1
chutecol:   .byte CHUTE_L, CHUTE_R
ghostpts_lo: .byte <200, <400, <800, <1600, <1600, <1600
ghostpts_hi: .byte >200, >400, >800, >1600, >1600, >1600
; energizer slots: rows 3/21, columns 2/37 (offsets into 40x25)
slot_off_lo: .byte <(3*40+2), <(3*40+37), <(21*40+2-768), <(21*40+37-768)
slot_off_hi: .byte 0, 0, 3, 3
sqlo:
.repeat 64, I
            .byte <(I*I)
.endrepeat
sqhi:
.repeat 64, I
            .byte >(I*I)
.endrepeat
; colours by glyph class (vclass from mkmaze.py): 0 wall, 1 dot,
; 2 energizer, 3 door, 4 gate, 5 arrow, 6 life, 7 text/other, 8 fruit icon
ccol_paused:
            .byte COL_BLUE, COL_DKGREY, COL_BLUE, COL_DKGREY, COL_RED
            .byte COL_DKGREY, COL_YELLOW, COL_DKGREY, COL_DKGREY

.segment "DATA"
ccol_active:
            .byte COL_LTBLUE, COL_LTRED, COL_CYAN, COL_LTRED, COL_RED
            .byte COL_YELLOW, COL_YELLOW, COL_LTGREY, COL_RED

.segment "ZEROPAGE"
pac_c:      .res 1
pac_r:      .res 1
goal_c:     .res 1
goal_r:     .res 1
