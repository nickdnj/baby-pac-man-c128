; vdctest.s - VDCTEST hardware diagnostic (Tier 1)
; Reports on BOTH screens: video standard, VDC status/version, R25/R28,
; VDC RAM size probe (16K vs 64K), CPU write/read speed, a 16-colour test
; on each chip, and a looping VDC RAM corruption test that uses only polled
; CPU writes and reads (no block copy/fill).
; Runs with interrupts off and ROMs in; never returns to BASIC.

.include "hw/c128.inc"
.include "hw/scr.inc"
.include "lib/macros.inc"

.importzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.importzp tcyc, num, tmp, vdc_busy, vdc_tmo, vdc_dead, video_pal, frame
.import scr_at, scr_vat, set_color, print, printi, putc, fmt_hex8, fmt_dec
.import cls_vic, cls_vdc, vic2rgbi
.import vdc_wreg, vdc_rreg, vdc_setaddr, vdc_put, vdc_get
.import sys_init, wait_frame, detect_video, timer_start, timer_stop
.import vdc_basic_init, vdc_copy_rom_font

.segment "ZEROPAGE"
addr:       .res 2
cnt:        .res 2
pat:        .res 1
patn:       .res 1
val:        .res 1
spin:       .res 1
rnd:        .res 1
cp:         .res 2
c0:         .res 1
c1:         .res 1
c2:         .res 1

.segment "BSS"
vstat:      .res 1
r25:        .res 1
r28:        .res 1
probe:      .res 4
ramsize:    .res 1      ; 16, 64, or 0 = unclear
cyc_seq:    .res 3
cyc_inl:    .res 3
cyc_rd:     .res 2
cyc_rnd:    .res 3
busy_save:  .res 2
passes:     .res 3
fails:      .res 3
checked:    .res 3
errors:     .res 3
rounderr:   .res 1
lasterr_a:  .res 2
lasterr_w:  .res 1
lasterr_r:  .res 1
round:      .res 3

.segment "CODE"

start:
        jsr sys_init
        lda #$04
        sta vicscr
        ; VIC: bank 0, screen $0400, ROM uppercase charset, display on
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
        sta VIC_BG0
        lda #COL_BLUE
        sta VIC_BORDER          ; phase marker: blue = starting

        lda #0
        sta vdc_dead
        sta vdc_tmo
        sta vdc_busy
        sta vdc_busy+1
        ldx #19
:       sta passes,x            ; clear counters (passes..round)
        dex
        bpl :-

        MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        PRS 0, 0, "VDCTEST - C128 DIAGNOSTIC FOR BABY PAC"
        COLOR COL_YELLOW
        PRS 2, 0, "STARTING... IF THIS LINE STAYS, THE VDC"
        PRS 3, 0, "CHECK IS STUCK. TELL NICK: STUCK AT VDC."

        jsr detect_video

        ; ---- VDC status, registers, RAM probe (before touching the screen)
        lda VDC_ADDR
        sta vstat
        ldx #25
        jsr vdc_rreg
        sta r25
        ldx #28
        jsr vdc_rreg
        sta r28
        jsr ram_probe

        ; ---- set up the VDC screen
        lda #COL_CYAN
        sta VIC_BORDER
        jsr vdc_basic_init
        jsr vdc_copy_rom_font
        lda #COL_WHITE
        jsr set_color
        jsr cls_vdc
        jsr cls_vic

        MASK 3
        COLOR COL_WHITE
        PRS 0, 0, "VDCTEST - C128 DIAGNOSTIC FOR BABY PAC"
        MASK 2
        COLOR COL_YELLOW
        PRS 0, 42, "80-COLUMN SCREEN (VDC 8563)"
        COLOR COL_WHITE
        PRS 1, 42, "IF YOU CAN READ THIS, THE VDC WORKS."
        PRS 2, 42, "SAME RESULTS ON THE 40-COL SCREEN."
        COLOR COL_LTGREY
        PRS 12, 0, "(VIC COLOUR BARS ARE ON THE 40-COL)"
        COLOR COL_YELLOW
        PRS 20, 0, "VDC RGBI COLOUR BARS 0-15 (CHECK ORDER):"

        jsr show_info
        jsr speed_test
        jsr show_speed
        jsr colour_test

        MASK 3
        COLOR COL_WHITE
        PRS 15, 0, "VDC RAM TEST (CPU ONLY, NO BLOCK OPS)"
        lda #COL_GREEN
        sta VIC_BORDER

