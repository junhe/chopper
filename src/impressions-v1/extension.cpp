
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


#include "impress.h"
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include "math.h"
#include "classes.h"
#include "montecarlo.h"
#include "word.h"
#include "fragment.h"

#define EXT_SIZE 3
#define NUM_EXTENSIONS 19


/* In order to create certain typed files
   Impressions makes use of  helper programs,
   if a helper program is not installed, then
   the corresponding file type creation will
   fail and Impressions will resort to a 
   binary file creation instead. 
   EXT_HELPERS specifies the location where
   extension_helper binaries are available
*/
#define EXT_HELPERS "./extension_helpers"

#define NUL 0
#define TXT 1
#define JPG 2 
#define EXE 3
#define CPP 4
#define HTM 5
#define H   6
#define DLL 7
#define GIF 8
#define PDB 9
#define PST 10
#define PCH 11
#define MP3 12
#define LIB 13
#define WMA 14
#define VHD 15
#define PDF 16
#define MPG 17
#define TAL 18  // all files falling in the tail

/* Timer variables for different components */

extern struct timeval main_time_start, main_time_end, \
               dirtree_start, dirtree_end, \
               filecontent_start, filecontent_end, \
               filesize_start, filesize_end, \
               word_model_start, word_model_end, \
               extension_start, extension_end, \
               aging_start, aging_end, \
               file_creation_start, file_creation_end;

extern double main_time_total, dirtree_total, filecontent_total, \
               word_model_total, extension_total, aging_total, \
               file_creation_total, filesize_total;

extern Random rv_extension;

/* (100-sum of all ext popularities): the LONG_TAIL represents the popularity
of all remaining exts that Impressions currently does not support. 
In the absense of accounting for the long tail, the relative popularity 
of all other extensions artificially increases.

The extension .tal reresents all file extensions belonging to the tail,
however for applications where one would not want to represent all the 
remainder of extension by a single .tal, Impressions can generate 
random substitutes instead.
*/

#define LONG_TAIL 47.35
#define UNKNOWN 1.0
//#define PRINT

/* change NUM_EXTENSIONS when changing this array */
char extension_array[][4] = {"nul", "txt", "jpg", "exe", "cpp", "htm", "h__", "dll", "gif", "pdb", "pst", "pch", "mp3", "lib", "wma", "vhd", "pdf","mpg","tal" };
char extension_header[][100] = {"", "", "FFD8\n", "", "", "", "",  "", "GIF89a\n", "", "", "", "", "", "", "",  "%PDF-1.4\n", "", "" };
float extension_popularity_large[] = {7.79, 5.02, 1.45, 2.08, 4.88, 3.24, 9.32, 3.64, 3.43, 1.94, 0.00, 0.10, 0.16, 1.76, 0.19, 0.01, 0.04, 0.00, 0.00};
float extension_popularity_default[] = {6.91, 3.64, 3.08, 2.88, 3.26, 4.45, 6.69, 6.63, 6.77, 1.34, UNKNOWN, UNKNOWN, UNKNOWN, 1.46, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN, LONG_TAIL};
int TOTAL_POPULARITY=0;
extern int ACTUAL_LOG_CREATION;
//float extension_popularity[NUM_EXTENSIONS];
float * extension_popularity;



/* ****************************************************

   Initialize extension popularity: Don't use sf_large2small
   for the most part stick to default

   **************************************************** */

int init_ext_popularity() {

    if(IMP_input->Flag[sf_large2small]==1) {

        // set values for large file systems
        TOTAL_POPULARITY = 4405; // for large FS
        extension_popularity = extension_popularity_large;
        print_debug(0,"file ext for large FS %f\n", extension_popularity[0]);
    }                    
    else {

        TOTAL_POPULARITY = 10000; // (45.65 + 7*UNKNOWN + LONG_TAIL) *100
        extension_popularity = extension_popularity_default;
    }
}

/* ****************************************************

   Extension name corresponding to the extension number
   in the array

   **************************************************** */
int ext_extnum (char *ext){
    
    if(strcmp(ext, "-1")==0) { // extension bias not needed
        return -1;
    }
    for (int i =0; i < NUM_EXTENSIONS; i++){
        if(strcmp(extension_array[i], ext)==0) {
            return i;
        }
    }
    print_debug(0,"Extension %s not supported!\n", ext);
    return -1;
}


