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
.import pb_logo_tint, pb_sfx_tick, mz_jingle_start, mz_jingle_tick, mz_wait_tick
.import sb_init, sb_show, sb_tick, sb_hide, sb_remove
.ifdef AUTOPLAY
.import timer_start, timer_stop, pb_check_table, chk_bad, chk_n
.import vdc_setaddr, vdc_get, row80lo, row80hi
.importzp tcyc
.endif

VCHR = $C800
IDLE_FRAMES = 3600              ; 60 s

; AUTOPLAY (test) builds only: whole-frame work cycles per loop, measured
; with the CIA1 cycle timer from the end of wait_frame to the next call
; (cy_pk: 24-bit peaks; 0 maze play, 1 pinball visit, 2 to_pinball handoff,
; 3 READY!, 4 back (pinball -> maze); cy_slow: frames over 17,045 in the
; maze (0) and pinball (1) loops). Compiles to nothing in shipped builds.
.ifdef AUTOPLAY
.macro CYEND n
        ldx #n
        jsr cy_end
.endmacro
.macro CYBEG
        jsr cy_beg
.endmacro
.else
.macro CYEND n
.endmacro
.macro CYBEG
.endmacro
.endif

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
.ifdef AUTOPLAY
        lda #0
        sta cy_run
        sta chk_bad
        sta chk_bad+1
        sta chk_n
        sta dmp_req
        sta wt_pk
        sta wt_pk+1
        sta sb_pk
        sta sb_pk+1
        ldx #25
:       sta cy_pk,x             ; (cy_pk, cy_slow, cy_n are contiguous)
        dex
        bpl :-
.endif
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
        jsr sb_init             ; VDC status board template (board.s)
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
        jsr sb_show             ; status board over the dimmed table
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
:       CYEND 3
        jsr wait_frame
        CYBEG
        jsr read_input
        jsr mz_jingle_tick
        jsr sb_tick
        dec cnt
        bne :-
        jsr mz_msg_clear
        jsr hint
        lda #0
        sta gotime
        jsr idle_reset
        CYEND 3

play:   CYEND 0
        jsr wait_frame
        CYBEG
        jsr read_input
        jsr pb_sfx_tick
        jsr idle_tick
        bcc :+
        CYEND 0
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
:
.ifdef AUTOPLAY
        jsr sb_timed            ; test builds: sb_tick, timed
        lda dmp_req             ; test builds: VDC row read back on request
        beq :+
        jsr dmp_row
:
.else
        jsr sb_tick             ; status board: one field at most
.endif
        lda frame
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
        CYEND 0
        CYBEG
        jsr mz_freeze
        jsr sb_hide             ; table codes back (pb_undim: attributes)
        jsr pb_undim
        jsr pb_reset_lights
        jsr vdc_cue_pin
        lda mz_chute
        jsr pb_launch
        CYEND 2
.ifdef AUTOPLAY
        lda #0                  ; test builds: the table must be intact
        jsr pb_check_table
.endif
pin:    CYEND 1
        jsr wait_frame
        CYBEG
.ifdef AUTOPLAY
        jsr wt_rd               ; test builds: time mz_wait_tick alone
        sta wt_t0
        stx wt_t0+1
.endif
        jsr mz_wait_tick        ; waiting ghosts, energizer counter (VIC)
.ifdef AUTOPLAY
        jsr wt_rd
        sta wt_t1
        stx wt_t1+1
        lda wt_t0               ; (timer counts down)
        sec
        sbc wt_t1
        sta wt_t1
        lda wt_t0+1
        sbc wt_t1+1
        cmp wt_pk+1
        bcc :++
        bne :+
        ldx wt_t1
        cpx wt_pk
        bcc :++
:       sta wt_pk+1
        lda wt_t1
        sta wt_pk
:
.endif
        jsr read_input
        jsr idle_tick
        bcc :+
        CYEND 1
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
        CYEND 1
        CYBEG
        jsr pb_flippers_rest
        jsr pb_dim
        jsr vdc_cue_maze
        jsr sb_show
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
        CYEND 4
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
        CYEND 0
        lda #4
        jsr pb_sfx
        lda #0
        sta cnt
:       jsr wait_frame
        lda cnt
        jsr mz_death_anim
        jsr sb_tick
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
        CYEND 0
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
        jsr sb_tick
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
        CYEND 5
        jsr sb_remove           ; board off, the table stays dimmed
