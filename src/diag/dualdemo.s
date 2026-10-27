; dualdemo.s - DUALDEMO (Tier 1): both screens in colour at once, a bouncing
; object on each (VIC hardware sprite, VDC character ball), and a live
; readout of joystick port 2, port 1 (paddle fire buttons) and paddle pots.
; Runs with interrupts off and ROMs in; never returns to BASIC.

.include "hw/c128.inc"
.include "hw/scr.inc"
.include "lib/macros.inc"

.importzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.importzp num, tmp, vdc_dead, frame, joy2, port1, potx, poty, video_pal
.import scr_at, scr_vat, set_color, print, printi, putc, fmt_hex8, fmt_dec
.import cls_vic, cls_vdc
.import vdc_wreg, vdc_rreg, vdc_setaddr, vdc_put
.import sys_init, wait_frame, detect_video, read_input, read_pots
.import vdc_basic_init, vdc_copy_rom_font

SPRDATA = $0E00         ; C128 sprite definition area in bank 0
BOXTOP  = 15            ; VDC ball box rows BOXTOP..BOXBOT
BOXBOT  = 23

.segment "ZEROPAGE"
sx:     .res 2          ; sprite x (9 bit)
sy:     .res 1
sdx:    .res 1          ; +1 / -1
sdy:    .res 1
scol:   .res 1
bx:     .res 1          ; VDC ball cell
by:     .res 1
bdx:    .res 1
bdy:    .res 1
bcol:   .res 1
oldj:   .res 1
oldp:   .res 1
redraw: .res 1
wptr:   .res 2
bits:   .res 1
wi:     .res 1

.segment "CODE"

start:
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
        lda #0
        sta vdc_dead

        MASK 1
        COLOR COL_WHITE
        jsr cls_vic
        PRS 0, 0, "DUALDEMO STARTING..."

        jsr detect_video
        jsr vdc_basic_init
        jsr vdc_copy_rom_font
        COLOR COL_WHITE
        jsr cls_vdc
        jsr cls_vic

        ; --- static text, both screens
        MASK 3
        COLOR COL_YELLOW
        PRS 0, 0, "DUALDEMO - BOTH SCREENS AT ONCE"
        MASK 2
        COLOR COL_LTGREY
        PRS 0, 42, "THIS IS THE 80-COLUMN (VDC) SCREEN"
        MASK 1
        PRS 24, 0, "80-COL SCREEN SHOULD SHOW A 2ND BALL"
        MASK 3
        COLOR COL_LTGREY
        PRS 1, 0, "FRAME"
        PRS 5, 0, "JOYSTICK PORT 2:"
        PRS 8, 0, "PORT 1 (PADDLE FIRE BUTTONS):"
        PRS 11, 0, "PORT 1 AS JOYSTICK:"
        PRS 13, 0, "PADDLE KNOBS (PORT 1): X     Y"
        COLOR COL_DKGREY
        PRS 7, 0, "MOVE STICK/PRESS FIRE: WORDS LIGHT UP"
        PRS 10, 0, "PRESS EACH PADDLE BUTTON IN TURN"

        ; colour bars: VIC row 3 (2 cols each), VDC row 3 (5 cols each)
        ldx #0
@cb:    txa
        pha
        jsr set_color
        MASK 1
        pla
        pha
        asl
        clc
        adc #4
        tax
        lda #3
        jsr scr_at
        lda #$A0
        jsr putc
        lda #$A0
        jsr putc
        MASK 2
        pla
        pha
        sta pr_vattr
        sta tmp+3
        asl
        asl
        adc tmp+3               ; x5
        tax
        lda #3
        jsr scr_at
        lda #<bar5
        ldx #>bar5
        jsr print
        pla
        tax
        inx
        cpx #16
        bne @cb

        ; --- sprite: ball in sprite 0
        ldx #62
        lda #0
:       sta SPRDATA,x
        dex
        bpl :-
        ldx #0
