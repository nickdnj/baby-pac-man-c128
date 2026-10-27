; sys.s - machine setup, frame sync, input sampling
; Timing is by polling the VIC raster (no interrupts are used at all;
; the CPU runs with interrupts disabled from start to finish).

.include "hw/c128.inc"

.exportzp tcyc, frame, joy2, port1, joy2_edge, port1_edge, potx, poty, video_pal
.export sys_init, wait_frame, read_input, detect_video, read_pots
.export timer_start, timer_stop, vdc_basic_init, vdc_copy_rom_font
.export ram_vectors
.importzp vdc_dead
.import vdc_wreg, vdc_rreg, vdc_setaddr, vdc_put

.segment "ZEROPAGE"
frame:      .res 2
joy2:       .res 1      ; port 2, active-high: b0 up b1 down b2 left b3 right b4 fire
port1:      .res 1      ; port 1, active-high, same bit layout (paddle fire X=b2, Y=b3)
joy2_edge:  .res 1      ; bits newly pressed this frame
port1_edge: .res 1
potx:       .res 1
poty:       .res 1
video_pal:  .res 1      ; 0 = NTSC, 1 = PAL, $80 = unknown
maxline:    .res 1
fptr:       .res 2
tcyc:       .res 3

.segment "CODE"

; sys_init: called right after SYS, with ROMs still in.
sys_init:
        sei
        cld
        lda #$7F
        sta CIA1_ICR
        sta CIA2_ICR
        lda CIA1_ICR
        lda CIA2_ICR
        lda #0
        sta VIC_IRQEN
        lda #$0F
        sta VIC_IRQ
        lda VIC_CLOCK           ; force 1 MHz so the VIC display is on
        and #$FC
        sta VIC_CLOCK
        lda #$FF
        sta CIA1_DDRA
        lda #$00
        sta CIA1_DDRB
        lda #$FF
        sta CIA1_PRA
        sta VIC_KBDEXT
        ; silence SID
        ldx #$18
        lda #0
:       sta SID,x
        dex
        bpl :-
        lda #0
        sta frame
        sta frame+1
        sta joy2
        sta port1
        rts

; ram_vectors: when the ROMs are banked out ($FF00=$3E) the CPU reads the
; NMI/RESET/IRQ vectors from RAM. Point NMI and IRQ at an RTI so a RESTORE
; key press cannot crash the program. Call with MMU_CR = MMU_CFG_RAM.
ram_vectors:
        lda #<nmi_rti
        sta $FFFA
        sta $FFFE
        lda #>nmi_rti
        sta $FFFB
        sta $FFFF
        lda #<nmi_rti           ; reset vector unused (reset maps ROMs in)
        sta $FFFC
        lda #>nmi_rti
        sta $FFFD
        rts
nmi_rti:
        rti

; wait_frame: wait for raster line 251 (lower border on NTSC and PAL)
wait_frame:
@w0:    lda VIC_RASTER
        cmp #251
        beq @w0
@w1:    lda VIC_RASTER
        cmp #251
        bne @w1
        inc frame
        bne :+
        inc frame+1
:       rts

; detect_video: measure the highest raster line. NTSC = 262/263, PAL = 311.
detect_video:
        lda #0
        sta maxline
        ; wait for the start of a frame (line 0)
        ldx #0
@a:     bit VIC_CR1
        bmi @a                  ; wait until raster < 256
@b:     bit VIC_CR1
        bpl @b                  ; wait until raster >= 256
@c:     lda VIC_RASTER
        cmp maxline
        bcc :+
        sta maxline
:       bit VIC_CR1
        bmi @c
        lda maxline             ; NTSC ~6-7, PAL ~55
        cmp #30
        lda #0
        bcc :+
        lda #1
:       sta video_pal
        rts

