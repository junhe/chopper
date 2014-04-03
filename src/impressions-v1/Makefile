CC = g++
CFLAGS = -g 
#-pg
LFLAGS = -lm
CFLAGS += -I./include/

all:	impress
impress: 	word.o get_spec.o extension.o posix_lib.o montecarlo.o impress.o fragment.o depth.o ssp.o
	$(CC) $(CFLAGS) $(LFLAGS) word.o impress.o posix_lib.o get_spec.o extension.o montecarlo.o fragment.o depth.o ssp.o\
		-o impressions

montecarlo.o:	montecarlo.cpp 
	$(CC) $(CFLAGS) -c montecarlo.cpp
get_spec.o:	get_spec.cpp 
	$(CC) $(CFLAGS) -c get_spec.cpp
word.o:	word.cpp 
	$(CC) $(CFLAGS) -c word.cpp
extension.o:	extension.cpp
	$(CC) $(CFLAGS) -c extension.cpp
impress.o:	impress.cpp
	$(CC) $(CFLAGS) -c impress.cpp
posix_lib.o:	posix_lib.cpp
	$(CC) $(CFLAGS) -c posix_lib.cpp
fragment.o:	fragment.cpp
	$(CC) $(CFLAGS) -c fragment.cpp
depth.o:	depth.cpp
	$(CC) $(CFLAGS) -c depth.cpp
ssp.o:	ssp.cpp
	$(CC) $(CFLAGS) -c ssp.cpp
clean: 
	rm -f *.o *~ impressions
