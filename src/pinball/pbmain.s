; pbmain.s - PINBALL (Tier 2): the VDC pinball on its own.
; Built twice: table v1 and (-D TABLE2) the v2 "faithful layout" table.
; 80-col screen: table + panels. 40-col screen: score and status.
; Balls launch from the top chutes (alternating); a drained ball relaunches
; after 2 s. Runs until reset. ROMs are banked out after start-up.

.include "hw/c128.inc"
.include "hw/scr.inc"
.include "lib/macros.inc"

.importzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.importzp num, tmp, vdc_dead, frame, joy2, port1, tcyc
.importzp pb_state, pb_score, pb_energ, pb_fruit, pb_bonus, pb_nudges, pb_tgts
.import scr_at, scr_vat, set_color, print, printi, putc, fmt_dec
.import cls_vic, cls_vdc
.import timer_start, timer_stop, sys_init, wait_frame, read_input, ram_vectors, vdc_basic_init
.import pb_setup, pb_launch, pb_frame, pb_draw_panels, pb_flippers_rest
.import pb_reset_lights, chr_ram

NTSC_FRAME = 17045             ; 1022727 Hz / 60 (approx.)

.segment "ZEROPAGE"
ball:   .res 2
chute:  .res 1
wait:   .res 1
wmax:   .res 2
vs_old: .res 6
vs_force: .res 1
wshow:  .res 2
wpeak:  .res 2          ; highest pb_frame cycle count since start
wslow:  .res 2          ; frames whose pb_frame work exceeded one NTSC frame

.segment "CODE"
start:
        sei
        cld
        ; copy ROM font glyphs 0-63 (char ROM $D000, MMU config $01) into
        ; chr_ram. This loop must stay below $4000 (it is at the start).
        ldx #0
@f:     lda #MMU_CFG_CHR
        sta MMU_CR
        lda $D000,x
        ldy #MMU_CFG_RAM
        sty MMU_CR
        sta chr_ram,x
        lda #MMU_CFG_CHR
        sta MMU_CR
        lda $D100,x
        ldy #MMU_CFG_RAM
        sty MMU_CR
        sta chr_ram+256,x
        inx
        bne @f
        lda #MMU_CFG_RAM
        sta MMU_CR
        ldx #$FF
        txs
        jsr ram_vectors
        jsr sys_init
        lda #$04
        sta vicscr
        lda CIA2_PRA
        ora #$03
        sta CIA2_PRA
        lda #$14
        sta VIC_MEMPTR
        lda #$1B
        sta VIC_CR1
        lda #$08
        sta VIC_CR2
        lda #0
        sta VIC_SPREN
        sta VIC_BORDER
        sta VIC_BG0
        sta vdc_dead

        MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        PRS 0, 0, "BABY PAC-MAN  PINBALL TEST (TIER 2)"
        COLOR COL_YELLOW
        PRS 2, 0, "SETTING UP THE 80-COLUMN SCREEN..."

        jsr vdc_basic_init
        lda #COL_LTGREY
        jsr set_color
        jsr cls_vdc
        jsr pb_setup
        jsr pb_draw_panels
        jsr pb_reset_lights

        bit vdc_dead
        bpl ok
        ; VDC not answering: say so, keep the border flashing
        MASK 1
        COLOR COL_RED
        PRS 4, 0, "80-COL CHIP (VDC) IS NOT RESPONDING."
        PRS 5, 0, "THE PINBALL NEEDS IT. RUN VDCTEST."
:       jsr wait_frame
        lda frame
        lsr
        lsr
        lsr
        and #1
        ora #COL_BLACK
        eor #COL_RED
        sta VIC_BORDER
        jmp :-

ok:     MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        PRS 0, 0, "BABY PAC-MAN  PINBALL TEST (TIER 2)"
        COLOR COL_YELLOW
        PRS 2, 2, "<< THE PINBALL IS ON THE"
        PRS 3, 2, "   80-COLUMN SCREEN"
        COLOR COL_LTGREY
        PRS 6, 2, "SCORE"
        PRS 8, 2, "BALL"
.ifdef TABLE2
        PRS 10, 2, "ENERGIZERS EARNED"
        PRS 11, 2, "PAC-MAN TARGETS     /8"
        PRS 12, 2, "FRUITS LANE (FRUIT +)"
.else
        PRS 10, 2, "ENERGIZERS LIT"
        PRS 11, 2, "FRUIT LANES LIT"
.endif
        PRS 14, 2, "FLIPPERS:"
        PRS 17, 2, "LEFT FLIPPER  = LEFT PADDLE BUTTON"
        PRS 18, 2, "RIGHT FLIPPER = RIGHT PADDLE BUTTON"
        PRS 19, 2, "(OR JOYSTICK PORT 2 LEFT / RIGHT)"
        COLOR COL_DKGREY
        PRS 23, 2, "RESET BUTTON TO EXIT"

        lda #1
        sta ball
        lda #0
        sta ball+1
        sta chute
        sta wpeak
        sta wpeak+1
        sta wslow
        sta wslow+1

newball:
        lda #1
        sta vs_force
        jsr pb_reset_lights
        lda chute
        jsr pb_launch
        MASK 1
        COLOR COL_WHITE
        PRS 21, 2, "GET READY...          "
