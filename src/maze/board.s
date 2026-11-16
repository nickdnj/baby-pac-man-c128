; board.s - maze status board on the 80-column (VDC) screen.
; While Pac-Man plays the maze on the VIC, the dimmed pinball table carries a
; live board over its middle (VDC rows 4-17, columns 25-54, inside the
; monitor's safe area): the four ghosts with their state (SCATTER / CHASE /
; BLUE with a countdown bar, flashing by hardware blink in the last 2 s /
; EYES / HOME), a dot thermometer (5 % per cell) with the dots left, the lives
; and the fruit level (IN MAZE blinks while a fruit is out).
;
; Glyphs: none new. The ghost and Pac-Man icons, the double rule and the
; fruit icons are the table's own art (pan_codes / vis_codes), recoloured
; through VDC attributes; bars are reverse-video spaces.
;
; Cost: sb_tick runs once per maze frame and does at most ONE of: half a
; template row (30 bytes), or one live field whose state changed since it
; was drawn (shadow copies, ~40-50 VDC bytes at most). It skips the frames
; where main3 runs mz_hud (frame & 7 = 0) and pb_show_score (frame & 31 = 4).
; sb_hide puts the table back (screen codes from the table's own `disp`; the
; caller's pb_undim rewrites the attributes); sb_remove also writes the
; dimmed attributes (game over -> title, table stays dimmed).
;
; Built with -D NOBOARD (the v1-table builds): every entry point is an rts.

.include "hw/c128.inc"
.include "hw/scr.inc"

.export sb_init, sb_show, sb_tick, sb_hide, sb_remove

.ifdef NOBOARD
.segment "CODE"
sb_init:
sb_show:
sb_tick:
sb_hide:
sb_remove:
        rts
.else

.importzp frame, tmp, vdc_dead, mz_lives, mz_dotsleft, gstate, fright, chase
.import gblue, fr_t, fr_kind, NDOTS
.import row80lo, row80hi, vdc_setaddr
.import pan_codes, pan_attrs, vis_codes
.import pb_restore_row, pbr_c0, pbr_n, pbr_dim

SB_ROW0 = 4                     ; first VDC row of the board
SB_ROWS = 14
SB_TC0  = 5                     ; first table column (VDC column 25)
SB_W    = 30
SB_VC0  = 20 + SB_TC0
SB_HALF = SB_ROWS * 2           ; template steps (codes, attrs per row)
NFLD    = 12

A_ALT   = $80                   ; attribute bits: bank 1 (bold font, panel art)
A_REV   = $40
A_BLINK = $10

; board columns (b) -> VDC column SB_VC0 + b
B_ICON  = 1                     ; ghost icon 3x2
B_NAME  = 5
B_WORD  = 13                    ; state word (7)
B_BAR   = 13                    ; blue countdown bar (12) under the word
BARLEN  = 12
B_TH    = 6                     ; thermometer, 20 cells, 2 rows
THLEN   = 20
B_PCT   = 26
B_LIVES = 7                     ; 3 Pac-Man icons 3x2, 1 column apart (11)
B_FRUIT = 26                    ; fruit icon (1 cell)
B_INMZ  = 20                    ; IN MAZE (7)

.segment "BSS"
tpl_c:  .res SB_ROWS * SB_W     ; template: screen codes
tpl_a:  .res SB_ROWS * SB_W     ;           attributes
sb_step: .res 1                 ; template step 0..SB_HALF-1; SB_HALF = live; $FF = off
sb_hi:  .res 1                  ; board rows touched on the VDC (to restore)
sb_fld: .res 1                  ; next field to check (round robin)
shadow: .res NFLD               ; what each live field shows ($FF = unknown)
sb_bl:  .res 1                  ; blue bar this frame: cells | $80 flashing
sb_dl:  .res 1                  ; mz_dotsleft (low byte) the bar was worked out for
sb_pct: .res 1                  ; percentage eaten (for the bar)
sb_th:  .res 1                  ; thermometer cells (0..20)
va_lo:  .res 1
va_hi:  .res 1
sb_t:   .res 1
sb_v:   .res 1
sb_buf: .res 12
dv_lo:  .res 1                  ; division
dv_hi:  .res 1
dv_r:   .res 2

.segment "CODE"

; ------------------------------------------------------------------------
; sb_init: build the template (once, after pb_setup). Board off.
sb_init:
        lda #$FF
        sta sb_step
        lda #0
        sta sb_hi
        sta sb_fld
        ldx #0
:       lda #$20
        sta tpl_c,x
        sta tpl_c+210,x
        lda #0
        sta tpl_a,x
        sta tpl_a+210,x
        inx
        cpx #210
        bne :-
        ; double rules on rows 0 and 9 (the panel's own rule glyph)
        ldx #SB_W-1
:       lda pan_codes+7*40
        sta tpl_c,x
        sta tpl_c+9*SB_W,x
        lda pan_attrs+7*40
        sta tpl_a,x
        sta tpl_a+9*SB_W,x
        dex
        bpl :-
        ldx #0                  ; texts: row, column, attribute, string
@txt:   lda txt_tab,x
        cmp #$FF
        beq @icons
        tay
        lda tpl_lo,y
        clc
        adc txt_tab+1,x
        sta tmp
        lda tpl_hi,y
        adc #0
        sta tmp+1
        lda tmp                 ; tmp+2 = the same cell in tpl_a
        clc
        adc #<(SB_ROWS*SB_W)
        sta tmp+2
        lda tmp+1
        adc #>(SB_ROWS*SB_W)
        sta tmp+3
        lda txt_tab+2,x
        sta sb_t
        inx
        inx
        inx
        ldy #0
@ch:    lda txt_tab,x
        inx
        cmp #0
        beq @txt
        sta (tmp),y
        lda sb_t
        sta (tmp+2),y
        iny
        bne @ch
@icons: ; ghost icons (3x2, two feet variants), in their own colours
        ldx #1
@g:     stx sb_t
        lda grow_off-1,x        ; template offset of the icon's top row
        tay
        lda gcol-1,x
        sta sb_v
        lda gfeet-1,x           ; 0 or 4: panel column 3 or 7
        tax
        lda #3
        sta dv_lo
@gc:    lda pan_codes+5*40+3,x
        sta tpl_c+B_ICON,y
        lda pan_codes+6*40+3,x
        sta tpl_c+B_ICON+SB_W,y
        lda sb_v
        sta tpl_a+B_ICON,y
        sta tpl_a+B_ICON+SB_W,y
        inx
        iny
        dec dv_lo
        bne @gc
        ldx sb_t
        inx
        cpx #5
        bne @g
        ; thermometer tube (rows 10-11) and the lives icon cells (12-13)
        ldx #THLEN-1
:       lda #RGBI_DKGREY|A_REV
        sta tpl_a+10*SB_W+B_TH,x
        sta tpl_a+11*SB_W+B_TH,x
        dex
        bpl :-
        ldx #10
:       lda #RGBI_LTYEL|A_ALT
        sta tpl_a+12*SB_W+B_LIVES,x
        sta tpl_a+13*SB_W+B_LIVES,x
        dex
        bpl :-
        rts

; sb_show: start drawing the board (entering the maze phase). The template
; goes up half a row per frame, then the live fields.
sb_show:
        lda #0
        sta sb_step
        sta sb_fld
        rts

; sb_hide: board off, the table's screen codes back from disp (the caller
; runs pb_undim for the attributes). ~1,400 cycles per board row touched.
sb_hide:
        lda #0
        beq hide
; sb_remove: same, plus the dimmed attributes (table stays dimmed)
sb_remove:
        lda #1
hide:   sta pbr_dim
        lda #$FF
        sta sb_step
        bit vdc_dead
        bmi @x
        lda #SB_TC0
        sta pbr_c0
        lda #SB_W
        sta pbr_n
@r:     lda sb_hi
        beq @x
        dec sb_hi
        clc
        adc #SB_ROW0-1
        tax
        jsr pb_restore_row
        jmp @r
@x:     lda #0
        sta sb_hi
        rts

; ------------------------------------------------------------------------
; sb_tick: once per maze frame
sb_tick:
        bit vdc_dead
        bmi @x
        lda sb_step
        bmi @x                  ; off
        lda frame
        and #7
        beq @x                  ; main3 runs mz_hud this frame
        lda frame
        and #31
        cmp #4
        beq @x                  ; ... or pb_show_score
        lda sb_step
        cmp #SB_HALF
        bcs live
        jmp tpl_step
@x:     rts

live:   jsr precompute
        ldx sb_fld
        lda #NFLD
        sta sb_t                ; fields left to check
@f:     stx sb_v
        jsr want                ; A = what field X should show
        ldx sb_v
        cmp shadow,x
        bne @draw
        inx
        cpx #NFLD
        bcc :+
        ldx #0
:       dec sb_t
        bne @f
        stx sb_fld
        rts
@draw:  sta shadow,x
        pha
        inx
        cpx #NFLD
        bcc :+
        ldx #0
:       stx sb_fld
        ldx sb_v
        lda fdraw_hi,x
        pha
        lda fdraw_lo,x
        pha
        rts                     ; -> draw routine, A on the stack below... (see fd_*)

; precompute: blue bar length (shared by the four ghosts) and, when a dot
; was eaten, the thermometer cells (percentage eaten / 5)
precompute:
        lda #0
        sta sb_bl
        lda fright
        ora fright+1
        beq @dots
        ; cells = ceil(fright / 30), at most BARLEN
        lda fright
        sta dv_lo
        lda fright+1
        sta dv_hi
        ldx #0
@b:     inx
        cpx #BARLEN
        bcs @bd
        lda dv_lo
        sec
        sbc #30
        sta dv_lo
        lda dv_hi
        sbc #0
        sta dv_hi
        bcc @bd
        ora dv_lo
        bne @b
@bd:    stx sb_bl
        lda fright+1            ; last 2 s: flashing
        bne @dots
        lda fright
        cmp #120
        bcs @dots
        lda sb_bl
        ora #$80
        sta sb_bl
@dots:  lda mz_dotsleft
        cmp sb_dl
        beq @x
        sta sb_dl
        ; eaten * 100 / NDOTS
        lda #<NDOTS
        sec
        sbc mz_dotsleft
        sta dv_lo
        lda #>NDOTS
        sbc mz_dotsleft+1
        sta dv_hi
        jsr mul100
        jsr div_ndots
        lda dv_lo
        sta sb_pct
        ldx #0                  ; thermometer: one cell per 5 %
        sec
:       sbc #5
        bcc :+
        inx
        bcs :-
:       stx sb_th
@x:     rts

; dv = dv * 100 (dv <= 311 -> <= 31,100)
mul100:
        lda dv_lo               ; x4
        asl
        sta dv_r
        lda dv_hi
        rol
        sta dv_r+1
        asl dv_r
        rol dv_r+1
        ldx #3                  ; x32 = x4 << 3
        lda dv_r
        sta sb_buf
        lda dv_r+1
        sta sb_buf+1
:       asl sb_buf
        rol sb_buf+1
        dex
        bne :-
        lda dv_r                ; x36
        clc
        adc sb_buf
        sta dv_r
        lda dv_r+1
        adc sb_buf+1
        sta dv_r+1
        asl sb_buf              ; x64
        rol sb_buf+1
        lda dv_r                ; x100
        clc
        adc sb_buf
        sta dv_lo
        lda dv_r+1
        adc sb_buf+1
        sta dv_hi
        rts

; dv = dv / NDOTS (16-bit shift-subtract)
div_ndots:
        lda #0
        sta dv_r
        sta dv_r+1
        ldx #16
@l:     asl dv_lo
        rol dv_hi
        rol dv_r
        rol dv_r+1
        lda dv_r
        sec
        sbc #<NDOTS
        tay
        lda dv_r+1
        sbc #>NDOTS
        bcc :+
        sta dv_r+1
        sty dv_r
        inc dv_lo
:       dex
        bne @l
        rts

; want: X = field -> A = the value it should show
want:   cpx #4
        bcs @n4
        inx                     ; ghosts 1-4: state
        jmp gstate_of
@n4:    cpx #8
        bcs @n8
        dex                     ; bars: ghost X-3
        dex
        dex
        jsr gstate_of
        cmp #2
        beq :+
        cmp #3
        beq :+
        lda #0
        rts
:       lda sb_bl
        rts
@n8:    bne @n9
        lda mz_dotsleft
        rts
@n9:    cpx #9
        bne @n10
        lda sb_th
        rts
@n10:   cpx #10
        bne @n11
        lda mz_lives
        cmp #4
        bcc :+
        lda #3
:       rts
@n11:   lda fr_t
        ora fr_t+1
        beq :+
        lda #$80
:       ora fr_kind
        rts

; gstate_of: X = ghost 1-4 -> A = 0 SCATTER, 1 CHASE, 2 BLUE, 3 BLUE
; (flashing), 4 EYES, 5 HOME (the order the VIC sprites use)
gstate_of:
        lda gstate,x
        cmp #2
        beq @eyes
        lda gblue,x
        bne @blue
        lda gstate,x
        beq @home
        lda chase
        and #1
        rts
@blue:  lda sb_bl
        bmi :+
        lda #2
        rts
:       lda #3
        rts
@eyes:  lda #4
        rts
@home:  lda #5
        rts

; ------------------------------------------------------------------------
; template step: even = screen codes of a row, odd = its attributes
tpl_step:
        lsr
        tax                     ; row
        php
        cpx sb_hi
        bcc :+
        inx
        stx sb_hi
        dex
:       lda tpl_lo,x
        sta tmp
        lda tpl_hi,x
        sta tmp+1
        txa
        clc
        adc #SB_ROW0
        ldx #SB_VC0
        jsr vaddr
        plp
        bcc :+
        jsr vattr
        lda tmp                 ; attributes: tpl_a = tpl_c + 420
        clc
        adc #<(SB_ROWS*SB_W)
        sta tmp
        lda tmp+1
        adc #>(SB_ROWS*SB_W)
        sta tmp+1
:       ldy #0
@p:     lda (tmp),y
        jsr vput
        iny
        cpy #SB_W
        bne @p
        inc sb_step
        lda sb_step
        cmp #SB_HALF
        bne @x
        ldx #NFLD-1             ; template done: every live field is unknown
        lda #$FF
:       sta shadow,x
        dex
        bpl :-
        lda mz_dotsleft         ; (force the count and the bar to be worked out)
        eor #$FF
        sta sb_dl
        sta shadow+8
@x:     rts

; ------------------------------------------------------------------------
; field draw routines: entered with the new value on the stack (pla)
; and sb_v = the field number

; ghost state: icon colour, state word
fd_ghost:
        pla
        sta sb_t                ; state 0-5
        ldx sb_v
        inx                     ; ghost 1-4
        stx sb_buf
        ; icon attribute
        lda sb_t
        cmp #2
        bcs :+
        lda gcol-1,x            ; normal: its own colour
        bne @ic
:       cmp #5
        bne :+
        lda gdim-1,x            ; home: its dark colour
        bne @ic
:       tay
        lda st_icon,y
@ic:    sta sb_buf+1
        lda grow-1,x            ; VDC row of the icon top
        sta sb_buf+2
        ldx #SB_VC0+B_ICON
        jsr vaddr
        jsr vattr
        lda sb_buf+1
        jsr vput
        jsr vput
        jsr vput
        lda sb_buf+2
        clc
        adc #1
        ldx #SB_VC0+B_ICON
        jsr vaddr
        jsr vattr
        lda sb_buf+1
        jsr vput
        jsr vput
        jsr vput
        ; word: codes, then attributes
        lda sb_buf+2
        ldx #SB_VC0+B_WORD
        jsr vaddr
        lda sb_t
        asl
        asl
        asl
        tax                     ; 8 bytes per word
        ldy #7
:       lda st_word,x
        jsr vput
        inx
        dey
        bne :-
        jsr vattr
        lda sb_t
        cmp #2
        bcs :+
        ldx sb_buf
        lda gcol-1,x            ; SCATTER / CHASE in the ghost's colour
        bne @wa
:       tay
        lda st_wattr,y
@wa:    ldy #7
:       jsr vput
        dey
        bne :-
        rts

; blue bar of ghost sb_v-3: cells = value & $7F, flashing if bit 7
fd_bar:
        pla
        sta sb_t
        lda sb_v
        sec
        sbc #3
        tax
        lda grow-1,x
        clc
        adc #1
        ldx #SB_VC0+B_BAR
        jsr vaddr
        jsr vattr
        lda #RGBI_LTBLUE|A_REV
        bit sb_t
        bpl :+
        ora #A_BLINK
:       sta sb_buf
        lda sb_t
        and #$7F
        tax                     ; filled cells
        ldy #BARLEN
@c:     lda #0                  ; empty: black space
        cpx #0
        beq :+
        dex
        lda sb_buf
:       jsr vput
        dey
        bne @c
        rts

; dots left (0-311), right aligned in 3 cells; LEFT is in the template
fd_left:
        pla
        lda mz_dotsleft
        sta dv_lo
        lda mz_dotsleft+1
        sta dv_hi
        ldx #$30                ; hundreds
@h:     lda dv_lo
        sec
        sbc #100
        tay
        lda dv_hi
        sbc #0
        bcc @t
        sta dv_hi
        sty dv_lo
        inx
        bne @h
@t:     stx sb_buf
        ldx #$30                ; tens
        lda dv_lo
:       cmp #10
        bcc :+
        sbc #10
        inx
        bne :-
:       ora #$30
        sta sb_buf+2
        stx sb_buf+1
        lda sb_buf              ; no leading zeros
        cmp #$30
        bne :+
        lda #$20
        sta sb_buf
        lda sb_buf+1
        cmp #$30
        bne :+
        lda #$20
        sta sb_buf+1
:       lda #SB_ROW0+10
        ldx #SB_VC0+B_PCT
        jsr vaddr
        ldx #0
:       lda sb_buf,x
        jsr vput
        inx
        cpx #3
        bne :-
        rts

; thermometer: two rows of 20, value cells yellow, the rest the dark tube
fd_therm:
        pla
        sta sb_t
        lda #SB_ROW0+10
        jsr therm_row
        lda #SB_ROW0+11
therm_row:
        ldx #SB_VC0+B_TH
        jsr vaddr
        jsr vattr
        ldx sb_t
        ldy #THLEN
@c:     lda #RGBI_DKGREY|A_REV
        cpx #0
        beq :+
        dex
        lda #RGBI_LTYEL|A_REV
:       jsr vput
        dey
        bne @c
        rts

; lives: up to 3 Pac-Man icons (codes only; the cells are yellow)
fd_lives:
        pla
        sta sb_t
        lda #0
        jsr lives_row
        lda #1
lives_row:
        sta sb_v                ; 0 top, 1 bottom
        clc
        adc #SB_ROW0+12
        ldx #SB_VC0+B_LIVES
        jsr vaddr
        ldx #0                  ; icon number
@i:     ldy #0
        lda #$20
        cpx sb_t
        bcs @sp
        lda sb_v
        beq @top
@bot:   lda pan_codes+6*40,y
        jsr vput
        iny
        cpy #3
        bne @bot
        beq @gap
@top:   lda pan_codes+5*40,y
        jsr vput
        iny
        cpy #3
        bne @top
        beq @gap
@sp:    jsr vput
        jsr vput
        jsr vput
@gap:   inx
        cpx #3
        beq @x
        lda #$20
        jsr vput                ; (vput changes the flags)
        jmp @i
@x:     rts

; fruit level icon; IN MAZE (blinking, attribute in the template) while one is out
fd_fruit:
        pla
        sta sb_t
        lda #SB_ROW0+12
        ldx #SB_VC0+B_FRUIT
        jsr vaddr
        lda sb_t
        and #3
        tax
        lda fr_icon,x
        tay
        lda vis_codes,y
        jsr vput
        jsr vattr
        lda fr_col,x
        jsr vput
        lda #SB_ROW0+13
        ldx #SB_VC0+B_INMZ
        jsr vaddr
        ldx #0
:       lda #$20
        bit sb_t
        bpl :+
        lda txt_inmaze,x
:       jsr vput
        inx
        cpx #7
        bne :--
        rts

; ------------------------------------------------------------------------
; vaddr: select VDC screen address of (row A, column X); vattr: the
; attribute address of the same cell. vput: write A (inline poll; only
; called while the VDC answers). All keep X and Y except vaddr / vattr (A).
vaddr:  sty sb_buf+11
        tay
        txa
        clc
        adc row80lo,y
        sta va_lo
        lda row80hi,y
        adc #0
        sta va_hi
        ldy va_lo
        jsr vdc_setaddr
        ldy sb_buf+11
        rts
vattr:  sty sb_buf+11
        lda va_hi
        clc
        adc #8
        ldy va_lo
        jsr vdc_setaddr
        ldy sb_buf+11
        rts
vput:   bit VDC_ADDR
        bpl vput
        sta VDC_DATA
        rts

.segment "RODATA"
; field draw routines (rts trick: address - 1)
fdraw_lo:   .byte <(fd_ghost-1), <(fd_ghost-1), <(fd_ghost-1), <(fd_ghost-1)
            .byte <(fd_bar-1), <(fd_bar-1), <(fd_bar-1), <(fd_bar-1)
            .byte <(fd_left-1), <(fd_therm-1), <(fd_lives-1), <(fd_fruit-1)
fdraw_hi:   .byte >(fd_ghost-1), >(fd_ghost-1), >(fd_ghost-1), >(fd_ghost-1)
            .byte >(fd_bar-1), >(fd_bar-1), >(fd_bar-1), >(fd_bar-1)
            .byte >(fd_left-1), >(fd_therm-1), >(fd_lives-1), >(fd_fruit-1)
tpl_lo:
.repeat SB_ROWS, I
            .byte <(tpl_c + I*SB_W)
.endrepeat
tpl_hi:
.repeat SB_ROWS, I
            .byte >(tpl_c + I*SB_W)
.endrepeat
; ghosts 1-4 (Blinky, Pinky, Inky, Clyde): colours as on the left panel
gcol:       .byte RGBI_LTRED|A_ALT, RGBI_LTPURP|A_ALT, RGBI_LTCYAN|A_ALT, RGBI_DKYEL|A_ALT
gdim:       .byte RGBI_DKRED|A_ALT, RGBI_DKPURP|A_ALT, RGBI_DKCYAN|A_ALT, RGBI_DKGREY|A_ALT
gfeet:      .byte 0, 4, 0, 4
grow:       .byte SB_ROW0+1, SB_ROW0+3, SB_ROW0+5, SB_ROW0+7
grow_off:   .byte 1*SB_W, 3*SB_W, 5*SB_W, 7*SB_W
; per state: icon colour (2-4; 0/1 own colour, 5 dark), word, word colour
st_icon:    .byte 0, 0, RGBI_LTBLUE|A_ALT, RGBI_LTBLUE|A_ALT|A_BLINK, RGBI_DKGREY|A_ALT
st_word:    .byte "SCATTER ", "CHASE   ", "BLUE    ", "BLUE    ", "EYES    ", "HOME    "
st_wattr:   .byte 0, 0, RGBI_LTBLUE|A_ALT, RGBI_LTBLUE|A_ALT|A_BLINK, RGBI_LTGREY|A_ALT
            .byte RGBI_LTGREY|A_ALT
; fruit level 0-3: cherry, strawberry, orange, apple (the table's fruit
; cluster icons at row 1, columns 5-7; bank 0)
fr_icon:    .byte 1*40+5, 1*40+6, 1*40+7, 1*40+7
fr_col:     .byte RGBI_LTRED, RGBI_LTRED, RGBI_DKYEL, RGBI_LTGREEN
txt_inmaze: .byte "IN MAZE"
; template texts: row, column, attribute, string, 0 ... $FF
txt_tab:
            .byte 0, 11, RGBI_WHITE|A_ALT, " GHOSTS ", 0
            .byte 1, B_NAME, RGBI_LTRED|A_ALT, "BLINKY", 0
            .byte 3, B_NAME, RGBI_LTPURP|A_ALT, "PINKY", 0
            .byte 5, B_NAME, RGBI_LTCYAN|A_ALT, "INKY", 0
            .byte 7, B_NAME, RGBI_DKYEL|A_ALT, "CLYDE", 0
            .byte 10, 1, RGBI_WHITE|A_ALT, "DOTS", 0
            .byte 11, B_PCT, RGBI_WHITE|A_ALT, "LEFT", 0
            .byte 10, B_PCT, RGBI_WHITE|A_ALT, "   ", 0
            .byte 12, 1, RGBI_LTYEL|A_ALT, "LIVES", 0
            .byte 12, B_INMZ, RGBI_LTRED|A_ALT, "FRUIT", 0
            .byte 13, B_INMZ, RGBI_WHITE|A_ALT|A_BLINK, "       ", 0
            .byte $FF
.endif
