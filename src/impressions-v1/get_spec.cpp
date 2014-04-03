
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
#include <stdio.h>
#include <stdlib.h>

char FILE_fsparam[FILENAME_SIZE];
char FILE_input_dist[FILENAME_SIZE];
char FILE_contentfilters[FILENAME_SIZE];
FILE *fp_fsparam, *fp_input_dist, *fp_contentfilters;

/* ****************************************************

   Scale the input parameters appropriately

   **************************************************** */
long int ScaleByUnit(char * unit) {

    if(strcmp(unit, "GB")==0)
        return 1024*1024*1024;
    else if (strcmp(unit, "MB")==0)
        return 1024*1024;
    else if (strcmp(unit, "KB")==0)
        return 1024;
    else if(strcmp(unit, "B")==0)
        return 1000*1000*1000;
    else if (strcmp(unit, "M")==0)
        return 1000*1000;
    else if (strcmp(unit, "K")==0)
        return 1000;
    else if (strcmp(unit, "N")==0)
        return 1;
}


/* ****************************************************

   Parse input file system parameters in the sample input file

   **************************************************** */
int input_tokenizer_int(char * line, int * dest_array){

    char * pch;
    int j =0;
    //printf("line: %s \n", line);
    pch = strtok (line," ");
    pch = strtok (NULL, " ");
    pch = strtok (NULL, " ");
    pch = strtok (NULL, " ");
    while (pch != NULL) {
        dest_array[j] = atoi(pch);
        print_debug(0, "%d %d\n", dest_array[j], j);
        pch = strtok (NULL, " ");
        j++;
    }
    return 1;
}

int input_tokenizer(char * line, double * dest_array){

    char * pch;
    int j =0;
    //printf("line: %s \n", line);
    pch = strtok (line," ");
    pch = strtok (NULL, " ");
    pch = strtok (NULL, " ");
    pch = strtok (NULL, " ");
    while (pch != NULL) {
        dest_array[j] = atof(pch);
        //printf ("%f %d\n", dest_array[j], j);
        pch = strtok (NULL, " ");
        j++;
    }
    return 1;
}

/* ****************************************************

   Scan the input file line by line getting specifications
    The input has be in the order expected here

   **************************************************** */