:       lda ballspr,x
        sta SPRDATA+3*3,x
        inx
        cpx #3*12
        bne :-
        lda #<(SPRDATA/64)
        sta $07F8
        lda #0
        sta VIC_SPRMC
        sta VIC_SPRXEXP
        sta VIC_SPRYEXP
        sta VIC_SPRPRI
        lda #1
        sta VIC_SPREN
        lda #100
        sta sx
        lda #0
        sta sx+1
        lda #120
        sta sy
        lda #1
        sta sdx
        sta sdy
        sta bdx
        sta bdy
        lda #COL_YELLOW
        sta scol
        lda #10
        sta bx
        lda #BOXTOP+1
        sta by
        lda #RGBI_WHITE
        sta bcol
        lda #$FF
        sta redraw

; ---------------------------------------------------------------- main loop
loop:
        jsr wait_frame
        jsr move_sprite
        jsr move_vball
        jsr read_input
        jsr read_pots
        ; frame counter
        MASK 3
        COLOR COL_WHITE
        lda #1
        ldx #6
        jsr scr_at
        lda frame
        sta num
        lda frame+1
        sta num+1
        lda #0
        sta num+2
        lda #5
        jsr fmt_dec
        jsr print
        ; pots
        COLOR COL_WHITE
        lda #13
        ldx #25
        jsr scr_at
        lda potx
        jsr pr3
        lda #13
        ldx #31
        jsr scr_at
        lda poty
        jsr pr3
        ; button words only when something changed
        lda joy2
        cmp oldj
        bne @chg
        lda port1
        cmp oldp
        bne @chg
        lda redraw
        beq loop
@chg:   lda #0
        sta redraw
        lda joy2
        sta oldj
        lda port1
        sta oldp
        ; port 2 joystick words, row 6
        lda joy2
        ldx #6
        ldy #0
        jsr words
        ; port 1 paddle fire words, row 9 (bits 2,3 only)
        lda port1
        ldx #9
        ldy #6
        jsr words
        ; port 1 joystick words, row 12
        lda port1
        ldx #12
        ldy #0
        jsr words
        jmp loop

; pr3: print A as 3 digits
pr3:
        sta num
        lda #0
        sta num+1
        sta num+2
        lda #3
        jsr fmt_dec
        jmp print

; words: A = bits, X = row, Y = first word index (0 = joystick set of 5,
; 5 = paddle set of 2). Lit words white, unlit dark grey.
words:
        sta bits
        stx pr_row
        sty wi
@w:     ldy wi
        lda wordcol,y
        bmi @done
        sta pr_col
        sta pr_vcol
        lda wordbit,y
        and bits
        beq @off
        lda #COL_WHITE
        bne @set
@off:   lda #COL_DKGREY
@set:   jsr set_color
        ldy wi
        lda wordlo,y
        ldx wordhi,y
        jsr print
        inc wi
        bne @w
@done:  rts

; move_sprite: bounce sprite 0 inside x 24..320, y 50..229
move_sprite:
        ; x
        lda sdx
        bmi @left
        inc sx
        bne :+
        inc sx+1
:       lda sx+1
        beq @xok
        lda sx
        cmp #<320
        bcc @xok
        lda #$FF
        sta sdx
        jsr sprcol
        jmp @xok
@left:  lda sx
        bne :+
        dec sx+1
:       dec sx
        lda sx+1
        bne @xok
        lda sx
        cmp #24
        bcs @xok
        lda #1
        sta sdx
        jsr sprcol
@xok:   ; y
        lda sdy
        bmi @up
        inc sy
        lda sy
        cmp #229
        bcc @yok
        lda #$FF
        sta sdy
        jsr sprcol
        jmp @yok
@up:    dec sy
        lda sy
        cmp #50
        bcs @yok
        lda #1
        sta sdy
        jsr sprcol
