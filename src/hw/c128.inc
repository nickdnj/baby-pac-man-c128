; c128.inc - Commodore 128 hardware equates
; Register facts used here are the ones the architecture marks [Unconfirmed];
; the VDCTEST/DUALDEMO programs exist to check them on the real machine.

; --- MMU ---
MMU_CR      = $FF00     ; configuration register (mirror, always visible)
MMU_CFG_ROM = $00       ; "BANK 15": BASIC+KERNAL ROMs, I/O, RAM 0
MMU_CFG_CHR = $01       ; "BANK 14": like 15 but character ROM at $D000
MMU_CFG_RAM = $3E       ; RAM 0 everywhere, I/O at $D000
MMU_RCR     = $D506     ; RAM configuration register

; --- VIC-IIe ---
VIC         = $D000
VIC_SPR0X   = $D000
VIC_SPR0Y   = $D001
VIC_SPRXMSB = $D010
VIC_CR1     = $D011
VIC_RASTER  = $D012
VIC_SPREN   = $D015
VIC_CR2     = $D016
VIC_SPRYEXP = $D017
VIC_MEMPTR  = $D018
VIC_IRQ     = $D019
VIC_IRQEN   = $D01A
VIC_SPRPRI  = $D01B
VIC_SPRMC   = $D01C
VIC_SPRXEXP = $D01D
VIC_BORDER  = $D020
VIC_BG0     = $D021
VIC_SPRMC0  = $D025
VIC_SPRMC1  = $D026
VIC_SPR0COL = $D027
VIC_KBDEXT  = $D02F     ; C128 extra keyboard lines
VIC_CLOCK   = $D030     ; bit 0 = 2 MHz

COLRAM      = $D800

; --- SID ---
SID         = $D400
SID_POTX    = $D419
SID_POTY    = $D41A
SID_VOL     = $D418

; --- VDC 8563 ---
VDC_ADDR    = $D600     ; write: register select; read: status
VDC_DATA    = $D601

; --- CIA ---
CIA1_PRA    = $DC00     ; joystick port 2 / keyboard columns
CIA1_PRB    = $DC01     ; joystick port 1 / keyboard rows
CIA1_DDRA   = $DC02
CIA1_DDRB   = $DC03
CIA1_TALO   = $DC04
CIA1_TAHI   = $DC05
CIA1_TBLO   = $DC06
CIA1_TBHI   = $DC07
CIA1_ICR    = $DC0D
CIA1_CRA    = $DC0E
CIA1_CRB    = $DC0F
CIA2_PRA    = $DD00
CIA2_DDRA   = $DD02
CIA2_ICR    = $DD0D

; --- VIC colours ---
COL_BLACK   = 0
COL_WHITE   = 1
COL_RED     = 2
COL_CYAN    = 3
COL_PURPLE  = 4
COL_GREEN   = 5
COL_BLUE    = 6
COL_YELLOW  = 7
COL_ORANGE  = 8
COL_BROWN   = 9
COL_LTRED   = 10
COL_DKGREY  = 11
COL_GREY    = 12
COL_LTGREEN = 13
COL_LTBLUE  = 14
COL_LTGREY  = 15

; --- VDC RGBI colours ---
RGBI_BLACK   = 0
RGBI_DKGREY  = 1
RGBI_DKBLUE  = 2
RGBI_LTBLUE  = 3
RGBI_DKGREEN = 4
RGBI_LTGREEN = 5
RGBI_DKCYAN  = 6
RGBI_LTCYAN  = 7
RGBI_DKRED   = 8
RGBI_LTRED   = 9
RGBI_DKPURP  = 10
RGBI_LTPURP  = 11
RGBI_DKYEL   = 12
RGBI_LTYEL   = 13
RGBI_LTGREY  = 14
RGBI_WHITE   = 15
