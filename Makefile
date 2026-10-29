# Baby Pac-Man for Commodore 128 - build
# Needs: ca65/ld65 (cc65), c1541 (VICE). On macOS: brew install cc65 vice
export PATH := /opt/homebrew/bin:$(PATH)

CA65  = ca65
LD65  = ld65
C1541 = c1541
X128  = x128
CFG   = src/linker/c128.cfg
AFLAGS = --cpu 6502 -g -I src
B = build

LIBOBJ = $(B)/stub.o $(B)/vdc.o $(B)/screen.o $(B)/sys.o

.PHONY: all tier1 tier2 tier3 clean release run-vdctest run-dualdemo

all: tier1 tier2 tier3

# ---------------------------------------------------------------- objects
$(B)/%.o: src/lib/%.s src/hw/*.inc src/lib/*.inc | $(B)
	$(CA65) $(AFLAGS) -o $@ $<
$(B)/%.o: src/diag/%.s src/hw/*.inc src/lib/*.inc | $(B)
	$(CA65) $(AFLAGS) -o $@ $<
$(B)/%.o: src/pinball/%.s src/hw/*.inc src/lib/*.inc | $(B)
	$(CA65) $(AFLAGS) -o $@ $<
$(B)/%.o: src/maze/%.s src/hw/*.inc src/lib/*.inc | $(B)
	$(CA65) $(AFLAGS) -o $@ $<

$(B):
	mkdir -p $(B)

# ---------------------------------------------------------------- tier 2
$(B)/table_data.s: tools/mktable.py tools/artlib.py | $(B)
	python3 tools/mktable.py $@ > $(B)/table_map.txt
$(B)/pinball.o: src/pinball/pinball.s $(B)/table_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -o $@ $<
$(B)/pinball-bot.o: src/pinball/pinball.s $(B)/table_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -D BOT=1 -o $@ $<
PBOBJ = $(B)/pbmain.o $(B)/pinball.o $(LIBOBJ)
$(B)/pinball.prg: $(PBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/pinball.map -Ln $(B)/pinball.lbl $(PBOBJ)
$(B)/pinball-bot.prg: $(B)/pbmain.o $(B)/pinball-bot.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/pinball-bot.map -Ln $(B)/pinball-bot.lbl $(B)/pbmain.o $(B)/pinball-bot.o $(LIBOBJ)

$(B)/tier2-pinball.d64: $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm tier2,t2" d64 $@ -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/tier2-pinball.d71: $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm tier2,t2" d71 $@ -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/test-bot.d64: $(B)/pinball-bot.prg
	rm -f $@
	$(C1541) -format "bpm bot,tb" d64 $@ -write $(B)/pinball-bot.prg pinbot >/dev/null

tier2: $(B)/tier2-pinball.d64 $(B)/tier2-pinball.d71 $(B)/test-bot.d64

# ---------------------------------------------------------------- tier 3
$(B)/maze_data.s: tools/mkmaze.py | $(B)
	python3 tools/mkmaze.py $@ > $(B)/maze_map.txt
$(B)/maze.o: src/maze/maze.s $(B)/maze_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -o $@ $<
BPOBJ = $(B)/main3.o $(B)/maze.o $(B)/pinball.o $(LIBOBJ)
$(B)/babypac.prg: $(BPOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/babypac.map -Ln $(B)/babypac.lbl $(BPOBJ)
$(B)/tier3-babypac.d64: $(B)/babypac.prg $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man,t3" d64 $@ -write $(B)/babypac.prg "baby pac-man" -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/tier3-babypac.d71: $(B)/babypac.prg $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man,t3" d71 $@ -write $(B)/babypac.prg "baby pac-man" -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null

$(B)/maze-auto.o: src/maze/maze.s $(B)/maze_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -D AUTOPLAY=1 -o $@ $<
$(B)/main3-auto.o: src/maze/main3.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -D AUTOPLAY=1 -o $@ $<
AUTOOBJ = $(B)/main3-auto.o $(B)/maze-auto.o $(B)/pinball-bot.o $(LIBOBJ)
$(B)/babypac-auto.prg: $(AUTOOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/babypac-auto.map -Ln $(B)/babypac-auto.lbl $(AUTOOBJ)
$(B)/test-auto.d64: $(B)/babypac-auto.prg
	rm -f $@
	$(C1541) -format "bpm auto,ta" d64 $@ -write $(B)/babypac-auto.prg bpauto >/dev/null

tier3: $(B)/tier3-babypac.d64 $(B)/tier3-babypac.d71 $(B)/test-auto.d64

# ---------------------------------------------------------------- tier 1
# Diagnostics keep the ROMs in, so they must end below $4000 (MAINTOP default)
$(B)/vdctest.prg: $(B)/vdctest.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -o $@ -m $(B)/vdctest.map -Ln $(B)/vdctest.lbl $(B)/vdctest.o $(LIBOBJ)
$(B)/dualdemo.prg: $(B)/dualdemo.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -o $@ -m $(B)/dualdemo.map -Ln $(B)/dualdemo.lbl $(B)/dualdemo.o $(LIBOBJ)

$(B)/tier1-diag.d64: $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm tier1,t1" d64 $@ -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/tier1-diag.d71: $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm tier1,t1" d71 $@ -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null

tier1: $(B)/tier1-diag.d64 $(B)/tier1-diag.d71

release: tier1 tier2 tier3
	mkdir -p release
	cp $(B)/tier1-diag.d64 $(B)/tier1-diag.d71 release/
	cp $(B)/tier2-pinball.d64 $(B)/tier2-pinball.d71 release/
	cp $(B)/tier3-babypac.d64 $(B)/tier3-babypac.d71 release/

# ---------------------------------------------------------------- art pass
# art-*.d64/.d71: the art-pass builds, written to release/ under NEW names.
# (`make release` above copies the tier images; the art targets never touch
# release/tier* or release/stable-baseline/.)
$(B)/art-pinball.d64: $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm art pinball,a2" d64 $@ -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/art-pinball.d71: $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "bpm art pinball,a2" d71 $@ -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/art-babypac.d64: $(B)/babypac.prg $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man art,a3" d64 $@ -write $(B)/babypac.prg "baby pac-man" -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/art-babypac.d71: $(B)/babypac.prg $(B)/pinball.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man art,a3" d71 $@ -write $(B)/babypac.prg "baby pac-man" -write $(B)/pinball.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null

.PHONY: art-pinball art-babypac
art-pinball: $(B)/art-pinball.d64 $(B)/art-pinball.d71 $(B)/test-bot.d64
	cp $(B)/art-pinball.d64 $(B)/art-pinball.d71 release/
art-babypac: $(B)/art-babypac.d64 $(B)/art-babypac.d71 $(B)/test-auto.d64
	cp $(B)/art-babypac.d64 $(B)/art-babypac.d71 release/

# ---------------------------------------------------------------- table v2
# "faithful layout" table (tools/mktable2.py, pinball.s -D TABLE2). Images:
# release/art2-pinball.d64/.d71 with BABY PAC-MAN and PINBALL on the v2 table.
$(B)/table2_data.s: tools/mktable2.py tools/artlib.py | $(B)
	python3 tools/mktable2.py $@ > $(B)/table2_map.txt
$(B)/pinball2.o: src/pinball/pinball.s $(B)/table2_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -D TABLE2=1 -o $@ $<
$(B)/pinball2-bot.o: src/pinball/pinball.s $(B)/table2_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -D TABLE2=1 -D BOT=1 -o $@ $<
$(B)/pbmain2.o: src/pinball/pbmain.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -D TABLE2=1 -o $@ $<
$(B)/pinball2.prg: $(B)/pbmain2.o $(B)/pinball2.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/pinball2.map -Ln $(B)/pinball2.lbl $(B)/pbmain2.o $(B)/pinball2.o $(LIBOBJ)
$(B)/pinball2-bot.prg: $(B)/pbmain2.o $(B)/pinball2-bot.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/pinball2-bot.map -Ln $(B)/pinball2-bot.lbl $(B)/pbmain2.o $(B)/pinball2-bot.o $(LIBOBJ)
$(B)/babypac2.prg: $(B)/main3.o $(B)/maze.o $(B)/pinball2.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/babypac2.map -Ln $(B)/babypac2.lbl $(B)/main3.o $(B)/maze.o $(B)/pinball2.o $(LIBOBJ)
$(B)/babypac2-auto.prg: $(B)/main3-auto.o $(B)/maze-auto.o $(B)/pinball2-bot.o $(LIBOBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/babypac2-auto.map -Ln $(B)/babypac2-auto.lbl $(B)/main3-auto.o $(B)/maze-auto.o $(B)/pinball2-bot.o $(LIBOBJ)
$(B)/test-bot2.d64: $(B)/pinball2-bot.prg
	rm -f $@
	$(C1541) -format "bpm bot2,t4" d64 $@ -write $(B)/pinball2-bot.prg pinbot >/dev/null
$(B)/test-auto2.d64: $(B)/babypac2-auto.prg
	rm -f $@
	$(C1541) -format "bpm auto2,t5" d64 $@ -write $(B)/babypac2-auto.prg bpauto >/dev/null
$(B)/art2-pinball.d64: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man t2,a4" d64 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/art2-pinball.d71: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man t2,a4" d71 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null

.PHONY: art2-pinball
art2-pinball: $(B)/art2-pinball.d64 $(B)/art2-pinball.d71 $(B)/test-bot2.d64 $(B)/test-auto2.d64
	cp $(B)/art2-pinball.d64 $(B)/art2-pinball.d71 release/

# ---------------------------------------------------------------- sound
# art3-sound: table v2 + SID sound (siren, chomp, thwack, pings, fanfare).
# Same programs as art2-pinball built from the current source. NOTE: re-running
# art-* / art2-* targets also rebuilds them from the current source (with sound);
# the checkpointed images in release/ were not rebuilt after their checkpoints.
$(B)/art3-sound.d64: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man snd,a5" d64 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/art3-sound.d71: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man snd,a5" d71 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
.PHONY: art3-sound
art3-sound: $(B)/art3-sound.d64 $(B)/art3-sound.d71 $(B)/test-bot2.d64 $(B)/test-auto2.d64
	cp $(B)/art3-sound.d64 $(B)/art3-sound.d71 release/

# baby-pac-man: art3-sound with the maze fixed (tunnel row was walled off,
# wall lines widened and smoothed). Same four programs.
$(B)/baby-pac-man.d64: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man,bp" d64 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
$(B)/baby-pac-man.d71: $(B)/babypac2.prg $(B)/pinball2.prg $(B)/vdctest.prg $(B)/dualdemo.prg
	rm -f $@
	$(C1541) -format "baby pac-man,bp" d71 $@ -write $(B)/babypac2.prg "baby pac-man" -write $(B)/pinball2.prg pinball -write $(B)/vdctest.prg vdctest -write $(B)/dualdemo.prg dualdemo >/dev/null
.PHONY: baby-pac-man
baby-pac-man: $(B)/baby-pac-man.d64 $(B)/baby-pac-man.d71
	cp $(B)/baby-pac-man.d64 $(B)/baby-pac-man.d71 release/

run-vdctest: $(B)/tier1-diag.d64
	$(X128) -ntsc -drive9type 1571 -9 $(B)/tier1-diag.d64 -keybuf 'dload"vdctest",u9\nrun\n'
run-dualdemo: $(B)/tier1-diag.d64
	$(X128) -ntsc -drive9type 1571 -9 $(B)/tier1-diag.d64 -keybuf 'dload"dualdemo",u9\nrun\n'

clean:
	rm -rf $(B)

# ---------------------------------------------------------------- tour test
# Test build: the maze autopilot walks a route that eats every dot and crosses
# the tunnel both ways; ghosts cannot hurt. Run tests/run_tour.py on it.
$(B)/tour_data.s: tools/mktour.py tools/mkmaze.py tools/artlib.py | $(B)
	python3 tools/mktour.py $@
$(B)/maze-tour.o: src/maze/maze.s $(B)/maze_data.s $(B)/tour_data.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -I $(B) -D AUTOPLAY=1 -D AUTOTOUR=1 -o $@ $<
$(B)/main3-tour.o: src/maze/main3.s src/hw/*.inc src/lib/*.inc
	$(CA65) $(AFLAGS) -D AUTOPLAY=1 -D AUTOTOUR=1 -o $@ $<
TOUROBJ = $(B)/main3-tour.o $(B)/maze-tour.o $(B)/pinball2-bot.o $(LIBOBJ)
$(B)/babypac-tour.prg: $(TOUROBJ) $(CFG)
	$(LD65) -C $(CFG) -D MAINTOP=0xC000 -o $@ -m $(B)/babypac-tour.map -Ln $(B)/babypac-tour.lbl $(TOUROBJ)
$(B)/test-tour.d64: $(B)/babypac-tour.prg
	rm -f $@
	$(C1541) -format "bpm tour,tt" d64 $@ -write $(B)/babypac-tour.prg bptour >/dev/null
.PHONY: test-tour
test-tour: $(B)/test-tour.d64 $(B)/test-auto2.d64
	python3 -I tests/maze_clearance.py
	python3 tests/run_tour.py
	python3 tests/ghost_tunnel.py
