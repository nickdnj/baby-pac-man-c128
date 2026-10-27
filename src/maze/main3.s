; main3.s - BABY PAC-MAN (Tier 3): maze on the VIC, pinball on the VDC,
; freeze/resume handoff between them. Scope-cut version: no attract demo,
; no high-score entry, no docent chord, no fruit, simple ghost AI.

.include "hw/c128.inc"
.include "hw/scr.inc"
.include "lib/macros.inc"

.importzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.importzp num, tmp, vdc_dead, frame, joy2, port1, joy2_edge, port1_edge
.importzp pb_state, pb_score, pb_energ, pb_fruit
.importzp mz_chute, mz_lives, mz_hold, mz_hiscore
.import scr_at, scr_vat, set_color, print, printi, putc, fmt_dec
.import cls_vic, cls_vdc
.import sys_init, wait_frame, read_input, ram_vectors, vdc_basic_init
.import pb_setup, pb_launch, pb_frame, pb_draw_panels, pb_flippers_rest
.import pb_reset_lights, pb_dim, pb_undim, pb_abort, pb_sfx, pb_show_score, pb_show_all, chr_ram
.import mz_init_gfx, mz_new_game, mz_new_board, mz_reset_actors, mz_frame
.import mz_freeze, mz_resume, mz_set_chutes, mz_hud, mz_paint, mz_show_sprites
.import mz_hide_pac, mz_msg_clear, mz_death_anim, mz_flash_walls, VSCR
.import mz_go_show, mz_sprites_off, mz_title_draw, mz_title_anim, mz_title_fade
.import pb_logo_tint, pb_sfx_tick, mz_jingle_start, mz_jingle_tick

VCHR = $C800
IDLE_FRAMES = 3600              ; 60 s

.segment "ZEROPAGE"
cnt:    .res 2
idle:   .res 2
lastin: .res 1
gotime: .res 1

.segment "CODE"
start:
        sei
        cld
        ; ROM font glyphs 0-63 -> chr_ram (VDC) and VCHR (VIC). Below $4000.
        ldx #0
@f:     lda #MMU_CFG_CHR
        sta MMU_CR
        lda $D000,x
        ldy #MMU_CFG_RAM
        sty MMU_CR
        sta chr_ram,x
        sta VCHR,x
        lda #MMU_CFG_CHR
        sta MMU_CR
        lda $D100,x
        ldy #MMU_CFG_RAM
        sty MMU_CR
        sta chr_ram+256,x
        sta VCHR+256,x
        inx
        bne @f
        lda #MMU_CFG_RAM
        sta MMU_CR
        ldx #$FF
        txs
        jsr ram_vectors
        jsr sys_init
        lda #0
        sta vdc_dead
        sta VIC_SPREN
        lda #3
        sta mz_hiscore          ; (cleared below)
        lda #0
        sta mz_hiscore
        sta mz_hiscore+1
        sta mz_hiscore+2
        jsr mz_init_gfx
        MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        COLOR COL_YELLOW
        PRS 12, 6, "BABY PAC-MAN: SETTING UP..."
        ; VDC
        jsr vdc_basic_init
        lda #COL_LTGREY
        jsr set_color
        jsr cls_vdc
        jsr pb_setup
        jsr pb_draw_panels
        jsr pb_reset_lights
        jsr pb_dim
        bit vdc_dead
        bmi :+
        jmp title
:       MASK 1
        COLOR COL_RED
        PRS 14, 1, "80-COL CHIP (VDC) NOT RESPONDING."
        PRS 15, 1, "MAZE ONLY: CHUTES WILL STAY SHUT."

; ------------------------------------------------------------------ title
; VIC: logo, roster and chase (maze.s). VDC: the table dimmed with PRESS
; FIRE in the right panel and the marquee colour-cycling. FIRE: fade out.
title:
        lda #0
        sta VIC_BORDER
        MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        jsr mz_title_draw
        jsr vdc_cue_title
        bit vdc_dead
        bmi :+
        jsr pb_show_all
:
@t:     jsr wait_frame
        jsr read_input
        jsr mz_title_anim
        lda frame
        and #7
        bne :+
        jsr vdc_logo_cycle
