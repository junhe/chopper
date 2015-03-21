#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    int fd;
    int size, off;
    char buf[4096];

    size = 4096;

    fd = open(argv[1], O_WRONLY|O_CREAT);
    if ( fd == -1 ) {
        perror("opening file");
        exit(1);
    }
    
    off = 60*1024;
    pwrite(fd, buf, size, off);
    printf("wrote at %d, size %d bytes\n", off, size);
    fsync(fd);

    off = off - size;
    pwrite(fd, buf, size, off);
    printf("wrote at %d, size %d bytes\n", off, size);
    fsync(fd);

    off = off - size;
    pwrite(fd, buf, size, off);
    printf("wrote at %d, size %d bytes\n", off, size);
    fsync(fd);

    off = off - size;
    pwrite(fd, buf, size, off);
    printf("wrote at %d, size %d bytes\n", off, size);
    fsync(fd);

    off = off - size;
    pwrite(fd, buf, size, off);
    printf("wrote at %d, size %d bytes\n", off, size);
    fsync(fd);

    close(fd);
    sync();

}



