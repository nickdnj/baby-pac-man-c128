; scr.inc - map source-text strings to C= screen codes (uppercase/graphics set)
; 'A'-'Z' -> 1-26, '@' -> 0, '[' -> 27, ']' -> 29. Digits, space and most
; punctuation already equal their screen codes. Use UPPERCASE text only.
.repeat 26, I
    .charmap $41+I, 1+I
.endrepeat
; '@' would be screen code 0 = string terminator: never use it in text
.charmap '[', 27
.charmap ']', 29
.charmap '^', 30        ; up arrow
.charmap '_', 31        ; left arrow
