; screen.s - text output to the VIC (40 col) and VDC (80 col) screens
; Strings are 0-terminated screen codes (see hw/scr.inc).
; pr_mask bit 0 = draw on VIC, bit 1 = draw on VDC.
; The VDC layout is: screen codes at $0000, attributes at $0800 (80x25).

.include "hw/c128.inc"

.exportzp pr_row, pr_col, pr_vcol, pr_color, pr_vattr, pr_mask, vicscr
.exportzp sptr, num, tmp
.export printi, scr_at, scr_vat, set_color, print, putc, print_num
.export fmt_hex8, fmt_dec, vic2rgbi, cls_vic, cls_vdc, vdc_font
.export row40lo, row40hi, row80lo, row80hi, vic_cell_addr
.import vdc_setaddr, vdc_put, vdc_fill, vdc_fillsetup

.segment "ZEROPAGE"
pr_row:     .res 1
pr_col:     .res 1      ; VIC column
pr_vcol:    .res 1      ; VDC column
pr_color:   .res 1      ; VIC colour 0-15
pr_vattr:   .res 1      ; VDC attribute byte
pr_mask:    .res 1
vicscr:     .res 1      ; VIC screen page (hi byte), e.g. $04
sptr:       .res 2      ; string pointer
vptr:       .res 2      ; VIC screen pointer
cptr:       .res 2      ; colour RAM pointer
num:        .res 3      ; 24-bit number for fmt_dec
tmp:        .res 4
plen:       .res 1

.segment "BSS"
numbuf:     .res 12

.segment "DATA"
; OR'd into every VDC text attribute by set_color. $80 = alternate
; character set (the art pass bold font lives there). Initialised 0 in
; the program image, so the Tier 1 diagnostics keep the ROM font.
vdc_font:   .byte 0

.segment "CODE"

; scr_at: A=row, X=col. VDC column = same column (use scr_vat to change).
scr_at:
        sta pr_row
        stx pr_col
        stx pr_vcol
        rts

; scr_vat: X = VDC column only
scr_vat:
        stx pr_vcol
        rts

; set_color: A = VIC colour; VDC attribute = mapped RGBI colour
set_color:
        and #$0F
        sta pr_color
        tax
        lda vic2rgbi,x
        ora vdc_font
        sta pr_vattr
        rts

; vic_cell_addr: compute vptr/cptr for pr_row/pr_col
vic_cell_addr:
        ldx pr_row
        lda row40lo,x
        clc
        adc pr_col
        sta vptr
        sta cptr
        lda row40hi,x
        adc #0
        sta cptr+1
        clc
        adc vicscr
        sta vptr+1
        lda cptr+1
        clc
        adc #>COLRAM
        sta cptr+1
        rts

; print: A/X = pointer to 0-terminated string
print:
        sta sptr
        stx sptr+1
        ; length
        ldy #0
:       lda (sptr),y
        beq :+
        iny
        bne :-
:       sty plen
        cpy #0
        bne :+
        rts
:       lda pr_mask
        and #1
        beq @novic
        jsr vic_cell_addr
        ldy #0
@vl:    lda (sptr),y
        beq @vd
        sta (vptr),y
        lda pr_color
        sta (cptr),y
        iny
        bne @vl
@vd:
@novic: lda pr_mask
        and #2
        beq @novdc
        jsr vdc_rowaddr
        lda tmp+1
        ldy tmp
        jsr vdc_setaddr
        ldy #0
@dl:    lda (sptr),y
        beq @dd
        jsr vdc_put
        iny
        bne @dl
@dd:    lda tmp+1
        clc
        adc #$08
        ldy tmp
        jsr vdc_setaddr
        ldy plen
        lda pr_vattr
@al:    jsr vdc_put
        dey
        bne @al
@novdc: lda pr_col
        clc
        adc plen
        sta pr_col
        lda pr_vcol
        clc
        adc plen
        sta pr_vcol
        rts

; vdc_rowaddr: tmp/tmp+1 = pr_row*80 + pr_vcol
vdc_rowaddr:
        ldx pr_row
        lda row80lo,x
        clc
        adc pr_vcol
        sta tmp
        lda row80hi,x
        adc #0
        sta tmp+1
        rts

; printi: print the 0-terminated string that follows the JSR, then
; return to the byte after it.
printi:
        pla
        sta sptr
        pla
        sta sptr+1
        inc sptr
        bne :+
        inc sptr+1
