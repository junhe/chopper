#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

int main()
{
    int fd;
    int hole, size, off;
    char buf[4096];

    
    hole = 1024*1024;
    size = 4096;


    fd = open("/tmp/tmpfile", O_WRONLY);
    
    off = 0;
    pwrite(fd, buf, 1, off);
    fsync(fd);

    off = size+hole;
    pwrite(fd, buf, 1, off);
    fsync(fd);

    off = size+hole;
    pwrite(fd, buf, 1, off);
    fsync(fd);

    close(fd);
}