:       lda joy2_edge
        and #$10
        bne @g
        lda port1_edge
        and #$1C
        bne @g
.ifdef AUTOPLAY
        lda frame
        cmp #200
        beq @g
.endif
        jmp @t
@g:     jsr title_out
        jmp game

; title_out: fade the 40-col screen out (4 steps x 4 frames), marquee back
; to its own colours, screen cleared for the maze
title_out:
        lda #3
        jsr pb_sfx
        lda #0
        sta cnt
:       jsr wait_frame
        lda cnt
        and #3
        bne :+
        lda cnt
        lsr
        lsr
        jsr mz_title_fade
:       inc cnt
        lda cnt
        cmp #16
        bne :--
        bit vdc_dead
        bmi :+
        lda #RGBI_LTPURP
        ldx #RGBI_LTYEL
        jsr pb_logo_tint
:       MASK 1
        jmp cls_vic

; vdc_logo_cycle: marquee "BABY" through 8 colours, "PAC-MAN" yellow with
; a white flash once per cycle (VDC, ~6,800 cycles every 8 frames)
vdc_logo_cycle:
        bit vdc_dead
        bmi @x
        lda frame
        lsr
        lsr
        lsr
        and #7
        tay
        ldx #RGBI_LTYEL
        cpy #7
        bne :+
        ldx #RGBI_WHITE
:       lda vdc_cyc,y
        jmp pb_logo_tint
@x:     rts

; ------------------------------------------------------------------ game
game:
        lda #0
        sta pb_score
        sta pb_score+1
        sta pb_score+2
        jsr mz_new_game
        bit vdc_dead
        bpl :+
        lda #0
        jsr mz_set_chutes       ; no VDC: never open the chutes
:       jsr mz_reset_actors
        jsr mz_hud
        jsr mz_jingle_start     ; start fanfare plays over READY!
        jsr vdc_cue_maze
        bit vdc_dead
        bmi ready
        jsr pb_show_all

ready:
        lda #0
        jsr mz_go_show
        MASK 1
        COLOR COL_YELLOW
        PRS 24, 1, "               READY!                 "
        lda #90
        sta cnt
:       jsr wait_frame
        jsr read_input
        jsr mz_jingle_tick
        dec cnt
        bne :-
        jsr mz_msg_clear
        jsr hint
        lda #0
        sta gotime
        jsr idle_reset

play:   jsr wait_frame
        jsr read_input
        jsr pb_sfx_tick
        jsr idle_tick
        bcc :+
        jmp game_over
:       jsr mz_frame
        cmp #1
        bne :+
        jmp to_pinball
:
        cmp #2
        bne :+
        jmp death
:       cmp #3
        bne :+
        jmp clear
:       lda frame
        and #7
        bne :+
        jsr mz_hud
:       lda frame
        and #31
        cmp #4
        bne :+
        bit vdc_dead
        bmi :+
        jsr pb_show_score
:       lda gotime
        beq play
        dec gotime
        bne :+
        lda #0
        jsr mz_go_show
        jsr hint
        jmp play
:       and #7
        bne play
        jsr go_blink
        jmp play

; ------------------------------------------------------------------ handoff
to_pinball:
        jsr mz_freeze
        jsr pb_undim
        jsr pb_reset_lights
        jsr vdc_cue_pin
        lda mz_chute
        jsr pb_launch
pin:    jsr wait_frame
        jsr read_input
        jsr idle_tick
        bcc :+
        jsr pb_abort
        jsr pb_flippers_rest
        jsr pb_dim
        jmp game_over
:       jsr pb_frame
        cmp #2
        beq back
        lda frame
        and #15
        bne pin
        jsr mz_hud
        jmp pin

back:
        jsr pb_flippers_rest
        jsr pb_dim
        jsr vdc_cue_maze
        ldx pb_energ
        lda mz_chute
        jsr mz_resume
        jsr mz_hud
        jsr mz_msg_clear
        lda #60
        sta gotime
        jsr go_blink
        lda #3
        jsr pb_sfx
        jmp play

