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

#include "Logger.h"
using namespace std;

#define MYBLOCKSIZE 4096
Logger *logger;

void punch_file(char *filepath, char *confpath)
{
    int ret;
    int fd;
    off_t off, len;
    int id;
    int flag;
    
    fd = open(filepath, O_RDWR|O_CREAT, 0666);
    if ( fd == -1 ) {
        //perror("open file");
        logger->write( strerror(errno) );
        delete logger;
        exit(1);
    } else {
        printf("file opened!\n");
    }
    
    ifstream conffile (confpath);
    if ( !conffile.is_open() ) {
        cout << "cannot open " << confpath << endl;
        logger->write( strerror(errno) );
        delete logger;
        exit(2);
    }

    id = 0;
    conffile >> off >> len;
    //cout << id << ":" << off << " " << len << endl;
    while ( off != -1 && len != -1 ) {
        if ( id == 0 ) {
            // first pair is used to 
            // allocate the whole file size
            flag = 0;
        } else {
            flag = FALLOC_FL_PUNCH_HOLE | FALLOC_FL_KEEP_SIZE;
        }
        ret = fallocate(fd, flag, off, len);
        if ( ret == -1 ) {
            //perror("failed to fallocate:");
            logger->write( strerror(errno) );
            delete logger;
            exit(1);
        }
        id++;
        conffile >> off >> len;
        //cout << id << ":" << off << " " << len << endl;
    }
   
    conffile.close();
    close(fd);
}

ssize_t pwrite_loop(int fd, const void *buf, size_t count, off_t offset)
{
    size_t nleft, wsize;
    int ret;
    off_t cur_off;

    nleft = count;
    cur_off = offset;
    while (nleft > 0) {
        // write at most a page at a time
        if ( nleft > MYBLOCKSIZE ) {
            wsize = MYBLOCKSIZE;
        } else {
            wsize = nleft;
        }
        ret = pwrite(fd, buf, wsize, cur_off);
        if ( ret == -1 ) {
            logger->write( strerror(errno) );
            delete logger;
            exit(1);
        }
        nleft -= ret;
        cur_off += ret;
    }
    return count;
}

void pad_file(char *filepath, char *confpath)
{
    char buf[MYBLOCKSIZE];
    int fd;
    off_t off, len;
    int id;
    off_t cur_hole_start, cur_hole_end, prev_hole_end;
    size_t i;
    off_t filesize;
    
    fd = open(filepath, O_RDWR|O_CREAT, 0666);
    if ( fd == -1 ) {
        //perror("open file");
        logger->write( strerror(errno) );
        delete logger;
        exit(1);
    } else {
        printf("file opened!\n");
    }
    
    ifstream conffile (confpath);
    if ( !conffile.is_open() ) {
        cout << "cannot open " << confpath << endl;
        logger->write( strerror(errno) );
        delete logger;
        exit(2);
    }

    id = 0;
    conffile >> off >> len;
    //cout << id << ":" << off << " " << len << endl;

    // initialize the buffer
    for ( i = 0; i < MYBLOCKSIZE; i++ ) {
        buf[i] = 'z'; 
    }
    
    //cout << "before loop.." << endl;
    while ( off != -1 && len != -1 ) {
        if ( id == 0 ) {
            // first pair is used to 
            // allocate the whole file size
            // safely ignore it since we don't need
            // to allocate the whole file at the beginning
            filesize = len;

            cur_hole_start = 0;
            cur_hole_end   = 0;
        } else {
            cur_hole_start = off;
            cur_hole_end = off + len;

            // no need to check error code of this one
            // it survives or die hard
            size_t wlen;
            off_t  woff;
            woff = prev_hole_end;
            wlen = cur_hole_start - prev_hole_end;
            //cout << woff << ":" << wlen << endl;
            pwrite_loop(fd, buf, wlen, woff);
        }

        // prepare for the next iteration
        prev_hole_end = cur_hole_end;
        id++;
        conffile >> off >> len;
        //cout << id << ":" << off << " " << len << endl;
    }

    // now need to seal the file end
    //cout << prev_hole_end << ":" << filesize - prev_hole_end << endl;
    pwrite_loop(fd, buf, filesize - prev_hole_end, prev_hole_end);

    conffile.close();
    close(fd);
}

int main(int argc, char **argv)
{
    logger = new Logger("/tmp/puncher.log");
    if (argc != 4) {
        printf("Usage: %s filepath confpath mode\n"
               "mode: 0: hole punching; 1: pad_file\n",
               argv[0]);
        logger->write( "Wrong program arguments" );
        delete logger;
        exit(1);
    }
    char *filepath = argv[1];
    char *confpath = argv[2];
    int punchmode = atoi(argv[3]);

    if ( punchmode == 0 ) {
        punch_file(filepath, confpath);
    } else {
        pad_file(filepath, confpath);
    }

    delete logger;
    return 0;
}