/* ****************************************************

    compare two long doubles

   **************************************************** */
int compfunc(const void *x, const void *y)
{
   long double pp,qq;
   int t;
   pp = (long double)(*(long double *)x);
   qq = (long double)(*(long double *)y);
   print_debug(0,"%d %d\n", pp, qq);
   if (pp < qq) t = -1;
   else if (pp == qq) t = 0;
   else  t = 1;
   return t;
}


/* ****************************************************

    Find the file extension according to count popularity

   **************************************************** */
int montecarlo_extension() {
    
    /* relative popularity of extensions*/
    // srand(deseeder());
    
    int i=0;
    int token = rv_extension.uniformDiscrete(0, TOTAL_POPULARITY-1);

    float token_until_now=extension_popularity[i]*100;
    while (token_until_now < token) {
        i++;
        token_until_now+=extension_popularity[i]*100;
    }
    
    // At this point, extension_array[i] is the extension
    return i;
}


int get_random_ext(char *random_ext) {

   char rand_char;
    
   for(int wc =0; wc < 3; wc ++) {
        rand_char = ( rand()% 26);
        print_debug(0, "%d %c ", rand_char, (char) (rand_char+97 ));
        random_ext[wc] = (char) (rand_char+97);
    }
    
    return 1;
}

/* ****************************************************

    Function that generates all files.

   **************************************************** */
long double make_generic_file(char * filepath, long double size, int depth, FILE * fp_log) {

    int header_size=0;
    char header[1024];
    char ext[3], full_filepath[1024], helperexec[1024];
    char cmd[1024], args[1024];
    int ext_number;
    
    __Ntime gettimeofday(&extension_start, NULL);

    /* Either the extension is specified directly
    by the user, or one is chosen according to the 
    count popularity */
    
    if(IMP_input->Flag[sf_ext] >=0)
        ext_number = IMP_input->Flag[sf_ext];
    else 
        ext_number = montecarlo_extension();
    

    __Ntime gettimeofday(&extension_end, NULL);
    __Ntime extension_total += diff_time(extension_start, extension_end);

    /* If the tail is chosen, generate a random extension */
    if(ext_number == NUM_EXTENSIONS - 1 ) { 
        get_random_ext(ext);
        print_debug(0, "Tail file selected %d %s\n", ext_number, ext);
    }
    else { 
        strcpy(ext, extension_array[ext_number]);
        print_debug(0, "Non Tail file selected %d %s\n", ext_number, ext);
    }

    if(IMP_input->Printwhat[pw_ext]==1) {
        print_debug(0,"Extension: %s\n", ext);
    }

    if(ext_number)
        sprintf(full_filepath, "%s.%s", filepath, ext); //extension_array[ext_number]);
    else if (ext_number ==0) {
        sprintf(full_filepath, "%s", filepath);
        
        /*If you want a ".nul" instead of just a file without any extension,
        use the following line instead*/
        //sprintf(full_filepath, "%s.%s", filepath, extension_array[ext_number]);
    }

    print_debug(0,"File: %s\n",full_filepath);
    
    if(ACTUAL_LOG_CREATION)
    {
        if(!fprintf(fp_log, "%s %d %Lf %d %s\n", ext, ext_number, size, depth, full_filepath))
            print_debug(0,"LOG FILE from impress not being written!\n");
    }
    
    /* If files and dirs are both being created on disk:
       Generate ascii, binary, or typed file according to file extension
    */
    if(IMP_input->Actualfilecreation == 1) {
        switch(ext_number) {
            case NUL: 
            case TXT: 
            case CPP: 
            case H:
                make_ascii_file(full_filepath, size, -1); 
                break;    
            case GIF:
                /* Create a gif file using the gif extension helper */
                __Ntime gettimeofday(&file_creation_start, NULL);
                sprintf(helperexec, "%s/%s",  EXT_HELPERS, "gif");
                sprintf(cmd, "%s/%s %s %d %d", EXT_HELPERS, "gif", full_filepath, 1000, 1000);
                size = 1757;
                if(access(helperexec, X_OK) == 0)
                    system(cmd);
                else {
                    print_debug(0, "EXT_HELPER: gif not available, resorting to binary file\n");
                    make_binary_file(full_filepath, size, -1);
                }
                __Ntime gettimeofday(&file_creation_end, NULL);
                __Ntime file_creation_total += diff_time(file_creation_start, file_creation_end);
                break;
            case MP3:
                /* Create a mp3 file using the mp3 extension helper */
                make_binary_file(full_filepath, size, -1);
                __Ntime gettimeofday(&file_creation_start, NULL);
                sprintf(args, "-a \"Test Artist\" -A \"Test Album\" -t \"Test Song Title\" -c \" Impressions File MP3\" -g \"POP\" -y \"2007\" -T \"1\"");
                sprintf(helperexec, "%s/%s",  EXT_HELPERS, "mp3");
                sprintf(cmd, "%s/%s %s %s",EXT_HELPERS, "mp3", args, full_filepath);
                if(access(helperexec, X_OK) == 0)
                    system(cmd);
                else {
                    print_debug(0, "EXT_HELPER: mp3 not available, resorting to binary file\n");
                }
                __Ntime gettimeofday(&file_creation_end, NULL);
                __Ntime file_creation_total += diff_time(file_creation_start, file_creation_end);
                break;
            case LIB:
            case VHD:
            case EXE:
            case PDB:
            case DLL:
            case TAL:   // tail file group, individual ext right now not factored
                make_binary_file(full_filepath, size, -1); // binary file
                break;
            case WMA:
            case PST:
            case PCH:
                // temporary solution, not creating a perfect PCH file
                make_binary_file(full_filepath, size, -1); // binary file
                break;
            case JPG:
                __Ntime gettimeofday(&file_creation_start, NULL);
                sprintf(helperexec, "%s/%s",  EXT_HELPERS, "gif");
                sprintf(cmd, "%s/%s %s %d %d", EXT_HELPERS, "gif", "temp.gif", 1000, 1000);
                size = 1757;
                if(access(helperexec, X_OK) == 0) {
                    system(cmd);
                    sprintf(cmd, "giftopnm temp.gif > temp.pnm");
                    system(cmd);
                    sprintf(cmd, "pnmtojpeg temp.pnm > %s", full_filepath);
                    system(cmd);
                }
                else {
                    print_debug(0, "EXT_HELPER: gif not available, resorting to binary file\n");
                    make_binary_file(full_filepath, size, -1);
                }
                __Ntime gettimeofday(&file_creation_end, NULL);
                __Ntime file_creation_total += diff_time(file_creation_start, file_creation_end);
                break;
            case PDF:
                make_binary_file(full_filepath, size, 16); 
                break;
            case HTM:
                make_ascii_file(full_filepath, size, -1); 
        }
    }
    return size;
}

