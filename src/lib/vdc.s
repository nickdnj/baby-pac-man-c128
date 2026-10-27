; vdc.s - VDC 8563 access layer (architecture section 6, ADR-004)
; Every register select and data access polls the status ready bit (bit 7)
; with a bounded timeout. No block copy / block fill is ever used.
; If the VDC stops answering, vdc_dead is set and all later calls return
; quickly, so callers never hang.

.include "hw/c128.inc"

.exportzp vdc_busy, vdc_tmo, vdc_dead
.export vdc_wait, vdc_wreg, vdc_rreg, vdc_setaddr, vdc_put, vdc_get
.export vdc_fill, vdc_fillsetup

.segment "ZEROPAGE"
vdc_busy:   .res 2      ; number of polls that found the VDC busy
vdc_tmo:    .res 1      ; number of polls that timed out
vdc_dead:   .res 1      ; $FF once the VDC is considered not responding
vfcount:    .res 2      ; vdc_fill byte count
vfval:      .res 1

.segment "CODE"

; vdc_wait: wait until the VDC is ready. Preserves A, X, Y.
vdc_wait:
        bit VDC_ADDR
        bmi @ok
        bit vdc_dead
        bmi @ok
        pha
        txa
        pha
        tya
        pha
        inc vdc_busy
        bne :+
        inc vdc_busy+1
:       ldy #8                  ; ~8 x 256 polls, about 20 ms
        ldx #0
@lp:    bit VDC_ADDR
        bmi @done
        dex
        bne @lp
        dey
        bne @lp
        ; timed out
        inc vdc_tmo
        lda vdc_tmo
        cmp #4
        bcc @done
        lda #$FF
        sta vdc_dead
@done:  pla
        tay
        pla
        tax
        pla
@ok:    rts

; vdc_wreg: write A to register X. Preserves A, X, Y.
vdc_wreg:
        stx VDC_ADDR
        jsr vdc_wait
        sta VDC_DATA
        rts

; vdc_rreg: read register X into A. Preserves X, Y.
vdc_rreg:
        stx VDC_ADDR
        jsr vdc_wait
        lda VDC_DATA
        rts

; vdc_setaddr: set update address to A (hi) / Y (lo), then select R31.
; Preserves X. Clobbers A.
vdc_setaddr:
        stx @sx+1
        ldx #18
        jsr vdc_wreg
        tya
        ldx #19
        jsr vdc_wreg
        lda #31
        sta VDC_ADDR
@sx:    ldx #0
        rts

; vdc_put: write A to VDC RAM at the update address (R31 must be selected),
; address auto-increments. Preserves A, X, Y.
vdc_put:
        jsr vdc_wait
        sta VDC_DATA
        rts

; vdc_get: read next VDC RAM byte into A. Preserves X, Y.
vdc_get:
        jsr vdc_wait
        lda VDC_DATA
        rts

; vdc_fillsetup: store count (A lo, X hi) and value (Y) for vdc_fill
vdc_fillsetup:
        sta vfcount
        stx vfcount+1
        sty vfval
        rts

; vdc_fill: CPU fill of vfcount bytes with vfval from the current update
; address (set by vdc_setaddr). Not a VDC block fill.
vdc_fill:
        lda vfcount
        ora vfcount+1
        beq @x
        lda vfval
@lp:    jsr vdc_put
        ldx vfcount
        bne :+
        dec vfcount+1
:       dec vfcount
        ldx vfcount
        bne @lp
        ldx vfcount+1
        bne @lp
@x:     rts
