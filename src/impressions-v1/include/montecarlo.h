#include <map>
#include <string>
#include <iostream>
#include <list>
#include <sys/time.h>
#include <unistd.h> 
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include "posix_lib.h"
int montecarlo (int);
int flat_tree (int);
int deep_tree (int);
int my_gettimeofday();
