# Define required macros here
SHELL=/bin/sh

OBJS=
CFLAGS=-Wall -D_FILE_OFFSET_BITS=64
CC=g++
INCLUDES=
LIBS=-lpthread

all: perform

perform: perform.o Util.o
	${CC} ${CFLAGS} ${INCLUDES} -o $@ Util.o perform.o ${LIBS}

seqorrandom: seqorrandom.cpp Util.o
	${CC} ${CFLAGS} ${INCLUDES} -o $@ Util.o seqorrandom.o ${LIBS}

clean:
	-rm -f *.o core *.core *.gch

.cpp.o:
	${CC} ${CFLAGS} ${INCLUDES} -c $<