int get_input_specification(char * input_file)
{
    extern int ACTUAL_LOG_CREATION;
    static FILE * fp_input = NULL;
    extern char PARENT_PATH[1024];
    char line[1024], input[64], param[64], value[64], unit[64];
    int num_flags=0, num_prints=0;
    char char_params[MAX_PARAMS][10];
    char * pch;
    int j=0;

    fp_input = fopen(input_file, "r");
    if (!fp_input) {
        fprintf(stderr, "Error: unable to open the input file %s\n", input_file);
        return -1;
    }
    /*
    if (!feof(fp_input)) {
        fscanf(fp_input, "ParamsOfInterest: %s\n", input);
        IMP_input->ParamsOfInterest = atoi(input);
    }
    */
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Parent_Path:") == 0) {
        strcpy(IMP_input->Parent_Path, value);
        if(atoi(unit) == 1)
            strcpy(PARENT_PATH, IMP_input->Parent_Path);
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Actuallogfile:") == 0) {
        strcpy(IMP_input->Actuallogfile, value);
        if(atoi(unit) == 1) {
            ACTUAL_LOG_CREATION = 1;
        }
    }
    fgets(line, 1024, fp_input);
    sscanf(line, "%s %s %s", param, value, unit);
    if (strcmp(param, "Randseeds:") == 0) {
            if(strcmp(value, "Direct") == 0) {
                IMP_input->num_randseeds = atoi(unit);
                input_tokenizer_int(line, IMP_input->Randseeds);
            }
            else {
                printf("Error getting Randseeds\n");
                IMP_input->num_randseeds = 0; //default to gettimeofday
                //return -1;
            }
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "FScapacity:") == 0) {
        IMP_input->FScapacity = atol(value);
        IMP_input->FScapacity *= ScaleByUnit(unit);
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "FSused:") == 0) {
        if(strcmp(value, "NO") == 0)
            IMP_input->FSused = -1;
        else {
            IMP_input->FSused = atol(value);
            IMP_input->FSused *= ScaleByUnit(unit);
        }
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Numfiles:") == 0) {
        if(strcmp(value, "NO") == 0)
            IMP_input->Numfiles = -1;
        else {
            IMP_input->Numfiles = atol(value);
            IMP_input->Numfiles *= ScaleByUnit(unit);
        }
    } 
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Numdirs:") == 0) {
        if(strcmp(value, "NO") == 0)
            IMP_input->Numdirs = -1;
        else {
            IMP_input->Numdirs = atol(value);
            IMP_input->Numdirs *= ScaleByUnit(unit);
        }
    } 
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Filesperdir:") == 0) {
        if(strcmp(value, "NO") == 0)
            IMP_input->mean_files_per_dir = -1;
        else {
            IMP_input->mean_files_per_dir = atof(value);
            IMP_input->mean_files_per_dir *= ScaleByUnit(unit);
        }
    } 
    fgets(line, 256, fp_input);
    sscanf(line, "%s %s %s", param, value, unit);
    if (strcmp(param, "FilesizeDistr:") == 0) {
        if(strcmp(value, "NO") == 0)
            strcpy(IMP_input->FilesizeDistr,"");
        else {
            if(strcmp(value, "Indir") == 0) {
                // Filename containing Distr (either X,Y or some 
                // encoding of the distribution
                strcpy(IMP_input->FilesizeDistr, unit);
            }
            else if(strcmp(value, "Direct") == 0) {
                IMP_input->num_filesizeparams = atoi(unit);
                input_tokenizer(line, IMP_input->filesizeparams);
            }
            else {
                printf("Error getting FilesizeDistr\n");
                return -1;
            }
        }
    }
    fgets(line, 256, fp_input);
    sscanf(line, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "FilecountDistr:") == 0) {
        if(strcmp(value, "NO") == 0)
            strcpy(IMP_input->FilecountDistr,"");
        else {
            if(strcmp(value, "Indir") == 0) {
                strcpy(IMP_input->FilecountDistr, unit);
            }
            else if(strcmp(value, "Direct") == 0) {
                IMP_input->num_filecountparams = atoi(unit);
                input_tokenizer(line, IMP_input->filecountparams);
            }
            else {
                printf("Error getting FilecountDistr\n");
                return -1;
            }
        }
    }
    fgets(line, 256, fp_input);
    sscanf(line, "%s %s %s", param, value, unit);
    if (strcmp(param, "Dircountfiles:") == 0) {
        if(strcmp(value, "NO") == 0)
            strcpy(IMP_input->Dircountfiles ,"");
        else {
            if(strcmp(value, "Indir") == 0) {
                strcpy(IMP_input->Dircountfiles, unit);
            }
            else if(strcmp(value, "Direct") == 0) {
                IMP_input->num_dircountfilesparams = atoi(unit);
                input_tokenizer(line, IMP_input->dircountfilesparams);
            }
            else {
                printf("Error getting Dircountfiles\n");
                return -1;
            }
        }
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "DirsizesubdirDistr:") == 0) {
        if(strcmp(value, "NO") == 0)
            strcpy(IMP_input->DirsizesubdirDistr,"");
        else {
            if(strcmp(value, "Indir") == 0) {
                strcpy(IMP_input->DirsizesubdirDistr, unit);
            }
            else {
                printf("Error getting DirsizesubdirDistr\n");
                return -1;
            }
        }
    }
    fscanf(fp_input, "%s %s %s\n", param, value, unit);
    if (strcmp(param, "Fileswithdepth:") == 0) {
        if(strcmp(value, "NO") == 0)
            strcpy(IMP_input->Fileswithdepth, "");
        else {
            if(strcmp(value, "Indir") == 0) {
                strcpy(IMP_input->Fileswithdepth, unit);
            }
            else if(strcmp(value, "Direct") == 0) {
                IMP_input->fileswithdepth_poisson = atof(unit);
            }
            else {
                printf("Error getting Fileswithdepth\n");
                return -1;
            }
        }
    }
    fscanf(fp_input, "%s %s\n", param, value);
    if (strcmp(param, "Layoutscore:") == 0) {
        IMP_input->Layoutscore = atof(value);
    }
    fscanf(fp_input, "%s %s\n", param, value);
    if (strcmp(param, "Actualfilecreation:") == 0) {
        IMP_input->Actualfilecreation = atoi(value);
    }
    fscanf(fp_input, "%s %s\n", param, value);
    if (strcmp(param, "SpecialFlags:") == 0) {
        num_flags=atoi(value);
        for(int i =0; i< num_flags; i++) {
            fscanf(fp_input, "%s %s\n", value, unit);
            
            if(strcmp(value, "Flat") == 0) {
                IMP_input->Flag[sf_flat] = atoi(unit);
            }
            else if(strcmp(value, "Deep") == 0) {
                if(IMP_input->Flag[sf_flat]==1) {
                    printf("Cannot have deep and flat tree at the same time ..\n \
                            going with Flat ..\n");
                }
                else IMP_input->Flag[sf_deep]=atoi(unit);
            }
            else if(strcmp(value, "Ext") == 0) {
                IMP_input->Flag[sf_ext]= ext_extnum(unit);
            }
            else if(strcmp(value, "Wordfreq") == 0) {
                IMP_input->Flag[sf_wordfreq]=atoi(unit) ;
            }
            else if(strcmp(value, "Large2Small") == 0) {
                IMP_input->Flag[sf_large2small]=atoi(unit);
            }
            else if(strcmp(value, "Small2Large") == 0) {
                IMP_input->Flag[sf_small2large]=atoi(unit);
            }
            else if(strcmp(value, "Depthwithcare") == 0) {
                IMP_input->Flag[sf_depthwithcare]=atoi(unit);
            }
            else if(strcmp(value, "Filedepthpoisson") == 0) {
                IMP_input->Flag[sf_filedepthpoisson]=atoi(unit);
            }
            else if(strcmp(value, "Dircountfiles") == 0) {
                IMP_input->Flag[sf_dircountfiles]=atoi(unit);
            }
            else if(strcmp(value, "Constraint") == 0) {
                IMP_input->Flag[sf_constraint]=atoi(unit);
            }
            else {
                printf("Error getting flags\n");
                return -1; 
            }
        }
    }
    fscanf(fp_input, "%s %s\n", param, value);
    if (strcmp(param, "Printwhat:") == 0) {
        num_prints=atoi(value);
        for(int i =0; i< num_prints; i++) {
            fscanf(fp_input, "%s %s\n", value, unit);
            
            if(strcmp(value, "ext") == 0) {
                IMP_input->Printwhat[pw_ext] = atoi(unit);
            }
            else if(strcmp(value, "size") == 0) {
                IMP_input->Printwhat[pw_size] = atoi(unit);
            }
            else if(strcmp(value, "sizebin") == 0) {
                IMP_input->Printwhat[pw_sizebin] = atoi(unit);
            }
            else if(strcmp(value, "initial") == 0) {
                IMP_input->Printwhat[pw_initial] = atoi(unit);
            }
            else if(strcmp(value, "final") == 0) {
                IMP_input->Printwhat[pw_final] = atoi(unit);
            }
            else if(strcmp(value, "depth") == 0) {
                IMP_input->Printwhat[pw_depth] = atoi(unit);
            }
            else if(strcmp(value, "tree") == 0) {
                IMP_input->Printwhat[pw_tree] = atoi(unit);
            }
            else if(strcmp(value, "subdirs") == 0) {
                IMP_input->Printwhat[pw_subdirs] = atoi(unit);
            }
            else if(strcmp(value, "dircountfiles") == 0) {
                IMP_input->Printwhat[pw_dircountfiles] = atoi(unit);
            }
            else if(strcmp(value, "constraint") == 0) {
                IMP_input->Printwhat[pw_constraint]=atoi(unit);
            }
            else {
                printf("Error getting printwhats\n");
                return -1; 
            }

        }
    }
    fclose(fp_input);
    return 1;
}

