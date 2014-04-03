#include <stdio.h>
#include <stdlib.h>
#include "stat.h"

#define FILENAME_SIZE 100
#define MY_BLOCK_SIZE 4096

//#define PARENT_PATH "/nitin/beagle/impress_home"
extern char PARENT_PATH[1024];

// List of Special Flags
#define sf_flat 0
#define sf_deep 1
#define sf_ext 2
#define sf_wordfreq 3
#define sf_large2small 4 
#define sf_small2large 5
#define sf_depthwithcare 6
#define sf_filedepthpoisson 7
#define sf_dircountfiles 8
#define sf_constraint 9
// change this when you add a flag
#define NUM_FLAGS 10

// List of params for Prinwhat: max is NUM_PRINTS
#define pw_ext 0
#define pw_size 1
#define pw_depth 2
#define pw_sizebin 3
#define pw_initial 4
#define pw_final 5
#define pw_tree 6
#define pw_subdirs 7
#define pw_dircountfiles 8
#define pw_constraint 9
// change this when you add a flag
#define NUM_PRINTS 10

/* max params to specify any given distribution 
   Realistically it will be 2-5 (mu, sigma) or pair of (mu,sigma)
   with alpha */
#define MAX_PARAMS 20

#define DEPTH_ENTRIES 20

// maintain probabilities upto dirs with 0-28 files and last bin >= 29 files
#define FILES_PERDIR 30 
extern int max_dir_depth;

/* Number of file size bins */
#define FILE_SIZE_BINS 50

/* Default specification file */
#define DEFAULT_SPEC_FILE "./inputfile"

struct {
int ParamsOfInterest;
long int FScapacity;
long int FSused;
long int Numfiles;
long int Numdirs;

int num_filesizeparams;
int num_filecountparams;
int num_dircountfilesparams;
int num_randseeds;
double mean_files_per_dir;

int Randseeds[MAX_PARAMS];
double filesizeparams[MAX_PARAMS];
double filecountparams[MAX_PARAMS];
double dircountfilesparams[MAX_PARAMS];
char FilesizeDistr[FILENAME_SIZE];
char FilecountDistr[FILENAME_SIZE];
char Dircountfiles[FILENAME_SIZE];
char DirsizesubdirDistr[FILENAME_SIZE];
char Fileswithdepth[FILENAME_SIZE];
double fileswithdepth_poisson;
int Flag[NUM_FLAGS];
int Printwhat[NUM_PRINTS];
char Parent_Path[1024];
char Actuallogfile[1024];
double Layoutscore;
int Actualfilecreation;
} typedef inputset;

extern int err;
extern inputset * IMP_input;

extern char FILE_fsparam[FILENAME_SIZE];
extern char FILE_input_dist[FILENAME_SIZE];
extern char FILE_contentfilters[FILENAME_SIZE];
extern FILE *fp_fsparam, *fp_input_dist, *fp_contentfilters;

//bw.c
int create_gif(int argc, char *argv[]);

/* Extension.cpp */
int get_extension(char * ext, char * header);
int get_meaningful_header(int ext_number, char * header);
int get_meaningful_footer(int ext_number, char * footer);
char * get_header(char * ext);
long double make_generic_file(char * filepath, long double size, int depth, FILE *fp);
int make_ascii_file(char * filepath, long double size, int extension_num);
int make_binary_file(char * filepath, long double size, int extension_num);
int ext_extnum (char *ext);
long int ScaleByUnit(char * unit);
int get_input_specification(char * input_file);
int printIMP_input(inputset * input);
int initialize_input();
int generate_image();
int fragment_image();
int apply_contentfilters();
int use_distributions();
int init_ext_popularity();
int my_gettimeofday();
int deseeder();

/* depth.cpp*/
int fn_depthsize_prob (long double filesize);

/* extension.cpp*/
int compfunc(const void *x, const void *y);

/* ssp.cpp*/
int subsetsumconstraint(long double * filesizearray, int N);

/* Define debugging macros */
#define PRINT_DEBUG
#ifdef PRINT_DEBUG
#define print_debug(n, f, a...)   \
        do {    \
                if (n) {        \
                        printf("(%s, %d): %s: ",     \
                        __FILE__, __LINE__, __FUNCTION__);      \
                        printf(f, ## a);        \
                }       \
        } while (0)
#else
#define print_debug(f, a...)  /* */
#endif

#define PRINT_DEBUG
#ifdef PRINT_DEBUG
#define print_debug1(n, f, a...)  \
    do {    \
        if (n) {    \
            printf(f, ## a);  \
        }   \
    } while (0)
#else
#define print_debug1(f, a...) /* */
#endif


/* **************** TIMING STUFF ************/
//#define PRINT_TIME

/* Usage ---
__NTRACE_sprintf(1,"C:%s:%s", TSTAMP,cmdbuf);
__NTRACE_PRINT(1, 0, __NTRACE_sprinted);
*/

#ifdef PRINT_TIME
#define __Nprint(n, string...) \
    if(n){printf(string);} 
#else
    #define __Nprint(string...)
#endif

#define NPRINT
#ifdef NPRINT
    #define __Ntime     
#else 
    #define __Ntime // abracadabra //   
#endif

/* **************** TIMING STUFF ENDS ************/