@yok:   lda sx
        sta VIC_SPR0X
        lda sx+1
        and #1
        sta VIC_SPRXMSB
        lda sy
        sta VIC_SPR0Y
        lda scol
        sta VIC_SPR0COL
        rts
sprcol: inc scol
        lda scol
        and #$0F
        bne :+
        lda #1
:       sta scol
        rts

; move_vball: VDC character ball in rows BOXTOP..BOXBOT, columns 0..79,
; one cell per frame across, one cell per 2 frames down.
move_vball:
        ; erase old cell (space)
        jsr vball_addr
        lda tmp+1
        ldy tmp
        jsr vdc_setaddr
        lda #$20
        jsr vdc_put
        ; x
        lda bx
        clc
        adc bdx
        sta bx
        beq @bx
        cmp #79
        bne @xok
@bx:    lda bdx
        eor #$FF
        clc
        adc #1
        sta bdx
        jsr vcolnext
@xok:   lda frame
        and #1
        bne @draw
        lda by
        clc
        adc bdy
        sta by
        cmp #BOXTOP
        beq @by
        cmp #BOXBOT
        bne @draw
@by:    lda bdy
        eor #$FF
        clc
        adc #1
        sta bdy
        jsr vcolnext
@draw:  jsr vball_addr
        lda tmp+1
        ldy tmp
        jsr vdc_setaddr
        lda #$51                ; filled circle
        jsr vdc_put
        lda tmp+1
        clc
        adc #$08
        ldy tmp
        jsr vdc_setaddr
        lda bcol
        jmp vdc_put

vcolnext:
        inc wi
        lda wi
        and #7
        tax
        lda brightcol,x
        sta bcol
        rts

; vball_addr: tmp = by*80 + bx
vball_addr:
        lda by
        sta tmp
        lda #0
        sta tmp+1
        ; *80 = *64 + *16
        ldx #4
:       asl tmp
        rol tmp+1
        dex
        bne :-
        lda tmp
        sta num
        lda tmp+1
        sta num+1
        asl tmp
        rol tmp+1
        asl tmp
        rol tmp+1
        lda tmp
        clc
        adc num
        sta tmp
        lda tmp+1
        adc num+1
        sta tmp+1
        lda tmp
        clc
        adc bx
        sta tmp
        bcc :+
        inc tmp+1
:       rts

.segment "RODATA"
ballspr:
        .byte $00,$7E,$00
        .byte $01,$FF,$80
        .byte $03,$FF,$C0
        .byte $07,$FF,$E0
        .byte $07,$FF,$E0
        .byte $07,$FF,$E0
        .byte $07,$FF,$E0
        .byte $07,$FF,$E0
        .byte $07,$FF,$E0
        .byte $03,$FF,$C0
        .byte $01,$FF,$80
        .byte $00,$7E,$00

w_up:   .byte "UP", 0
w_dn:   .byte "DOWN", 0
w_lf:   .byte "LEFT", 0
w_rt:   .byte "RIGHT", 0
w_fi:   .byte "FIRE", 0
w_px:   .byte "PADDLE-1 FIRE", 0
w_py:   .byte "PADDLE-2 FIRE", 0

wordlo: .byte <w_up, <w_dn, <w_lf, <w_rt, <w_fi, 0, <w_px, <w_py
wordhi: .byte >w_up, >w_dn, >w_lf, >w_rt, >w_fi, 0, >w_px, >w_py
wordbit: .byte $01, $02, $04, $08, $10, 0, $04, $08
brightcol: .byte RGBI_WHITE, RGBI_LTYEL, RGBI_LTCYAN, RGBI_LTGREEN, RGBI_LTRED, RGBI_LTPURP, RGBI_LTBLUE, RGBI_LTGREY
bar5:   .byte $A0,$A0,$A0,$A0,$A0,0
wordcol: .byte 2, 6, 12, 18, 25, $FF, 2, 18, $FF