play:   jsr wait_frame
        jsr read_input
        jsr timer_start
        jsr pb_frame
        pha
        jsr meas_end
        pla
        cmp #2
        beq drained
        cmp #1
        bne :+
        lda frame
        and #63
        bne :+
        MASK 1
        COLOR COL_GREEN
        PRS 21, 2, "BALL IN PLAY          "
:       jsr vic_status
        jmp play

drained:
        MASK 1
        COLOR COL_LTRED
        PRS 21, 2, "DRAINED! NEXT BALL... "
        jsr pb_flippers_rest
        lda #120
        sta wait
:       jsr wait_frame
        jsr read_input
        jsr vic_status
        dec wait
        bne :-
        inc ball
        bne :+
        inc ball+1
:       lda chute
        eor #1
        sta chute
        jmp newball

; work cycle measurement: timer started right after wait_frame, read just
; before the next one. Max over each 64-frame window is shown.
meas_end:
        jsr timer_stop          ; A/X = cycles (16-bit; tcyc+2 = overflow)
        ldy tcyc+2
        beq :+
        lda #$FF
        tax
:       cpx wmax+1
        bcc @nm
        bne @m
        cmp wmax
        bcc @nm
@m:     sta wmax
        stx wmax+1
@nm:    cpx wpeak+1             ; all-time peak
        bcc @np
        bne @p
        cmp wpeak
        bcc @np
@p:     sta wpeak
        stx wpeak+1
@np:    cpx #>NTSC_FRAME        ; over one frame of work?
        bcc @ns
        bne @s
        cmp #<NTSC_FRAME
        bcc @ns
@s:     inc wslow
        bne @ns
        inc wslow+1
@ns:    lda frame
        and #63
        beq :+
        rts
:       lda wmax
        sta wshow
        lda wmax+1
        sta wshow+1
        lda #0
        sta wmax
        sta wmax+1
        MASK 1
        COLOR COL_DKGREY
        PRS 22, 2, "PINBALL MAX       CYCLES/FRAME"
        COLOR COL_WHITE
        lda #22
        ldx #14
        jsr scr_at
        lda wshow
        sta num
        lda wshow+1
        sta num+1
        lda #0
        sta num+2
        lda #5
        jsr fmt_dec
        jsr print
        COLOR COL_DKGREY
        PRS 24, 2, "PEAK       SLOW FRAMES"
        COLOR COL_WHITE
        lda #24
        ldx #7
        jsr scr_at
        lda wpeak
        sta num
        lda wpeak+1
        sta num+1
        lda #0
        sta num+2
        lda #5
        jsr fmt_dec
        jsr print
        lda #24
        ldx #25
        jsr scr_at
        lda wslow
        sta num
        lda wslow+1
        sta num+1
        lda #0
        sta num+2
        lda #5
        jsr fmt_dec
        jsr print
        rts

; vic_status: score, ball, tally, flipper buttons on the 40-col screen
vic_status:
        lda pb_score
        eor vs_old
        sta tmp+3
        lda pb_score+1
        eor vs_old+1
        ora tmp+3
        sta tmp+3
        lda pb_energ
        eor vs_old+2
        ora tmp+3
        sta tmp+3
        lda pb_fruit
        eor vs_old+3
        ora tmp+3
        sta tmp+3
        lda ball
        eor vs_old+4
        ora tmp+3
        sta tmp+3
        lda port1
        ora joy2
        and #$0C
        eor vs_old+5
        ora tmp+3
        ora vs_force
        bne :+
        rts
:       lda #0
        sta vs_force
        lda pb_score
        sta vs_old
        lda pb_score+1
        sta vs_old+1
        lda pb_energ
        sta vs_old+2
        lda pb_fruit
        sta vs_old+3
        lda ball
        sta vs_old+4
        lda port1
        ora joy2
        and #$0C
        sta vs_old+5
        MASK 1
        COLOR COL_WHITE
        lda #6
        ldx #20
        jsr scr_at
        lda pb_score
        sta num
        lda pb_score+1
        sta num+1
        lda pb_score+2
        sta num+2
        lda #8
        jsr fmt_dec
        jsr print
        lda #8
        ldx #22
        jsr scr_at
        lda ball
        sta num
        lda ball+1
        sta num+1
        lda #0
        sta num+2
        lda #6
        jsr fmt_dec
        jsr print
        lda #10
        ldx #25
        jsr scr_at
        lda pb_energ
        jsr pr3
.ifdef TABLE2
        lda #11
        ldx #19
        jsr scr_at
        lda pb_tgts
        jsr pr3
        lda #12
        ldx #25
        jsr scr_at
        lda pb_fruit
        jsr pr3
.else
        lda #11
        ldx #25
        jsr scr_at
        lda pb_fruit
        jsr pr3
.endif
        ; flipper indicators
        lda port1
        ora joy2
        sta tmp+2
        and #$04
        beq :+
        lda #COL_YELLOW
        jmp :++
:       lda #COL_DKGREY
:       jsr set_color
        PRS 14, 12, "[LEFT]"
        lda tmp+2
        and #$08
        beq :+
        lda #COL_YELLOW
        jmp :++
:       lda #COL_DKGREY
:       jsr set_color
        PRS 14, 20, "[RIGHT]"
        rts

pr3:    sta num
        lda #0
        sta num+1
        sta num+2
        lda #3
        jsr fmt_dec
        jmp print
