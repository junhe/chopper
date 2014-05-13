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

int main(int argc, char **argv)
{
    logger = new Logger("/tmp/puncher.log");
    if (argc != 3) {
        printf("Usage: %s filepath confpath\n", argv[0]);
        logger->write( "Wrong program arguments" );
        delete logger;
        exit(1);
    }
    char *filepath = argv[1];
    char *confpath = argv[2];

    punch_file(filepath, confpath);

    delete logger;
    return 0;
}


