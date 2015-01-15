#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <iostream>

#include "Util.h"

using namespace std;

#define BLOCKSIZE 4096

int readfile(char *fpath, int fsize)
{
    int bytes_done = 0;
    int ret;
    int fd;
    char buf[BLOCKSIZE];

    fd = open(fpath, O_RDONLY);
    if ( fd == -1 ) {
        cout << "error open " << fpath << " for reading" << endl;
        exit(1);
    }
    
    while ( bytes_done < fsize ) {
        ret = read(fd, buf, BLOCKSIZE);
        if ( ret == -1 ) {
            perror("file reading. error");
            exit(1);
        }
        if ( ret == 0 && bytes_done != fsize ) {
            cout << "bytes_done:" << bytes_done << endl;
            cout << "fsize:"      << fsize << endl;
            exit(1);
        }
        bytes_done += ret;
    }
    close(fd);
    //cout << "final bytes_done:" << bytes_done << endl;
    return bytes_done;
}

int writefile(char *fpath, int fsize)
{
    int bytes_left = fsize;
    int ret;
    int fd;
    char buf[BLOCKSIZE];

    memset(buf, 'z', BLOCKSIZE);

    fd = open(fpath, O_WRONLY|O_CREAT, 0666);
    if ( fd == -1 ) {
        perror("open file for writing");
        exit(1);
    }
    
    while ( bytes_left > 0 ) {
        ret = write(fd, buf, 
                    bytes_left > BLOCKSIZE? BLOCKSIZE : bytes_left);
        if ( ret == -1 ) {
            perror("file writing. error");
            exit(1);
        }
        bytes_left -= ret;
    }
    fsync(fd);
    close(fd);
    return 0;
}

int main(int argc, char **argv)
{
    char mode;
    int fsize;
    struct timeval start;
    double dur;
    char *filepath, *filepaths, *tofree;
    Performance perf;

    if ( argc != 6 ) {
        cout << "usage: ./me r|w filepaths filesize addition-head additional-datarow" << endl;
        cout << "example: ./perform w /tmp/myfile1,/tmp/myfile2 1024 'hello hellodata' 'echo echodata'" << endl;
        exit(1);
    }
    
    mode = argv[1][0];
    tofree = filepaths = strdup(argv[2]);
    fsize = atoi(argv[3]);
    
    start_timer(&start);

    while ((filepath = strsep(&filepaths, ",")) != NULL) {
        if ( mode == 'r' )
            readfile(filepath, fsize);
        else
            writefile(filepath, fsize);
    }

    dur = end_timer_get_duration(&start);

    perf.put("duration", dur);
    perf.put("filesize", fsize);
    perf.put("mode", argv[1]);
    perf.put(argv[4], argv[5]);
    cout << perf.showColumns();

    free(tofree);
}




