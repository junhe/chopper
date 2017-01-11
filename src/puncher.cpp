/*
 *  Chopper is a diagnostic tool that explores file systems for unexpected
 *  behaviors. For more details, see paper Reducing File System Tail 
 *  Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
 * 
 *  Please send bug reports and questions to jhe@cs.wisc.edu.
 *
 *  Written by Jun He at University of Wisconsin-Madison
 *  Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */
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
#include <assert.h>
#include <unistd.h>

#include "Logger.h"
using namespace std;


/*
 This program takes configuration in the following
 format:
 
 0 filesize
 hole-offset hole-length
 hole-offset hole-length
 ...
 -1 -1 //mark the end

 if filesize == -2, hole punching component will
 skip the step of falloate file. 
 */



#define MYBLOCKSIZE 4096
#define MAX_CHUNK_SIZE 8388608  //8MB
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

        // actually do the fallocate() if needed
        // if id == 0 and len == -2, the fallocate()
        // is skipped.
        if ( !(id == 0 && len == -2) ) {
            ret = fallocate(fd, flag, off, len);
            if ( ret == -1 ) {
                //perror("failed to fallocate:");
                ostringstream oss;
                oss << "id:" << id << "msg:" << strerror(errno) << endl;
                logger->write( oss.str().c_str() );
                delete logger;
                exit(1);
            }
        }
        id++;
        conffile >> off >> len;
        //cout << id << ":" << off << " " << len << endl;
    }
   
    conffile.close();
    close(fd);
    cout << "file punched successfully!" << endl;
}

ssize_t pwrite_loop(int fd, const void *buf, 
                    size_t count, off_t offset)
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

// buf has to be at least the size of max_chunk_size
ssize_t pwrite_loop_maxchunk(int fd, const void *buf, 
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



void fill_file(const char *filepath, off_t filesize)
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
        //printf("file opened!\n");
    }
    
    // initialize the buffer
    buf = (char *)malloc(MAX_CHUNK_SIZE);
    if ( buf == NULL ) {
        logger->write( "failed to malloc()" );
        logger->write( strerror(errno) );
        delete logger;
        exit(1);
    }
    memset(buf, 'z', MAX_CHUNK_SIZE);
    
    pwrite_loop_maxchunk(
            fd, buf, filesize, 0, MAX_CHUNK_SIZE);

    free(buf);
    fsync(fd);
    close(fd);
}

int file_exists(const char *filepath) 
{
    struct stat buffer;
    int         ret;
    ret = stat(filepath, &buffer);
    return !ret; //0 indicates existence
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
            // when padding
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
            fsync(fd);
            
            //if ( id % 2 == 0 ) {
                //if ( file_exists("/mnt/scratch/holeholder1") ) {
                    //unlink("/mnt/scratch/holeholder1");
                //}
                //fill_file("/mnt/scratch/holeholder0", len);
            //} else {
                //if ( file_exists("/mnt/scratch/holeholder0") ) {
                    //unlink("/mnt/scratch/holeholder0");
                //}
                //fill_file("/mnt/scratch/holeholder1", len);
            //}
            char filename[128];
            sprintf(filename, "%s.placeholder%d", filepath, id);
            fill_file(filename, len);
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
               "mode: 0=hole punching, 1=pad_file\n"
               "padding is an experimental way of creating fragmentations.\n"
               " It keeps creating new files while writing an original one,\n"
               " hoping it will create fragment size as desired. It failed.\n",
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