; go_blink: the big GO! banner over the ghost house, white / yellow
go_blink:
        lda gotime
        and #8
        beq :+
        lda #COL_WHITE
        jmp mz_go_show
:       lda #COL_YELLOW
        jmp mz_go_show

hint:
        MASK 1
        COLOR COL_YELLOW
        PRS 24, 1, " JOYSTICK STEERS - TAKE A CHUTE (V)   "
        rts

; ------------------------------------------------------------------ death
death:
        lda #4
        jsr pb_sfx
        lda #0
        sta cnt
:       jsr wait_frame
        lda cnt
        jsr mz_death_anim
        inc cnt
        lda cnt
        cmp #90
        bne :-
        dec mz_lives
        jsr mz_hud
        lda mz_lives
        beq game_over
        bit vdc_dead
        bmi :+
        lda #1
        jsr mz_set_chutes
:       lda #0
        jsr mz_paint
        jsr mz_reset_actors
        jmp ready

; ------------------------------------------------------------------ board clear
clear:
        lda #0
        sta cnt
:       jsr wait_frame
        lda cnt
        lsr
        lsr
        lsr
        lsr
        and #1
        jsr mz_flash_walls
        inc cnt
        lda cnt
        cmp #128
        bne :-
        lda #0
        jsr mz_flash_walls
        jsr mz_new_board
        bit vdc_dead
        bpl :+
        lda #0
        jsr mz_set_chutes
:       jsr mz_reset_actors
        jmp ready

; ------------------------------------------------------------------ game over
game_over:
        jsr mz_sprites_off
        lda #0
        sta VIC_BORDER
        lda #0
        jsr mz_paint
        ; high score
        lda pb_score+2
        cmp mz_hiscore+2
        bcc @nohi
        bne @hi
        lda pb_score+1
        cmp mz_hiscore+1
        bcc @nohi
        bne @hi
        lda pb_score
        cmp mz_hiscore
        bcc @nohi
@hi:    lda pb_score
        sta mz_hiscore
        lda pb_score+1
        sta mz_hiscore+1
        lda pb_score+2
        sta mz_hiscore+2
@nohi:  jsr mz_hud
        MASK 1
        COLOR COL_RED
        PRS 24, 1, "             GAME  OVER               "
        lda #180
        sta cnt
:       jsr wait_frame
        jsr read_input
        dec cnt
        bne :-
        jmp title

; ------------------------------------------------------------------ idle
idle_reset:
        lda #0
        sta idle
        sta idle+1
        rts
; idle_tick: C=1 when the game has had no input change for 60 s
idle_tick:
        lda joy2
        ora port1
        cmp lastin
        beq :+
        sta lastin
        jsr idle_reset
        clc
        rts
:       inc idle
        bne :+
        inc idle+1
:       lda idle+1
        cmp #>IDLE_FRAMES
        bcc @no
        bne @yes
        lda idle
        cmp #<IDLE_FRAMES
        bcc @no
@yes:   sec
        rts
@no:    clc
        rts

; ------------------------------------------------------------------ VDC cues
vdc_cue_title:
        MASK 2
        COLOR COL_YELLOW
        lda pr_vattr            ; hardware blink on the prompt
        ora #$10
        sta pr_vattr
        PRS 21, 61, "PRESS FIRE TO PLAY "
        COLOR COL_LTGREY
        PRS 22, 61, "                   "
        rts

.segment "RODATA"
vdc_cyc:    .byte RGBI_LTPURP, RGBI_LTRED, RGBI_LTYEL, RGBI_LTGREEN
            .byte RGBI_LTCYAN, RGBI_LTBLUE, RGBI_LTPURP, RGBI_WHITE
.segment "CODE"
vdc_cue_maze:
        MASK 2
        COLOR COL_LTRED
        PRS 21, 61, "MAZE ON CENTER     "
        PRS 22, 61, "SCREEN >>          "
        rts
vdc_cue_pin:
        MASK 2
        COLOR COL_LTGREY
        PRS 21, 61, "MAZE IS PAUSED     "
        PRS 22, 61, "                   "
        rts