; ---- corruption test loop (forever)
loop:
        INC24 round
        jsr show_counts
        lda #0
        sta rounderr
        jsr phase_a
        jsr phase_b
        lda rounderr
        bne @f
        INC24 passes
        jmp @d
@f:     INC24 fails
@d:     jsr show_counts
        jsr show_verdict
        jmp loop

; ------------------------------------------------------------------------
; ram_probe: set R28 bit 4 (64K RAM type), write 4 bytes 16K apart,
; read them back, restore R28. All four distinct = 64K.
ram_probe:
        bit vdc_dead
        bpl :+
        lda #0
        sta ramsize
        rts
:       lda r28
        ora #$10
        ldx #28
        jsr vdc_wreg
        ldx #0
@w:     lda probehi,x
        ldy #$80
        jsr vdc_setaddr
        lda probev,x
        jsr vdc_put
        inx
        cpx #4
        bne @w
        ldx #0
@r:     lda probehi,x
        ldy #$80
        jsr vdc_setaddr
        jsr vdc_get
        sta probe,x
        inx
        cpx #4
        bne @r
        lda r28
        ldx #28
        jsr vdc_wreg
        ; classify
        ldx #3
@c:     lda probe,x
        cmp probev,x
        bne @not64
        dex
        bpl @c
        lda #64
        sta ramsize
        rts
@not64: ; 16K if any location reads back a value written to another one
        ; (address aliasing); otherwise the result is unclear.
        ldx #3
@a1:    ldy #3
@a2:    lda probe,x
        cmp probev,y
        bne @a3
        lda #16
        sta ramsize
        rts
@a3:    dey
        bpl @a2
        dex
        bpl @a1
        lda #0
        sta ramsize
        rts

; ------------------------------------------------------------------------
show_info:
        MASK 3
        COLOR COL_LTGREY
        PRS 2, 0, "VIDEO: "
        COLOR COL_WHITE
        lda video_pal
        beq :+
        PRT "PAL "
        jmp :++
:       PRT "NTSC"
:       COLOR COL_LTGREY
        PRT "  VDC STATUS $"
        COLOR COL_WHITE
        PRHEX8 vstat
        COLOR COL_LTGREY
        PRT " VER "
        COLOR COL_WHITE
        lda vstat
        and #$07
        ora #$30
        jsr putc

        COLOR COL_LTGREY
        PRS 3, 0, "VDC R25 $"
        COLOR COL_WHITE
        PRHEX8 r25
        COLOR COL_LTGREY
        PRT "  R28 $"
        COLOR COL_WHITE
        PRHEX8 r28
        COLOR COL_LTGREY
        PRT "  (AT START)"

        PRS 4, 0, "VDC RAM: "
        lda vdc_dead
        bpl :+
        COLOR COL_RED
        PRT "NO REPLY"
        jmp @pr
:       lda ramsize
        cmp #64
        bne :+
        COLOR COL_GREEN
        PRT "64K"
        jmp @pr
:       cmp #16
        bne :+
        COLOR COL_GREEN
        PRT "16K"
        jmp @pr
:       COLOR COL_ORANGE
        PRT "UNCLEAR"
@pr:    COLOR COL_LTGREY
        PRT "  PROBE "
        COLOR COL_WHITE
        ldx #0
@pl:    txa
        pha
        lda probe,x
        jsr fmt_hex8
        jsr print
        lda #$20
        jsr putc
        pla
        tax
        inx
        cpx #4
        bne @pl
        COLOR COL_DKGREY
        PRS 5, 0, "(64K READS 11 22 33 44; 16K REPEATS)"
        rts

; ------------------------------------------------------------------------
; speed_test: all writes go to VDC $1000-$13FF (not displayed)
speed_test:
        lda #COL_PURPLE
        sta VIC_BORDER
        lda #0
        sta vdc_busy
        sta vdc_busy+1
        ; (1) sequential writes via the polled vdc_put routine
        lda #$10
        ldy #$00
        jsr vdc_setaddr
        jsr timer_start
        ldx #4
        ldy #0
        lda #$5A
@s1:    jsr vdc_put
        dey
        bne @s1
        dex
        bne @s1
        jsr timer_stop
        jsr savecyc
        .word cyc_seq
        ; (2) sequential writes, inline poll (best case for the game)
        lda #$10
        ldy #$00
        jsr vdc_setaddr
        jsr timer_start
        ldx #4
        ldy #0
        lda #$A5