:       lda sptr
        ldx sptr+1
        jsr print               ; leaves sptr = string start, plen = length
        lda sptr
        clc
        adc plen
        sta sptr
        bcc :+
        inc sptr+1
:       lda sptr+1              ; return address = terminator byte
        pha
        lda sptr
        pha
        rts

; putc: print one screen code (A)
putc:
        sta numbuf+10
        lda #0
        sta numbuf+11
        lda #<(numbuf+10)
        ldx #>(numbuf+10)
        jmp print

; print_num: print the string fmt_* left in A/X (just a jmp to print)
print_num = print

; fmt_hex8: A -> 2 hex digits. Returns A/X = string pointer.
fmt_hex8:
        pha
        lsr
        lsr
        lsr
        lsr
        tax
        lda hexdig,x
        sta numbuf
        pla
        and #$0F
        tax
        lda hexdig,x
        sta numbuf+1
        lda #0
        sta numbuf+2
        lda #<numbuf
        ldx #>numbuf
        rts

; fmt_dec: 24-bit num -> decimal right-justified in a field of width A (1-8)
; Returns A/X = string pointer.
fmt_dec:
        sta tmp+3
        ldx #0                  ; digit index 0..7
@dig:   ldy #0                  ; digit value
@sub:   lda num
        sec
        sbc p10_0,x
        sta tmp
        lda num+1
        sbc p10_1,x
        sta tmp+1
        lda num+2
        sbc p10_2,x
        bcc @nx
        sta num+2
        lda tmp+1
        sta num+1
        lda tmp
        sta num
        iny
        bne @sub
@nx:    tya
        ora #$30
        sta numbuf,x
        inx
        cpx #8
        bne @dig
        lda #0
        sta numbuf+8
        ; leading zeros -> spaces
        ldx #0
@lz:    lda numbuf,x
        cmp #$30
        bne @lzd
        lda #$20
        sta numbuf,x
        inx
        cpx #7
        bne @lz
@lzd:   lda #8
        sec
        sbc tmp+3
        clc
        adc #<numbuf
        pha
        lda #>numbuf
        adc #0
        tax
        pla
        rts

; cls_vic: fill the VIC screen with spaces in colour pr_color
cls_vic:
        lda vicscr
        sta vptr+1
        lda #>COLRAM
        sta cptr+1
        lda #0
        sta vptr
        sta cptr
        ldx #4
@pg:    ldy #0
@l:     lda #$20
        sta (vptr),y
        lda pr_color
        sta (cptr),y
        iny
        bne @l
        inc vptr+1
        inc cptr+1
        dex
        bne @pg
        rts

; cls_vdc: spaces at $0000-$07CF, attribute pr_vattr at $0800-$0FCF
cls_vdc:
        lda #$00
        ldy #$00
        jsr vdc_setaddr
        lda #<2000
        ldx #>2000
        ldy #$20
        jsr vdc_fillsetup
        jsr vdc_fill
        lda #$08
        ldy #$00
        jsr vdc_setaddr
        lda #<2000
        ldx #>2000
        ldy pr_vattr
        jsr vdc_fillsetup
        jmp vdc_fill

.segment "RODATA"
hexdig: .byte $30,$31,$32,$33,$34,$35,$36,$37,$38,$39,1,2,3,4,5,6
p10_0:  .byte <10000000, <1000000, <100000, <10000, <1000, <100, <10, <1
p10_1:  .byte >10000000 & $FF, >1000000 & $FF, >100000 & $FF, >10000, >1000, >100, >10, >1
p10_2:  .byte ^10000000, ^1000000, ^100000, ^10000, ^1000, ^100, ^10, ^1

; VIC colour index -> VDC RGBI colour for the "same" look
vic2rgbi:
        .byte RGBI_BLACK, RGBI_WHITE, RGBI_LTRED, RGBI_LTCYAN
        .byte RGBI_LTPURP, RGBI_LTGREEN, RGBI_LTBLUE, RGBI_LTYEL
        .byte RGBI_DKYEL, RGBI_DKYEL, RGBI_LTRED, RGBI_DKGREY
        .byte RGBI_LTGREY, RGBI_LTGREEN, RGBI_LTBLUE, RGBI_LTGREY

row40lo:
.repeat 25, I
        .byte <(I*40)
.endrepeat
row40hi:
.repeat 25, I
        .byte >(I*40)
.endrepeat
row80lo:
.repeat 25, I
        .byte <(I*80)
.endrepeat
row80hi:
.repeat 25, I
        .byte >(I*80)
.endrepeat