/* ****************************************************

   Print the input specifications

   **************************************************** */
int printIMP_input(inputset * input) {
    extern int ACTUAL_LOG_CREATION;
    printf("Input Parameters\n");
    printf(" %d\n", input->ParamsOfInterest);
    printf(" Parent Path: %s\n", PARENT_PATH);
    printf(" Actual Log file : %s %d\n", IMP_input->Actuallogfile, ACTUAL_LOG_CREATION);
    printf(" %f\n", input->Layoutscore);
    printf(" %ld\n", input->FScapacity);
    printf(" %ld\n", input->FSused);
    printf(" %ld\n", input->Numfiles);
    printf(" %ld\n", input->Numdirs);
    printf(" %s\n", input->FilesizeDistr);
    printf(" %s\n", input->FilecountDistr);
    printf(" %s\n", input->Dircountfiles);
    printf(" %s\n", input->DirsizesubdirDistr);
    printf(" Fileswithdepth: %s %f\n", input->Fileswithdepth, input->fileswithdepth_poisson);
    printf(" File Size params: ");
    for(int j=0; j < input->num_filesizeparams; j++) {
        printf(" %f", input->filesizeparams[j]);
    }
    printf("\n");
    printf(" File Count params: ");
    for(int j=0; j < input->num_filecountparams; j++) {
        printf(" %f", input->filecountparams[j]);
    }
    printf("\n");
    printf(" Randseeds: ");
    for(int j=0; j < input->num_randseeds; j++) {
        printf(" %d", input->Randseeds[j]);
    }
    printf(" Dircountfilesparams: ");
    for(int j=0; j < input->num_dircountfilesparams; j++) {
        printf(" %f", input->dircountfilesparams[j]);
    }
    printf("\n");
    printf("\n");
    printf(" Flags:\n");
    for(int i =0 ; i< NUM_FLAGS; i++) {
        printf(" %d\n", input->Flag[i]);
    }
}