/* ****************************************************

    Function that generates a binary file.

   **************************************************** */
int make_binary_file(char * filepath, long double size, int extension_num) {
    
    long double blocks_written=0;
    int num_seeks=0, turn =0, seeker=0;
    long double * frag_schedule_array;
    long double num_blocks = ceill(size/MY_BLOCK_SIZE);
    double min_blocks_needed=0.0;

    char buf[MY_BLOCK_SIZE], strerr[100];
    long double written = 0.0;
    long double temp_write = 0.0;
    int is_garbage =0, j=0;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;
    FILE *fp;
    
    int write_iter =0;

    __Ntime gettimeofday(&filecontent_start, NULL);
    
    for(j=0; j< MY_BLOCK_SIZE; j++) {
        buf[j]= '\0';
    }
    __Ntime gettimeofday(&filecontent_end, NULL);
    __Ntime filecontent_total += diff_time(filecontent_start, filecontent_end);
    
    
    if(is_garbage ==1) {
        buf[0]='I';
        buf[1]='M';
        buf[2]='P';
        buf[3]='R';
        buf[4]='E';
        buf[5]='S';
        buf[6]='S';
    }
    
    if(IMP_input->Layoutscore < 1) {
        double fragment_degree = 1 - IMP_input->Layoutscore;
        min_blocks_needed = (double) ceil(1/fragment_degree);
        if(num_blocks>= min_blocks_needed) {
            num_seeks = (int) ((fragment_degree*num_blocks -floor(fragment_degree*num_blocks) <= 0.5) ? \
                            floor(fragment_degree*num_blocks):ceil(fragment_degree*num_blocks));
            if(num_seeks!=0){
                frag_schedule_array = (long double*) malloc(sizeof(long double)*num_seeks);
                #ifdef PRINT
                if(frag_schedule_array!=NULL) 
                    print_debug(0,"Allocated %d, numblocks %Lf, size %Lf\n", num_seeks, num_blocks, size);
                else 
                    print_debug(0,"Allocation error\n");
                #endif
            }
            
            for(int i = 0; i < num_seeks; i++) {
                frag_schedule_array[i] = (long double) (rand()%((int)num_blocks) + 1);
                print_debug(0," - %Lf -", frag_schedule_array[i]);
            }
            
            qsort((void*) frag_schedule_array, (size_t) num_seeks, (size_t) sizeof(long double), compfunc);
            
            #ifdef PRINT 
            for(int j=0; j<num_seeks; j++) {
                print_debug(0," %Lf ", frag_schedule_array[j]);
            }
            #endif
        }
    }
    
    if((fp = fopen(filepath,"wb"))==NULL ) {
            print_debug(0,"Error: Unable to create file= %s %d\n", filepath, errno);
    }
    else { // write to file with size
        written = 0;
        // if filetype has a header, write it, e.g, PDF
        if (extension_num > 0){
            temp_write = (double) fwrite((void*)extension_header[extension_num], (size_t) (sizeof(extension_header[extension_num])),1, fp);
            written+=(long double) temp_write*sizeof(extension_header[extension_num]);
        }
            
        while(written < size) {
            
            print_debug(0, "Write iteration %d\n", write_iter++);

            __Ntime gettimeofday(&file_creation_start, NULL);
            if (size - written < MY_BLOCK_SIZE) {
                temp_write = (long double)fwrite((void*)buf,(size_t)(size-written), 1, fp);
                written+=temp_write*(size-written);
            }
            else {
                temp_write =(long double)fwrite((void*)buf,(size_t)(MY_BLOCK_SIZE), 1, fp);
                written+=temp_write*MY_BLOCK_SIZE;
            }
            __Ntime gettimeofday(&file_creation_end, NULL);
            __Ntime file_creation_total += diff_time(file_creation_start, file_creation_end);

            /* Fragment the file */
           __Ntime gettimeofday(&aging_start, NULL);
            if(num_seeks!=0 && seeker < num_seeks) {
                
                #ifdef PRINT 
                print_debug(0,"sch %Lf written %Lf\n", frag_schedule_array[seeker], blocks_written); 
                #endif

                while(frag_schedule_array[seeker]==frag_schedule_array[seeker+1])
                    seeker++; // throw away duplicates
                
                if(seeker < num_seeks && frag_schedule_array[seeker]==blocks_written) {
                    fragment(turn);
                    turn++;
                    seeker++;
                }
            }
           __Ntime gettimeofday(&aging_end, NULL);
           __Ntime aging_total += diff_time(aging_start, aging_end);
        }
        //cleanup
        if(num_seeks > 0 && turn%2==1) 
            fragment(-1);       
        fclose(fp);
    }
    if(num_seeks!=0) 
        free(frag_schedule_array);
}