@s2:    bit VDC_ADDR
        bpl @s2
        sta VDC_DATA
        dey
        bne @s2
        dex
        bne @s2
        jsr timer_stop
        jsr savecyc
        .word cyc_inl
        ; (3) sequential reads
        lda #$10
        ldy #$00
        jsr vdc_setaddr
        jsr timer_start
        ldx #4
        ldy #0
@s3:    jsr vdc_get
        dey
        bne @s3
        dex
        bne @s3
        jsr timer_stop
        jsr savecyc
        .word cyc_rd
        ; (4) 256 single-byte pokes at pseudo-random addresses
        lda #$37
        sta rnd
        jsr timer_start
        ldx #0
@s4:    lda rnd
        asl
        bcc :+
        eor #$1D
:       sta rnd
        tay
        txa
        and #$03
        ora #$10
        jsr vdc_setaddr
        lda rnd
        jsr vdc_put
        inx
        bne @s4
        jsr timer_stop
        jsr savecyc
        .word cyc_rnd
        lda vdc_busy
        sta busy_save
        lda vdc_busy+1
        sta busy_save+1
        rts

; savecyc: copy tcyc to the 3-byte address in the .word after the JSR
savecyc:
        pla
        sta tmp
        pla
        sta tmp+1
        ldy #1
        lda (tmp),y
        sta cp
        iny
        lda (tmp),y
        sta cp+1
        ldy #0
        lda tcyc
        sta (cp),y
        iny
        lda tcyc+1
        sta (cp),y
        iny
        lda tcyc+2
        sta (cp),y
        lda tmp
        clc
        adc #2
        tax
        lda tmp+1
        adc #0
        pha
        txa
        pha
        rts

show_speed:
        MASK 3
        COLOR COL_YELLOW
        PRS 6, 0, "VDC SPEED (CPU CYCLES AT 1 MHZ):"
        COLOR COL_LTGREY
        PRS 7, 0, " 1K WRITES POLLED"
        COLOR COL_WHITE
        ldx #0
        jsr pr_cyc1k
        COLOR COL_LTGREY
        PRS 8, 0, " 1K WRITES INLINE"
        COLOR COL_WHITE
        ldx #3
        jsr pr_cyc1k
        COLOR COL_LTGREY
        PRS 9, 0, " 1K READS  POLLED"
        COLOR COL_WHITE
        ldx #6
        jsr pr_cyc1k
        COLOR COL_LTGREY
        PRS 10, 0, " 256 RAND POKES"
        COLOR COL_WHITE
        PRDEC24 cyc_rnd, 6
        COLOR COL_LTGREY
        PRT " ="
        COLOR COL_WHITE
        lda cyc_rnd+1
        sta num
        lda cyc_rnd+2
        sta num+1
        lda #0
        sta num+2
        lda #4
        jsr fmt_dec
        jsr print
        COLOR COL_LTGREY
        PRT "/EA"
        PRS 11, 0, " BUSY WAITS "
        COLOR COL_WHITE
        PRDEC16 busy_save, 5
        COLOR COL_LTGREY
        PRT "  TIMEOUTS "
        COLOR COL_WHITE
        PRDEC8 vdc_tmo, 3
        rts

; pr_cyc1k: X = offset of a 3-byte cycle count (from cyc_seq) for 1024
; operations; prints "nnnnnn =nn.n/EA"
pr_cyc1k:
        lda cyc_seq,x
        sta c0
        sta num
        lda cyc_seq+1,x
        sta c1
        sta num+1
        lda cyc_seq+2,x
        sta c2
        sta num+2
        lda #6
        jsr fmt_dec
        jsr print
        COLOR COL_LTGREY
        PRT " ="
        COLOR COL_WHITE
        ; integer part = cycles >> 10
        lda c2
        sta num+1
        lda c1
        lsr num+1
        ror
        lsr num+1
        ror
        sta num
        lda #0
        sta num+2
        lda #3
        jsr fmt_dec
        jsr print
        lda #$2E
        jsr putc
        ; tenths = ((cycles & $3FF) * 10) >> 10
        lda c1
        and #$03
        sta c1
        asl c0                  ; x2
        rol c1
        lda c0
        sta num
        lda c1
        sta num+1
        asl c0                  ; x8
        rol c1
        asl c0
        rol c1
        lda c0
        clc
        adc num
        lda c1
        adc num+1               ; hi byte of x10
        lsr
        lsr
        ora #$30
        jsr putc
        COLOR COL_LTGREY
        PRT "/EA"
        rts

