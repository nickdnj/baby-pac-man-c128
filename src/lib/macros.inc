; macros.inc - text printing helpers (needs scr.inc charmap active)

; NOTE: these macros must not define labels (that would break the
; cheap-local @labels around them), so strings follow a "jsr printi".

; PRS row, col, "TEXT" : print at row/col on the screens in pr_mask
.macro PRS row, col, text
    lda #row
    ldx #col
    jsr scr_at
    jsr printi
    .byte text, 0
.endmacro

; PRT "TEXT" : print at the current position
.macro PRT text
    jsr printi
    .byte text, 0
.endmacro

.macro COLOR c
    lda #c
    jsr set_color
.endmacro

.macro MASK m
    lda #m
    sta pr_mask
.endmacro

; PRDEC addr, width : print 24-bit number at addr (3 bytes) right-justified
.macro PRDEC24 addr, width
    lda addr
    sta num
    lda addr+1
    sta num+1
    lda addr+2
    sta num+2
    lda #width
    jsr fmt_dec
    jsr print
.endmacro

; PRDEC16 addr, width : 16-bit number
.macro PRDEC16 addr, width
    lda addr
    sta num
    lda addr+1
    sta num+1
    lda #0
    sta num+2
    lda #width
    jsr fmt_dec
    jsr print
.endmacro

; PRDEC8 addr, width
.macro PRDEC8 addr, width
    lda addr
    sta num
    lda #0
    sta num+1
    sta num+2
    lda #width
    jsr fmt_dec
    jsr print
.endmacro

.macro PRHEX8 addr
    lda addr
    jsr fmt_hex8
    jsr print
.endmacro

; INC24 addr
; (addr must be an absolute, non-zero-page address)
.macro INC24 addr
    inc addr
    bne *+10
    inc addr+1
    bne *+5
    inc addr+2
.endmacro