; read_input: sample port 2 (joystick) and port 1 (paddle buttons/joystick)
; with no keyboard column selected. Active-high results with edge bits.
read_input:
        lda #$FF
        sta CIA1_PRA
        sta VIC_KBDEXT
        lda CIA1_PRB
        eor #$FF
        and #$1F
        tax
        eor port1
        and #$FF
        stx port1
        and port1
        sta port1_edge
        lda CIA1_PRA
        eor #$FF
        and #$1F
        tax
        eor joy2
        stx joy2
        and joy2
        sta joy2_edge
        rts

; read_pots: select port 1 paddles on the SID and read both pots.
; Takes about 1 ms (SID needs 512 cycles per sample). Leaves $DC00=$FF.
read_pots:
        lda #$7F                ; bits 7-6 = 01: port 1 pots (keyboard col 7 low)
        sta CIA1_PRA
        ldx #0
:       nop
        nop
        dex
        bne :-                  ; ~1800 cycles
        lda SID_POTX
        sta potx
        lda SID_POTY
        sta poty
        lda #$FF
        sta CIA1_PRA
        rts

; timer_start: CIA1 timer A free-running from $FFFF at phi2, timer B
; counting timer A underflows (cascade) -> 32-bit cycle counter.
timer_start:
        lda #0
        sta CIA1_CRA
        sta CIA1_CRB
        lda #$FF
        sta CIA1_TALO
        sta CIA1_TAHI
        sta CIA1_TBLO
        sta CIA1_TBHI
        lda #$51                ; TB: force load, count TA underflows, start
        sta CIA1_CRB
        lda #$11                ; TA: force load, continuous, start
        sta CIA1_CRA
        rts

; timer_stop: stop, elapsed cycles -> tcyc (24 bit). Returns A/X = low 16.
timer_stop:
        lda #0
        sta CIA1_CRA
        sta CIA1_CRB
        lda CIA1_TALO
        eor #$FF
        sta tcyc
        lda CIA1_TAHI
        eor #$FF
        sta tcyc+1
        lda CIA1_TBLO
        eor #$FF
        sta tcyc+2
        lda tcyc
        ldx tcyc+1
        rts

; vdc_basic_init: display start $0000, attributes $0800, attributes on,
; text mode, charset at $2000 (RAM-type bit 4 left as found), black bg.
; Timing registers R0-R8 are not touched.
vdc_basic_init:
        lda #0
        ldx #12
        jsr vdc_wreg
        ldx #13
        jsr vdc_wreg
        lda #$08
        ldx #20
        jsr vdc_wreg
        lda #$00
        ldx #21
        jsr vdc_wreg
        ldx #25
        jsr vdc_rreg
        and #%00001111          ; keep fine scroll bits
        ora #%01000000          ; attributes on, text mode, no reverse screen
        jsr vdc_wreg
        lda #$F0                ; fg white / bg black
        ldx #26
        jsr vdc_wreg
        ldx #28
        jsr vdc_rreg
        and #%00011111
        ora #%00100000          ; charset base $2000
        jsr vdc_wreg
        rts

; vdc_copy_rom_font: copy the 512 character-ROM glyphs ($D000-$DFFF in
; MMU config $01) to VDC $2000-$3FFF with a 16-byte stride (8 rows + 8
; zero rows). Must be called with ROMs in (code below $4000).
vdc_copy_rom_font:
        lda #$20
        ldy #$00
        jsr vdc_setaddr
        lda #$00
        sta fptr
        lda #$D0
        sta fptr+1
@glyph: ldy #0
@row:   lda #MMU_CFG_CHR
        sta MMU_CR
        lda (fptr),y
        ldx #MMU_CFG_ROM
        stx MMU_CR
        jsr vdc_put
        iny
        cpy #8
        bne @row
        lda #0
@pad:   jsr vdc_put
        iny
        cpy #16
        bne @pad
        lda fptr
        clc
        adc #8
        sta fptr
        bcc @glyph
        inc fptr+1
        lda fptr+1
        cmp #$E0
        bne @glyph
        rts