; ------------------------------------------------------------------------
colour_test:
        ; VIC: rows 12-14, blocks of 2 columns starting at column 4
        MASK 1
        COLOR COL_YELLOW
        PRS 12, 0, "VIC:"
        ldx #0
@v:     txa
        pha
        jsr set_color
        pla
        pha
        asl
        clc
        adc #4
        tax
        lda #12
        jsr scr_at
        lda #$A0
        jsr putc
        lda #$A0
        jsr putc
        pla
        tax
        inx
        cpx #16
        bne @v
        COLOR COL_LTGREY
        PRS 13, 4, "0 1 2 3 4 5 6 7 8 9 A B C D E F"
        PRS 14, 4, "BKWHRDCYPUGNBLYEORBRLRG1G2LGLBG3"

        ; VDC: rows 21-24, 16 bars of 5 columns
        MASK 2
        ldx #0
@d:     txa
        pha
        sta pr_vattr
        lda vdcbarcol,x
        tax
        lda #21
        jsr scr_at
        lda #<bar5
        ldx #>bar5
        jsr print
        lda #22
        sta pr_row
        pla
        pha
        tax
        lda vdcbarcol,x
        sta pr_vcol
        lda #<bar5
        ldx #>bar5
        jsr print
        pla
        tax
        inx
        cpx #16
        bne @d
        lda #RGBI_LTGREY
        sta pr_vattr
        lda #23
        ldx #0
        jsr scr_at
        lda #<vdcnum
        ldx #>vdcnum
        jsr print
        lda #24
        ldx #0
        jsr scr_at
        lda #<vdcnames
        ldx #>vdcnames
        jsr print
        rts

; ------------------------------------------------------------------------
; phase_a: pattern test of VDC $1000-$1FFF (never displayed)
phase_a:
        MASK 3
        COLOR COL_LTGREY
        PRS 19, 0, " PHASE A: PATTERNS $1000-$1FFF     "
        lda #0
        sta patn
@pat:   ldx patn
        lda patterns,x
        sta pat
        ; write 4K
        lda #$10
        ldy #$00
        jsr vdc_setaddr
        lda #$00
        sta addr
        lda #$10
        sta addr+1
@wl:    jsr patbyte
        jsr vdc_put
        inc addr
        bne @wl
        jsr progress
        inc addr+1
        lda addr+1
        cmp #$20
        bne @wl
        ; read back 4K
        lda #$10
        ldy #$00
        jsr vdc_setaddr
        lda #$00
        sta addr
        lda #$10
        sta addr+1
@rl:    jsr vdc_get
        sta val
        jsr patbyte
        cmp val
        beq :+
        jsr record_err
:       INC24 checked
        inc addr
        bne @rl
        jsr progress
        inc addr+1
        lda addr+1
        cmp #$20
        bne @rl
        inc patn
        lda patn
        cmp #5
        bne @pat
        rts

; patbyte: expected byte for pattern pat at addr (pattern $01 = address)
patbyte:
        lda pat
        cmp #$01
        bne :+
        lda addr
        eor addr+1
:       rts

; phase_b: non-destructive check of the live areas $0000-$0FFF and
; $2000-$3FFF: read, write complement, read back, restore original.
phase_b:
        MASK 3
        COLOR COL_LTGREY
        PRS 19, 0, " PHASE B: LIVE AREAS INV/RESTORE   "
        lda #$00
        sta addr
        sta addr+1
@lp:    lda addr+1
        ldy addr
        jsr vdc_setaddr
        jsr vdc_get
        sta val
        lda addr+1
        ldy addr
        jsr vdc_setaddr
        lda val
        eor #$FF
        jsr vdc_put
        lda addr+1
        ldy addr
        jsr vdc_setaddr
        jsr vdc_get
        eor #$FF
        cmp val
        beq @ok
        eor #$FF
        pha
        lda val
        eor #$FF
        sta pat                 ; expected
        pla
        sta tmp
        jsr record_err2
@ok:    lda addr+1
        ldy addr
        jsr vdc_setaddr
        lda val
        jsr vdc_put
        INC24 checked
        inc addr
        bne @lp
        jsr progress
        inc addr+1
        lda addr+1
        cmp #$10
        bne :+
        lda #$20                ; skip $1000-$1FFF (phase A)
        sta addr+1
:       cmp #$40
        bne @lp
        rts

; record_err: expected in A, read in val (phase A)
record_err:
        sta lasterr_w
        lda val
        sta lasterr_r
        jmp rec_common