/* ****************************************************

    Function that generates an ascii file.

   **************************************************** */
int make_ascii_file(char * filepath, long double size, int extension_num) {

    char buf[MY_BLOCK_SIZE], strerr[100];
    long double written = 0.0;
    long double blocks_written=0;
    int num_seeks=0, turn =0, seeker=0;
    long double * frag_schedule_array;
    int is_garbage =0, j=0;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH;
    int fd=0;
    long double num_blocks = ceill(size/MY_BLOCK_SIZE);
    double min_blocks_needed=0.0;
    int write_iter =0;

    if(is_garbage ==1) {
        buf[0]='I';
        buf[1]='M';
        buf[2]='P';
        buf[3]='R';
        buf[4]='E';
        buf[5]='S';
        buf[6]='S';
    }
    
    // get data buffer once for non word-freq
    __Ntime gettimeofday(&filecontent_start, NULL);
    
    random_word_block(buf);
    
    __Ntime gettimeofday(&filecontent_end, NULL);
    __Ntime filecontent_total += diff_time(filecontent_start, filecontent_end);
    
    if(IMP_input->Layoutscore < 1) {
        double fragment_degree = 1 - IMP_input->Layoutscore;
        min_blocks_needed = (double) ceil(1/fragment_degree);
        if(num_blocks>= min_blocks_needed) {
            num_seeks = (int) ((fragment_degree*num_blocks -floor(fragment_degree*num_blocks) <= 0.5) ? \
                        floor(fragment_degree*num_blocks):ceil(fragment_degree*num_blocks));
            if(num_seeks!=0){
                frag_schedule_array = (long double*) malloc(sizeof(long double)*num_seeks);
                
                #ifdef PRINT
                if(frag_schedule_array!=NULL) 
                    print_debug(0,"Allocated %d, numblocks %Lf, size %Lf\n", num_seeks, num_blocks, size);
                else 
                    print_debug(0,"Allocation error\n");
                #endif
            }
            
            for(int i = 0; i < num_seeks; i++) {
                frag_schedule_array[i] = (long double) (rand()%((int)num_blocks) + 1);
                print_debug(0, " - %Lf -", frag_schedule_array[i]);
            }
            
            qsort((void*) frag_schedule_array, (size_t) num_seeks, (size_t) sizeof(long double), compfunc);
            
            #ifdef PRINT 
            for(int j=0; j<num_seeks; j++) {
                print_debug(0," %Lf ", frag_schedule_array[j]);
            }
            #endif
        }
    }
       
    if((fd = pos_creat(filepath, mode)) <0) {
            strerror_r(errno, strerr, 100);
            print_debug(1,"Error: Unable to create file= %s %d\n", filepath, errno);
    }
    else { // write to file with size
        
        written = 0;
        
        // if filetype has a header, write it, e.g, PDF
        if (extension_num > 0){
            written += (long double) pos_write(fd, (void*)extension_header[extension_num],sizeof(extension_header[extension_num]));
        }
            
        while(written < size) {
          
            // get new random block everytime for wordfreq, else we already got it once above
            if(IMP_input->Flag[sf_wordfreq] >=1) {
                __Ntime gettimeofday(&filecontent_start, NULL);
                random_word_block(buf);
                __Ntime gettimeofday(&filecontent_end, NULL);
                __Ntime filecontent_total += diff_time(filecontent_start, filecontent_end);
           }
           
            print_debug(0, "Write iteration %d\n", write_iter++);
          
           __Ntime gettimeofday(&file_creation_start, NULL);
           print_debug(0,"random block : %s\n", buf);
            if (size - written < MY_BLOCK_SIZE) {
                print_debug(0,"%s, %f, %f\n", filepath, size - written, size);
                written+=(long double)pos_write(fd,(void*)buf,(size_t)(size-written));
                blocks_written+=1; // assumes previous pos_write wrote an entire block as issued

                print_debug(0,"Blocks to file %s,%f,%d\n",filepath,written,MY_BLOCK_SIZE);
            }
            else {
                written += (long double) pos_write(fd, (void*) buf, MY_BLOCK_SIZE);
                blocks_written+=1; // assumes previous pos_write wrote an entire block as issued
                print_debug(0,"Blocks to file %s, %f\n", filepath, written);
            }
           __Ntime gettimeofday(&file_creation_end, NULL);
           __Ntime file_creation_total += diff_time(file_creation_start, file_creation_end);
                
            /* Fragment the file in this loop */
           __Ntime gettimeofday(&aging_start, NULL);
            if(num_seeks!=0 && seeker < num_seeks) {
                
                print_debug(0,"sch %Lf written %Lf\n", frag_schedule_array[seeker], blocks_written); 

                while(frag_schedule_array[seeker]==frag_schedule_array[seeker+1])
                    seeker++; // throw away duplicates
                
                if(seeker < num_seeks && frag_schedule_array[seeker]==blocks_written) {
                    fragment(turn);
                    turn++;
                    seeker++;
                }
            }
           __Ntime gettimeofday(&aging_end, NULL);
           __Ntime aging_total += diff_time(aging_start, aging_end);
        }
        
        //cleanup
        if(num_seeks > 0 && turn%2==1) 
            fragment(-1);       
        pos_close(fd);
    }
    if(num_seeks!=0) 
        free(frag_schedule_array);
}

