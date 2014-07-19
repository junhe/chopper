#include <stdio.h>
#include <iostream>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <linux/falloc.h>
#include <fcntl.h>
#include <stdlib.h>
#include <fstream>
#include <string.h>
#include <errno.h>
#include <sstream>

#include "Logger.h"
using namespace std;

#define MYBLOCKSIZE 4096
#define MAX_CHUNK_SIZE 8388608  //8MB
Logger *logger;

// buf has to be at least the size of max_chunk_size
ssize_t pwrite_loop(int fd, const void *buf, 
                    size_t count, off_t offset,
                    size_t max_chunk_size)
{
    size_t nleft, wsize;
    int ret;
    off_t cur_off;

    nleft = count;
    cur_off = offset;
    while (nleft > 0) {
        // write at most a page at a time
        if ( nleft > max_chunk_size ) {
            wsize = max_chunk_size;
        } else {
            wsize = nleft;
        }
        ret = pwrite(fd, buf, wsize, cur_off);
        if ( ret == -1 ) {
            ostringstream oss;
            oss << "len:" << count 
                << " offset:" << offset 
                << "msg:" << strerror(errno) << endl;
            logger->write( oss.str().c_str() );
            delete logger;
            exit(1);
        }
        nleft -= ret;
        cur_off += ret;
    }
    return count;
}


void fill_file(char *filepath, off_t filesize)
{
    char *buf;
    int fd;
    
    fd = open(filepath, O_RDWR|O_CREAT, 0666);
    if ( fd == -1 ) {
        //perror("open file");
        logger->write( strerror(errno) );
        delete logger;
        exit(1);
    } else {
        printf("file opened!\n");
    }
    
    // initialize the buffer
    buf = (char *)malloc(MAX_CHUNK_SIZE);
    if ( buf == NULL ) {
        logger->write( strerror(errno) );
        delete logger;
        exit(1);
    }
    memset(buf, 'z', MAX_CHUNK_SIZE);
    
    pwrite_loop(fd, buf, filesize, 0, MAX_CHUNK_SIZE);

    close(fd);
}


int main(int argc, char **argv)
{
    logger = new Logger("/tmp/filefiller.log");
    if (argc != 3) {
        printf("Usage: %s filepath size-in-bytes\n"
               "This program creates file using chunks as"
               "large as possible (up to 8MB)\n",
               argv[0]);
        logger->write( "Wrong program arguments" );
        delete logger;
        exit(1);
    }
    char *filepath = argv[1];
    long long size = atoll(argv[2]);

    fill_file( filepath, size );

    delete logger;
    return 0;
}