; record_err2: expected in pat, read in tmp (phase B)
record_err2:
        lda pat
        sta lasterr_w
        lda tmp
        sta lasterr_r
rec_common:
        lda addr
        sta lasterr_a
        lda addr+1
        sta lasterr_a+1
        INC24 errors
        lda #1
        sta rounderr
        lda #COL_RED
        sta VIC_BORDER
        rts

; progress: VIC-only live address + spinner so a running test is visible
progress:
        lda pr_mask
        pha
        lda pr_color
        pha
        MASK 1
        COLOR COL_WHITE
        lda #19
        ldx #36
        jsr scr_at
        lda addr+1
        jsr fmt_hex8
        jsr print
        inc spin
        lda spin
        and #3
        tax
        lda spinch,x
        jsr putc
        pla
        jsr set_color
        pla
        sta pr_mask
        rts

show_counts:
        MASK 3
        COLOR COL_LTGREY
        PRS 16, 0, " ROUND "
        COLOR COL_WHITE
        PRDEC24 round, 6
        COLOR COL_GREEN
        PRT " PASS "
        PRDEC24 passes, 6
        COLOR COL_RED
        PRT " FAIL "
        PRDEC24 fails, 5
        COLOR COL_LTGREY
        PRS 17, 0, " BYTES CHECKED "
        COLOR COL_WHITE
        PRDEC24 checked, 8
        COLOR COL_LTGREY
        PRT " ERR "
        COLOR COL_WHITE
        PRDEC24 errors, 7
        COLOR COL_LTGREY
        PRS 18, 0, " LAST ERROR AT $"
        COLOR COL_WHITE
        PRHEX8 lasterr_a+1
        PRHEX8 lasterr_a
        COLOR COL_LTGREY
        PRT " WROTE $"
        COLOR COL_WHITE
        PRHEX8 lasterr_w
        COLOR COL_LTGREY
        PRT " READ $"
        COLOR COL_WHITE
        PRHEX8 lasterr_r
        rts

show_verdict:
        lda vdc_dead
        bpl :+
        lda #COL_RED
        ldx #<vtxt_dead
        ldy #>vtxt_dead
        jmp @go
:       lda errors
        ora errors+1
        ora errors+2
        beq :+
        lda #COL_RED
        ldx #<vtxt_err
        ldy #>vtxt_err
        jmp @go
:       lda #COL_GREEN
        ldx #<vtxt_ok
        ldy #>vtxt_ok
@go:    stx addr
        sty addr+1
        jsr set_color
        MASK 1
        lda #21
        ldx #0
        jsr scr_at
        lda addr
        ldx addr+1
        jsr print
        MASK 2
        lda #4
        ldx #41
        jsr scr_at
        lda addr
        ldx addr+1
        jsr print
        MASK 1
        COLOR COL_LTGREY
        PRS 22, 0, "NO 80-COL MONITOR? ALL RESULTS ARE HERE"
        PRS 23, 0, "ON THE 40-COL SCREEN. RUN/STOP+RESTORE"
        PRS 24, 0, "OR RESET TO EXIT. PHOTO BOTH SCREENS."
        MASK 2
        COLOR COL_LTGREY
        PRS 6, 42, "RESET OR RUN/STOP+RESTORE TO EXIT."
        PRS 7, 42, "PLEASE PHOTOGRAPH BOTH SCREENS."
        rts

.segment "RODATA"
probehi:    .byte $1F, $5F, $9F, $DF
probev:     .byte $11, $22, $33, $44
patterns:   .byte $55, $AA, $00, $FF, $01
spinch:     .byte $2D, $4E, $5D, $4D     ; - / | \ (graphics set)
bar5:       .byte $A0,$A0,$A0,$A0,$A0,0
vdcbarcol:
.repeat 16, I
            .byte I*5
.endrepeat
vtxt_dead:  .byte "VDC NOT RESPONDING: 80-COL CANNOT WORK ", 0
vtxt_err:   .byte "VDC RAM ERRORS SEEN - PHOTO THIS SCREEN", 0
vtxt_ok:    .byte "ALL VDC CHECKS OK SO FAR (KEEP RUNNING)", 0
vdcnum:     .byte " 0   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  ", 0
vdcnames:   .byte "BLACKDGREYDBLUELBLUEDGRENLGRENDCYANLCYANDRED LRED DPURPLPURPDYEL LYEL LGREYWHITE", 0