.ifdef AUTOPLAY
        lda #1                  ; test builds: dimmed table intact
        jsr pb_check_table
.endif
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
.ifdef AUTOTOUR
        clc                     ; the tour test never idles out
        rts
.endif
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

.ifdef AUTOPLAY
.segment "BSS"
.export cy_pk, cy_slow, cy_n
cy_run: .res 1
cy_pk:  .res 18         ; 6 x 24-bit peaks
cy_slow: .res 4         ; 2 x 16-bit
cy_n:   .res 4          ; frames measured: maze, pinball (16-bit)
.segment "CODE"
cy_beg: lda #1
        sta cy_run
        jmp timer_start
; cy_end: X = slot. Stops a running measurement and keeps the peak.
cy_end: lda cy_run
        bne :+
        rts
:       lda #0
        sta cy_run
        stx cy_x
        jsr timer_stop
        lda cy_x
        asl
        adc cy_x
        tax                     ; X = slot * 3
        lda tcyc+2
        cmp cy_pk+2,x
        bcc @nopk
        bne @pk
        lda tcyc+1
        cmp cy_pk+1,x
        bcc @nopk
        bne @pk
        lda tcyc
        cmp cy_pk,x
        bcc @nopk
@pk:    lda tcyc
        sta cy_pk,x
        lda tcyc+1
        sta cy_pk+1,x
        lda tcyc+2
        sta cy_pk+2,x
@nopk:  lda cy_x
        cmp #2
        bcs @x
        asl
        tax
        inc cy_n,x
        bne :+
        inc cy_n+1,x
:       lda tcyc+2              ; over one NTSC frame (17,045)?
        bne @slow
        lda tcyc+1
        cmp #>17045
        bcc @x
        bne @slow
        lda tcyc
        cmp #<17045
        bcc @x
@slow:  inc cy_slow,x
        bne @x
        inc cy_slow+1,x
@x:     rts
.segment "BSS"
cy_x:   .res 1
wt_t0:  .res 2
wt_t1:  .res 2
.segment "CODE"
; sb_timed: sb_tick, keeping the most cycles one call took in sb_pk
sb_timed:
        jsr wt_rd
        sta wt_t0
        stx wt_t0+1
        jsr sb_tick             ; status board: one field at most
        jsr wt_rd
        sta wt_t1
        stx wt_t1+1
        lda wt_t0
        sec
        sbc wt_t1
        sta wt_t1
        lda wt_t0+1
        sbc wt_t1+1
        cmp sb_pk+1
        bcc @x
        bne :+
        ldx wt_t1
        cpx sb_pk
        bcc @x
:       sta sb_pk+1
        lda wt_t1
        sta sb_pk
@x:     rts
; wt_rd: CIA1 timer A -> A lo, X hi (re-read if the high byte ticked)
wt_rd:  ldx CIA1_TAHI
        lda CIA1_TALO
        cpx CIA1_TAHI
        bne wt_rd
        rts
.segment "BSS"
.export wt_pk, dmp_req, dmp_c, dmp_a, sb_pk
sb_pk:  .res 2          ; most cycles one sb_tick took (+ ~35 for the reads)
dmp_req: .res 1         ; poke VDC row + 1: dmp_c / dmp_a get its columns
dmp_c:  .res 30         ; 25-54 (the status board), then dmp_req = 0
dmp_a:  .res 30
.segment "CODE"
dmp_row:
        ldx dmp_req
        dex
        lda row80lo,x
        clc
        adc #25
        sta dmp_t
        lda row80hi,x
        adc #0
        sta dmp_t+1
        ldy dmp_t
        jsr vdc_setaddr
        ldx #0
:       jsr vdc_get
        sta dmp_c,x
        inx
        cpx #30
        bne :-
        lda dmp_t+1
        clc
        adc #8
        ldy dmp_t
        jsr vdc_setaddr
        ldx #0
:       jsr vdc_get
        sta dmp_a,x
        inx
        cpx #30
        bne :-
        lda #0
        sta dmp_req
        rts
.segment "BSS"
dmp_t:  .res 2
wt_pk:  .res 2          ; most cycles one mz_wait_tick took (+ ~20 for the reads)
.segment "CODE"
.endif
