
/* Copyright notice

Copyright 2009, 2010 Nitin Agrawal
nitina@cs.wisc.edu
Developed at the University of Wisconsin-Madison.

This file is part of Impressions.

Impressions is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Impressions is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Impressions.  If not, see <http://www.gnu.org/licenses/>.

GNU General Public License in file named COPYING

*/


#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <sys/time.h>

#include "montecarlo.h"
#include "impress.h"
#include "fragment.h"

/*  *************************************************************
    Fragment is called according to the fragment schedule:
    For a 0.N layout score, create a seek
    after every N blocks written. e,g, if you
    are writing 10 blocks and want 0.9 layout
    insert a seek after block 9. this seek
    is created by creating a file and deleting
    it the next time. You need two files to be 
    created/deleted alternately 
 ************************************************************/

int fragment(int turn) {

    int ret=0;
    char strerr[100];
    char fragfile1[100], fragfile2[100];
    sprintf(fragfile1, "%s/fragfile1", PARENT_PATH);
    sprintf(fragfile2, "%s/fragfile2", PARENT_PATH);

    if (turn==-1) {

        // end of file cleanup
        print_debug(0,"Clean up ...");
        make_frag_file(fragfile1, 1024*1024*1);

        if((ret=pos_unlink(fragfile2))<0) 
            print_debug(0,"Error deleting fragmentfile2 %d %s\n", ret, strerror_r(errno, strerr, 100));

        return 1;
    }
    if (turn % 2 ==0) {
        print_debug(0,"creating file2, del file 1 : ");
        make_frag_file(fragfile2, 1024*1024*1); // create a 1MB file: size of file can be changed if needed

        if((ret = pos_unlink(fragfile1))<0) 
            print_debug(0,"Error deleting fragmentfile1 %d %s\n", ret, strerror_r(errno, strerr, 100));
    }
    else {
        print_debug(0,"creating file1, del file 2 : ");
        make_frag_file(fragfile1, 1024*1024*1); // create a 1MB file: size of file can be changed if needed

        if((ret=pos_unlink(fragfile2))<0) 
            print_debug(0,"Error deleting fragmentfile2 %d %s\n", ret, strerror_r(errno, strerr, 100));
    }
}

int make_frag_file(char * filepath, long double size) {

    int j=0;
    char buf[MY_BLOCK_SIZE], strerr[100];
    long double written = 0.0;
    long double temp_write = 0.0;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;
    FILE *fp;

    for(j=0; j< MY_BLOCK_SIZE; j++) {
        buf[j]= '\0';
    }   

    if((fp = fopen(filepath,"wb"))==NULL ) { 
        print_debug(0,"Error: Unable to create file= %s %d\n", filepath, errno);
    }   
    else {
        written = 0;
        while(written < size) {
            if (size - written < MY_BLOCK_SIZE) {
                temp_write = (long double)fwrite((void*)buf,(size_t)(size-written), 1, fp);
                written+=temp_write*(size-written);
            }
            else {
                temp_write =(long double)fwrite((void*)buf,(size_t)(MY_BLOCK_SIZE), 1, fp);
                written+=temp_write*MY_BLOCK_SIZE;
            }
        }
        fclose(fp);
    }
    return 1;
}
