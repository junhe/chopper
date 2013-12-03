# regldg version 1.0.0
# a regular expression grammar language dictionary generator
# (c) Patrick Cronin 2004-2006
# pcronin@loyola.edu
#
# Permission is granted to use, alter, and distribute this
# code under the terms of the GNU Public License.  A copy
# of this license should have been included with this
# software in the file gpl.txt.  If you need a copy, please
# visit http://www.gnu.org/copyleft/gpl.html.
#
# Makefile for regldg
# 4 July 2004

COMPILE=cc -O3 -Wall -g -c
LINK=gcc -O3 -Wall -g -lm

all: alt.o altlist.o build_structs.o char_set.o data.o debug.o \
	grouplist.o grouprecord.o main.o memory.o parse_regex.o \
	program_args.o re_perm.o silist.o tnode.o vlr.o vlrlist.o
	$(LINK) alt.o altlist.o build_structs.o char_set.o data.o \
	debug.o grouplist.o grouprecord.o main.o memory.o \
	parse_regex.o program_args.o re_perm.o silist.o tnode.o \
	vlr.o vlrlist.o -o regldg -lm
alt.o: alt.h memory.h
	$(COMPILE) alt.c -o alt.o
altlist.o: altlist.h altlist.c alt.h memory.h
	$(COMPILE) altlist.c -o altlist.o
build_structs.o: build_structs.h build_structs.c grouprecord.h grouplist.h \
	vlr.h vlrlist.h
	$(COMPILE) build_structs.c -o build_structs.o
char_set.o: char_set.h char_set.c data.h debug.h memory.h parse_regex.h
	$(COMPILE) char_set.c -o char_set.o
data.o: data.h data.c memory.h silist.h
	$(COMPILE) data.c -o data.o
debug.o: debug.c debug.h data.h
	$(COMPILE) debug.c -o debug.o
grouplist.o: grouplist.h grouplist.c grouprecord.h memory.h
	$(COMPILE) grouplist.c -o grouplist.o
grouprecord.o: grouprecord.h grouprecord.c memory.h tnode.h
	$(COMPILE) grouprecord.c -o grouprecord.o
main.o: main.c data.h char_set.h parse_regex.h program_args.h tnode.h
	$(COMPILE) main.c -o main.o
memory.o: memory.c memory.h
	$(COMPILE) memory.c -o memory.o
parse_regex.o: parse_regex.h parse_regex.c data.h debug.h memory.h \
	silist.h
	$(COMPILE) parse_regex.c -o parse_regex.o
program_args.o: program_args.c program_args.h char_set.h data.h debug.h \
	memory.h parse_regex.h
	$(COMPILE) program_args.c -o program_args.o
re_perm.o: re_perm.h re_perm.c char_set.h memory.h
	$(COMPILE) re_perm.c -o re_perm.o
silist.o: silist.h silist.c memory.h
	$(COMPILE) silist.c -o silist.o
tnode.o: tnode.c tnode.h memory.h silist.h
	$(COMPILE) tnode.c -o tnode.o
vlr.o: vlr.h vlr.c memory.h
	$(COMPILE) vlr.c -o vlr.o
vlrlist.o: vlrlist.h vlrlist.c vlr.h memory.h
	$(COMPILE) vlrlist.c -o vlrlist.o


clean:
	rm -f *~; rm -f core; rm -f log; rm -f regldg; rm -f *.o
