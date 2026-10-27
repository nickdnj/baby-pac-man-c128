; stub.s - PRG load address and BASIC stub "10 SYS 7184" at $1C01
; Code must start at $1C10 (= 7184), which the linker config guarantees.

.segment "LOADADDR"
        .word $1C01

.segment "STUB"
        .word stubnext             ; link to next line
        .word 10                ; line number
        .byte $9E               ; SYS token
        .byte "7184"
        .byte 0
stubnext:  .word 0                 ; end of program
