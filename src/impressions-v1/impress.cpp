
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
#include "montecarlo.h"
#include "math.h"
#include "classes.h"
#include "word.h"
#include "fragment.h"

#define FINAL_DEBUG

# define FILE_SIZE 0
# define PARENT_DIR 1

// Num of above definitions
# define NUM_FILE_ATTRIBS 2

# define DIR_SIZE_FILES 0
# define DIR_SIZE_DIRS 1
# define DIR_DEPTH 2

// Num of above definitions
# define NUM_DIR_ATTRIBS 3

/* Timing variables for different components */

struct timeval main_time_start, main_time_end, \
               dirtree_start, dirtree_end, \
               filecontent_start, filecontent_end, \
               filesize_start, filesize_end, \
               depthcare_start, depthcare_end, \
               poisson_start, poisson_end, \
               dircountfiles_start, dircountfiles_end, \
               word_model_start, word_model_end, \
               extension_start, extension_end, \
               aging_start, aging_end, \
               file_creation_start, file_creation_end;

double main_time_total, dirtree_total, filecontent_total, \
               word_model_total, extension_total, aging_total, \
               file_creation_total, depthcare_total, poisson_total, \
               filesize_total, dircountfiles_total;
             
Random rv_extension, rv_dfc, rv_dfc2;

int sec_main_time_total;

// For the hybrid tail selection bias 
double poisson_mu;
double poisson_sigma;

double alpha1;
double pareto_base1; 
double pareto_shape1;
double bias = 0; 

long double * filesizearray;

double dircountfiles_prob[FILES_PERDIR];
long double *filearray;
long double binsize[FILE_SIZE_BINS];
int bincounter[FILE_SIZE_BINS];
long double totalfilesize=0; // this is the sum of the original sample
long double stdev=0, meanfilesize=0;
char parent_path[1024], strerr[100];
inputset * IMP_input;
char PARENT_PATH[1024] = "/nitin/beagle/impress_home";
int ACTUAL_FILE_CREATION = 1;
int ACTUAL_LOG_CREATION = 0;
double poly_degree=0, poly_offset = 0;
int total_dfc=0;
 

// one of the following three can be true
int ATTR_FILE_SIZE = 0;
int ATTR_NUM_DIRS  = 0;
int ATTR_NUM_FILES = 0;

// usually true if ATTR_NUM_DIRS or ATTR_NUM_FILES is 1
int FILE_TRUNCATOR = 0; // or (ATTR_NUM_DIRS || ATTR_NUM_FILES);

extern dir * Dirs;
extern list<dir> LD;
extern list<dir>::iterator li;
extern list<dir>::iterator ni;
extern multimap<int, dir> DirDepthmultimap;
extern map<int, dir> DirIDmap;
extern multimap<int, int> Dircountfilesmmap[DEPTH_ENTRIES];

pair<multimap<int, dir>::iterator, multimap<int, dir>::iterator> dirppp, dirppp2;
multimap<int, dir>::iterator it3, it4;
pair<multimap<int, int>::iterator, multimap<int, int>::iterator> idcppp, idcppp2;
multimap<int, int>::iterator idcit1, idcit2;
map<int, dir>::iterator cur;//  = DirIDmap.find((int)data2);


/* ****************************************************

    Use the seed values supplied by the user.
    When supplied seeds are all used up, 
    gettimeofday is used instead
    
   **************************************************** */
int deseeder() {
   
    print_debug(0,"Deseeding %d %d\n", IMP_input->num_randseeds, IMP_input->Randseeds[IMP_input->num_randseeds-1]);
    int seed;
    if(IMP_input->num_randseeds>0) {
        seed = IMP_input->Randseeds[IMP_input->num_randseeds-1]; 
        IMP_input->num_randseeds--;// eat up a seed
    }
    else {
        seed = my_gettimeofday();
    } 

    return seed;
}

/* ****************************************************

    Given a FS capacity and file size distribution, 
    find corresponding number of files and directories 
    
   **************************************************** */
int init_files_dirs_for_capacity() {

    double global_mean = (exp(poisson_mu + poisson_sigma*poisson_sigma/2) * alpha1/100000)+(pareto_base1*(1-alpha1/100000));   
    
    if(IMP_input->FSused > 0) {
        IMP_input->Numfiles = lrint(IMP_input->FSused/global_mean);
        IMP_input->Numdirs  = lrint(IMP_input->Numfiles/IMP_input->mean_files_per_dir);
    }
    return 1;
}

/* ****************************************************

   Difference between two timeval structs

   **************************************************** */
double diff_time(struct timeval st, struct timeval et)
{
    double diff;
    if (et.tv_usec < st.tv_usec) {
        et.tv_usec += 1000000;
        et.tv_sec --;
    }
    diff = (et.tv_sec - st.tv_sec)*1000000 + (et.tv_usec - st.tv_usec);
    return diff; 
}

/* ****************************************************

   Difference between two timeval struct: low resolution version

   **************************************************** */
int diff_time_sec(struct timeval st, struct timeval et)
{
    int diff;
    if (et.tv_usec < st.tv_usec) {
        et.tv_usec += 1000000;
        et.tv_sec --;
    }
    diff = (int) (et.tv_sec - st.tv_sec);
    return diff; 
}

/* ****************************************************

   Difference between two timeval struct: low resolution version

   **************************************************** */
double diff_time_sec2(struct timeval st, struct timeval et)
{
    double diff;
    if (et.tv_usec < st.tv_usec) {
        et.tv_usec += 1000000;
        et.tv_sec --;
    }
    diff = (et.tv_sec - st.tv_sec) + (et.tv_usec - st.tv_usec)/1000000;
    return diff; 
}

/* ****************************************************

   Initialize data structures

   **************************************************** */
void init () {
   
    int i =0;
    double temp_sum=0;
    
    /* Initialize numfiles and numdirs given capacity if needed */
    init_files_dirs_for_capacity();

    /* word length popularity is initilized if BNC is chosen;
        certain attribs are common such as "precision" */
    if(IMP_input->Flag[sf_wordfreq]>0)
        set_word_popularity();

    // Activate BNC corpus: "the" is most popular and so on.
    if(IMP_input->Flag[sf_wordfreq]==2)
        if(init_word_bnc_frequency_list() == -1) {
            print_debug1(1, "No BNC corpus, resorting to word length popularity model ...\n");
            IMP_input->Flag[sf_wordfreq]=1;
        }
   
    // initialize popular file extensions
    init_ext_popularity();
    
    print_debug(0, "fragstate : %f\n", IMP_input->Layoutscore);
    if(IMP_input->Layoutscore < 1.0) {
        
        //initialize fragmentation files
        char fragfile1[100];
        sprintf(fragfile1, "%s/fragfile1", PARENT_PATH);
        make_frag_file(fragfile1, 1024*1024*1);
        print_debug1(1, "fragstate created ..\n");
    }
    
    /* do not pick a dir at random, but match the existing file counts
       pick a dir at depth = depth -1 and file count == XX
       =(degree-1)*POWER(offset,degree-1)*POWER((A2+offset),-degree); for dir with files > 0
       =22.5 % directories have no files
       degree =2; offset = 2.36 obtained by curve fit on 2004 data */
    if(IMP_input->num_dircountfilesparams>0) {
        
        poly_degree  = IMP_input->dircountfilesparams[0];
        poly_offset  = IMP_input->dircountfilesparams[1];
        
        for (i = 1; i< FILES_PERDIR-1; i++) {
            //for dir with files > 0
            dircountfiles_prob[i] = (poly_degree-1)*pow(poly_offset,poly_degree-1)*pow((i+poly_offset),-poly_degree); 
            temp_sum+=dircountfiles_prob[i];
        }
        
        dircountfiles_prob[0]= 0.225;
        // dircountfiles_prob[0]= 0.0; // for testing only
        temp_sum+=dircountfiles_prob[0];
        total_dfc = (int)(10000*temp_sum);
        
        // last bin is cumulative prob of all files >= FILES_PERDIR-1
        dircountfiles_prob[FILES_PERDIR-1]= 1-temp_sum; 
        // dircountfiles_prob[FILES_PERDIR-1]= 0;// for testing only
    }


    for(i =0; i< FILE_SIZE_BINS; i++){
        bincounter[i]=0;
        binsize[i]=0;
    }

}
int montecarlo_dirfilescount() {

    // First bin is the one having no files, hence i is initialized to 1, not 0
    int total_pop= total_dfc- (int)(dircountfiles_prob[0]*10000);
    int i=1; 
    
    int token = rv_dfc.uniformDiscrete(0, total_pop-1);

    float token_until_now=dircountfiles_prob[i]*10000;
    while (token_until_now < token) {
        i++;
        token_until_now+=dircountfiles_prob[i]*10000;
    }
    
    /* 
    if (i>=10)
        i=1;
    */

    /* Bins for Directories with particular file count 
       partitioned into FILES_PERDIR bins. Last bin
       contains probability for dirs with file count
       greater than equal to FILES_PERDIR-1 */
    if(i > FILES_PERDIR-1) {
        i = 1; //most dirs have only 1 file
    }

    return i;
}

/* ****************************************************

   Clear data structures; print timing statistics

   **************************************************** */
void exit () {
    
    int ret;
    char strerr[100];
    long double data1=0, mu=0, sigma=0;
    
    if(IMP_input->Layoutscore < 1.0) {
        //clear fragment files;
        char fragfile1[100];
        sprintf(fragfile1, "%s/fragfile1", PARENT_PATH);
        if((ret = pos_unlink(fragfile1))<0) {
            print_debug1(1, "Error deleting fragmentfile1 %d %s\n", ret, strerror_r(errno, strerr, 100));
        }
    }
    
    /* Print timing statistics here if needed 
       convert micro to milli seconds  */
    
    #ifdef NPRINT
    dirtree_total         = diff_time(dirtree_start, dirtree_end);  
    main_time_total       = diff_time_sec2(main_time_start, main_time_end);    
    sec_main_time_total   = diff_time_sec(main_time_start, main_time_end);    
    filecontent_total   = diff_time(filecontent_start, filecontent_end)/1000;
    word_model_total    = diff_time(word_model_start, word_model_end)/1000;
    extension_total     = diff_time(extension_start, extension_end)/1000;
    aging_total         = diff_time(aging_start, aging_end)/1000;
    file_creation_total = diff_time(file_creation_start, file_creation_end)/1000;

    if(IMP_input->Printwhat[pw_final]==1){
        print_debug1(1, "Time(msec)\ndirtree %f\nfilecontent %f\nextension\
            %f\naging %f\ndepthcare %f\npoisson %f\nfilesize\
            %f\nfile_creation %f\nmain_time(s) %f\nnew_main_time(s) %d\n",\
            dirtree_total/1000,filecontent_total/1000,extension_total/1000,aging_total/1000,
            depthcare_total/1000, poisson_total/1000, filesize_total/1000, 
            file_creation_total/1000, main_time_total, sec_main_time_total);
        
        for (int i = 0; i< IMP_input->Numfiles; i++){
            data1 = *(filearray+ NUM_FILE_ATTRIBS*i + FILE_SIZE);
            stdev += (data1-meanfilesize)*(data1-meanfilesize);
        }
        stdev = sqrt(stdev/IMP_input->Numfiles); 
        mu = logl(meanfilesize) - 0.5* logl(1+ (stdev*stdev)/(meanfilesize*meanfilesize));
        sigma = sqrt(logl(1+ (stdev*stdev)/(meanfilesize*meanfilesize)));
        print_debug1(1, "Filesize_mean: %Lf sddev: %Lf\nmu: %Lf sigma: %Lf \n\
totalbytes: %Lf totalfiles: %d totaldirs: %d\n", meanfilesize, stdev, mu, sigma,\
        totalfilesize, IMP_input->Numfiles,  IMP_input->Numdirs);
        print_debug1(1, "totalbytes (GB): %Lf\n", totalfilesize/(1024*1024*1024));
        
    }
    #endif
    
    if(IMP_input->Printwhat[pw_sizebin]==1){
        for(int i =0; i< FILE_SIZE_BINS; i++)
            printf ("Bin: %d \t%d \t%Lf \t%.10Lf \t%.10Lf\n", i, bincounter[i], binsize[i],\
            (long double)bincounter[i]/IMP_input->Numfiles, binsize[i]/totalfilesize);
        
    }
    
    if(IMP_input->Printwhat[pw_subdirs]==1){
        // Print subdir count/depth and file count with directories
        for(li=LD.begin(); li!=LD.end();li++) {
            print_debug1(1, "Subdirs: %d Depth: %d Files: %d\n",(*li).subdirs,(*li).depth,(*li).files);
        }
    }
    
    if(IMP_input->Printwhat[pw_dircountfiles]==1){
        // Print subdir count/depth and file count with directories
        for(cur  = DirIDmap.begin(); cur!=DirIDmap.end(); ++cur)  {
            print_debug1(1, "Files: %d\n",((*cur).second).files);

        }
    }

    if(IMP_input->Flag[sf_constraint]==1){
        if(filesizearray)
            free(filesizearray);
    }
}

/* ****************************************************

   Maintain statistics on file sizes sampled

   **************************************************** */
int experimental_center (long double data1, long double data3) {
    
    if(data1!=0) {
        bincounter[(int)floor(log2l(data1))+1]++;
        binsize[(int)floor(log2l(data1))+1]+=data1;
        totalfilesize+=data1;
    }
    else
        bincounter[0]++;
    
    meanfilesize = totalfilesize/IMP_input->Numfiles;
}


/* ****************************************************

   Impressions main()

   **************************************************** */
int main(int argc, char * argv[]) {
    
    FILE * fp_log;
    int header_size;
    double logn;
    int seed=1;
    int input_scan_err = -1; 
    
    /* user specified specification file */
    if (argc == 2) {
        if( strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "-help") == 0 || strcmp(argv[1], "help") == 0) {
            print_debug1(1, "Impressions usage: \n impressions <specification file> \n");
            print_debug1(1, "if specfication file unspecified, use default file at %s \n", DEFAULT_SPEC_FILE);
            exit(0);
        }
        else {
            /* Hold all input parameters */
            IMP_input = (inputset *) malloc(sizeof(inputset));

            input_scan_err = get_input_specification(argv[1]);
            print_debug1(1, "Reading spec from %s\n", argv[1]);
        }
    }
    else {
        /* Hold all input parameters */
        IMP_input = (inputset *) malloc(sizeof(inputset));

        /* default specification file */
        input_scan_err = get_input_specification(DEFAULT_SPEC_FILE);
    }
    
    if (input_scan_err == -1 ){ 
        // Inputfile read fails or not enough essential parameters specified
        print_debug(1,"input specification file read failed, please supply valid \
            spec file. Exiting ...\n");
        free(IMP_input);
        exit(-1);
    }
    else { // successfully read spec file 
        if(IMP_input->Printwhat[pw_initial]==1){
            print_debug1(1, "Inputfile scan:\n");
            printIMP_input(IMP_input);
        }
    }
    //double alpha2= 0.00223;
    //double pareto_base2 = pow((double)2,(double)31);
    //double pareto_shape2 = 0.6;
   
    if(IMP_input->num_filecountparams>0) {
        poisson_mu = IMP_input->filecountparams[0];
        poisson_sigma = IMP_input->filecountparams[1];
    }
    
    if(IMP_input->num_filesizeparams>0) {
        alpha1        = IMP_input->filesizeparams[0];
        pareto_base1  = pow((double)2,(double)IMP_input->filesizeparams[1]);
        pareto_shape1 = IMP_input->filesizeparams[2];    
    }
    
    /* Initialize random number generators with user specified seeds */
    Random rv(deseeder()); 
    Random rv_filedepth(deseeder());
    Random rv_parentdir(deseeder());
    rv_extension = Random(deseeder()); 
    rv_dfc = Random(deseeder()); 
    rv_dfc2 = Random(deseeder()); 
    Random rv_bias(deseeder());
    srand(deseeder());

    long double data1 = 0, data2 = 0, data3=0, bimodal_sum=0;
    long double olddata1 = 0;
    int j=0, fd=0;
    struct timeval st, et;
    int FULL =0;
    int iteration=0;
    int success = 0;
    int depth =0;
    int idccount=0, idcbincount=0, idccurbin=0, curbindirs=0;
    
    /* ********** INITIALIZE DATA STRUCTURES **************
       This also initializes file/dir counts for capacity 
       based on distributions */
    init();
    /* ****************************************************/

    if(ACTUAL_LOG_CREATION) {
        char logfilename[100];
        sprintf(logfilename, "%s/log-%d", IMP_input->Actuallogfile, IMP_input->Numfiles);
        if( !(fp_log = fopen(logfilename, "w"))) {
            print_debug1(1, "Cannot create Log file, proceeding without logging\n");
            //exit(-1);
        }
    }

    filearray=(long double*)malloc(sizeof(long double)*NUM_FILE_ATTRIBS*IMP_input->Numfiles);
    Dirs = (dir *) malloc(sizeof(dir)*IMP_input->Numdirs);
    if(filearray==NULL || Dirs == NULL)  {
        print_debug(1, "ERROR: Failed to allocated memory for File/Dir data structures. Exit\n");
        exit(-1);
    }
    // start main time loop
    __Ntime gettimeofday(&main_time_start, NULL);
    
    
    /* Create directory tree: 
       these functions check for FLAG:Actualfilecreation*/

    __Ntime gettimeofday(&dirtree_start, NULL);
    if (IMP_input->Flag[sf_flat] ==1 )
        flat_tree(IMP_input->Numdirs);
    else if (IMP_input->Flag[sf_deep] == 1)
        deep_tree(IMP_input->Numdirs);
    else montecarlo(IMP_input->Numdirs);
    __Ntime gettimeofday(&dirtree_end, NULL);

    /* These two should be used for lookup. Not the List.
        DirDepthmultimap; DirIDmap;
    
        Check their contents:
        Here do the one time depth breakdown: store in Dircountfilesmmap
    */
    
    __Ntime gettimeofday(&dircountfiles_start, NULL);
    
    for (int idc=0; idc <= max_dir_depth; idc++) {
        dirppp2 = DirDepthmultimap.equal_range(idc); //all dirs at depth idc
        it3 = dirppp2.first;
        idccount = (int)DirDepthmultimap.count(idc); // number of dirs at depth idc
        idcbincount =0;
        
        for (int idc2=0; idc2<FILES_PERDIR-1; idc2++){ 
        
            /* Run this initilization for all except the last bin
               breakdown the dirs at this depth
               idccurbin is the num of dirs in bin idc2; 
               put these dirs in their multimap
            */
            
            idccurbin = lrint(dircountfiles_prob[idc2]*idccount); //round to nearest int

            //grab all idccurbin curbindirs and put them in mmap for depth
            if(idccurbin>0){
                for(int idc3=0; idc3<idccurbin; idc3++) {
                    Dircountfilesmmap[idc].insert(pair<int, int>(idc2,((*it3).second).id));
                    ++it3;
                }
                idcbincount+=idccurbin;
            }

        }
        // remaining directories go in last bin: the tail of dir by file count
        if(idcbincount < idccount) {
            for(int idc3=0; idc3<(idccount-idcbincount); idc3++) {

             Dircountfilesmmap[idc].insert(pair<int, int>(FILES_PERDIR-1,((*it3).second).id));
             /* Testing only 
             Dircountfilesmmap[idc].insert(pair<int, int>(0,((*it3).second).id)); 
             */
             ++it3;
            }
        }
    }
    __Ntime gettimeofday(&dircountfiles_end, NULL);
    __Ntime dircountfiles_total += diff_time(dircountfiles_start, dircountfiles_end);

    /**************** TRIAL for array of mmaps*************/
    //#define MULTIMAP
    #ifdef MULTIMAP 
    cout << "Elements in 30 mmaps: maxdirdpeth " << max_dir_depth << endl;

    for (int idc=0; idc <= max_dir_depth; idc++) {
        cout << "\n Depth  " << idc <<  endl;
        for (idcit1 = Dircountfilesmmap[idc].begin();
            idcit1 != Dircountfilesmmap[idc].end(); ++idcit1) {
            cout << "files: "<< (*idcit1).first << " dirid: " << (*idcit1).second  << endl;
        }
        //getchar();
    }
    #endif
    /**************** TRIAL ENDS for array of mmaps*************/

    /************************************TRIAL *****************/
    //#define MULTI_MAP2
    #ifdef MULTI_MAP2 
   
    cout << "Elements in maps: " << endl;
    for (multimap<int, dir>::iterator it = DirDepthmultimap.begin();
       it != DirDepthmultimap.end(); ++it)
    {
       cout << (*it).first << " " << ((*it).second).id << " " << ((*it).second).depth <<  endl;
        //getchar();
    }

    pair<multimap<int, dir>::iterator, multimap<int, dir>::iterator> ppp;

    /* equal_range(b) returns pair<iterator,iterator> representing the range
       of element with depth 3 */
    ppp = DirDepthmultimap.equal_range(3);

    // Loop through range of maps of key "3"
    cout << endl << "Range of 3 depth elements:" << endl;
    for (multimap<int, dir>::iterator it2 = ppp.first;
        it2 != ppp.second;
        ++it2)
    {
        cout << (*it2).first <<endl; //<< " " <<(*it2).second << endl;
    }
    #endif
    /************************************TRIAL *****************/
    
    // extension selection can change the sampled value 
    long double total_file_size=0; 
    
    double total_time=0.0;
    long shrink =0;
    
    
    if(IMP_input->Flag[sf_large2small]==1) {
        /* set values for large file systems; use this 
        feature for testing with large size distribution:
        not a good idea if you have a small disk */
        poisson_mu = 12.37;
        poisson_sigma = 3.35;
    }
    
    /* Constraint on file sizes to match the FSused*/
    if(IMP_input->Flag[sf_constraint] == 1) {
       filesizearray = (long double *) malloc(sizeof(long double) * IMP_input->Numfiles);
       if(!filesizearray) {
            print_debug(1, "ERROR: Filesize array not allocated for contraint solving,\
                            proceeding without constraints\n");
            IMP_input->Flag[sf_constraint] = 0;
       }
       else {
            for (int i=0; i<IMP_input->Numfiles; i++) {
                
                if( (bias = (double)(rv.uniformDiscrete(0, 100000-1))) <= alpha1)
                    filesizearray[i] = (long double) floor(rv.lognormal(0, poisson_mu, poisson_sigma));
                else if (bias > alpha1) //&& bias <= alpha2*100000)
                    filesizearray[i] = (long double) floor(rv.pareto(pareto_shape1)*pareto_base1);

            }
            //subsetsumconstraint(filesizearray, IMP_input->Numfiles);
       }

    }

    for (int i=0; i<IMP_input->Numfiles; i++) {
        
        __Ntime gettimeofday(&st, NULL);

        /* For file sizes: we use a hybrid model with a pareto tail.
           with shape = 0.4 (slope of LLCD = -1.4) and A = pow(2,22) = 4MB
           Two ways: 
        1. Sample from Lognormal X% and Pareto 100-X% times, but then lognormal
           would also contribute to the tail making it biased
        2. Sample from logn. if filesize>= tail split, switch to pareto and get the file size
           This would make the count of files >= tail split exactly as logn would have it,
           but select the bytes from pareto instead. */
        
        __Ntime gettimeofday(&filesize_start, NULL);
        
        if(IMP_input->Flag[sf_constraint] == 1) {
            data1 = filesizearray[i];
        }
        else {
            if( (bias = (double)(rv.uniformDiscrete(0, 100000-1))) <= alpha1)
                data1 = (long double) floor(rv.lognormal(0, poisson_mu, poisson_sigma));
            else if (bias > alpha1) //&& bias <= alpha2*100000)
                data1 = (long double) floor(rv.pareto(pareto_shape1)*pareto_base1);
        }

        __Ntime gettimeofday(&filesize_end, NULL);
        __Ntime filesize_total += diff_time(filesize_start, filesize_end);
        
        print_debug(0, "%f: \n", data1/1024/1024/1024);
       
        // Just some statistics bookkeeping
        experimental_center(data1, data3);
       
       /* ******************************************************
        * Parent Directory for a File implications: 
        * 1. File Depth
        * 2. Count of files/Bytes per Directory
        * 3. Bytes with Depth: Larger files are higher up in the dirtree
        * 4. Special Biases: files/bytes at say Dir Depth 2; 
             or more files in Dir called "Windows"
        * ****************************************************/

        int bin_atdepth=0, count_atbin=0, dirchosen=0;
        
        /* supply filesize as input to depth selection 
           if FLAG:sf_depthwithcare is set
        */
        if(IMP_input->Flag[sf_depthwithcare]==1) {
            
            if(IMP_input->Flag[sf_filedepthpoisson]==1) { 
                // no special weight to special directories
                __Ntime gettimeofday(&poisson_start, NULL);
                
                do {
                    depth = rv_filedepth.poisson(IMP_input->fileswithdepth_poisson);
                    print_debug(0, "FileDepth_poisson: %d %d\n", depth, max_dir_depth);
                } 
                while(depth < 1 || depth > (max_dir_depth+1)); // do not accept < 1
                __Ntime gettimeofday(&poisson_end, NULL);
                __Ntime poisson_total += diff_time(poisson_start, poisson_end);
            }
            else { 
                  // for testing print both poisson and specialdir depth 
                __Ntime gettimeofday(&depthcare_start, NULL);
                depth = fn_depthsize_prob(data1); 
                __Ntime gettimeofday(&depthcare_end, NULL);
                __Ntime depthcare_total += diff_time(depthcare_start, depthcare_end);
            }
            print_debug(0, "Depth: %d, max_dir_depth %d\n", depth, max_dir_depth);
            
            if(IMP_input->Flag[sf_dircountfiles]==1) { // Filecount in directories
                
                #ifdef CNN
                /* use the dircountfiles_prob[FILES_PERDIR] array to get 
                   probability of number of files in a dir 
                   dircountfiles_prob[0] = prob of 0 files; 
                   dircountfiles_prob[FILES_PERDIR-1] = prob of FILES_PERDIR-1 to max files
                */
                
                // given file, pick a bin of dirs
                for (int idc=0; idc < max_dir_depth; idc++) 
                    cout << "Depth  " <<  depth-1 <<  endl;
                
                for (idcit1 = Dircountfilesmmap[depth-1].begin();
                  idcit1 != Dircountfilesmmap[depth-1].end(); ++idcit1) {
                  cout << "files: "<< (*idcit1).first << " dirid: " << (*idcit1).second <<  endl;
                }
                getchar();
                #endif
                
                if(depth==1) {
                    print_debug(0, "Depth is 1\n");
                    // just assign the root as parent
                    cur  = DirIDmap.find(0);
                    depth = ((*cur).second).depth+1;
                    ((*cur).second).files++;
                    sprintf(parent_path,"%s%sF%d", PARENT_PATH, ((*cur).second).path, i);

                }
                else {
                    count_atbin=0;
                    do {
                        bin_atdepth = montecarlo_dirfilescount(); // which bin it goes to
                        //cout << "bin_atdepth: " << bin_atdepth << " depth " << depth-1 <<endl;

                        if(bin_atdepth == 0 ) { // BUG 
                            print_debug1(1, "BUG: bin needs to be > 0; first bin is for empty dirs\n");
                            exit(-1);
                        }
                        else {// pick a random dir uniformly from that bin
                            count_atbin = Dircountfilesmmap[depth-1].count(bin_atdepth); 
                            if(count_atbin>1)
                                dirchosen = rv_dfc2.uniformDiscrete(0,count_atbin-1); 
                            else if (count_atbin==1)
                                dirchosen = 0;
                        }
                        print_debug1(0, "countatbin: %d dirchosen: %d\n", count_atbin, dirchosen);
                        if(count_atbin==0) {
                            print_debug(1, "BUG: count_atbin : %d\n", count_atbin);
                            /*cout << "Depth: " << depth << " Binatdepth " << bin_atdepth <<\
                              " Dirchosen: " << dirchosen << " countatbin: " << count_atbin << endl;
                            */
                        }
                    }
                    while(count_atbin <1);
                    idcppp = Dircountfilesmmap[depth-1].equal_range(bin_atdepth); 
                    idcit2 = idcppp.first;
                    advance(idcit2, dirchosen);

                    // Given the chosen dir within the bin. get Dir details
                    cur  = DirIDmap.find((*idcit2).second);
                    depth = ((*cur).second).depth+1;
                    ((*cur).second).files++;
                    sprintf(parent_path,"%s%sF%d", PARENT_PATH, ((*cur).second).path, i);
                }    
            }
            else {
                dirppp = DirDepthmultimap.equal_range(depth-1);
                int countatdepth = (int)DirDepthmultimap.count(depth-1);
                if(countatdepth>1)
                    data2 = (long double) rv_parentdir.uniformDiscrete(0,countatdepth );
                else if (countatdepth==1)
                    data2 = 0;
                else {
                    print_debug1(1, "No directory at chosen depth: BUG!\n");
                    exit(-1);
                }
                it3 = dirppp.first;
                advance(it3, (int)data2);
                ((*it3).second).files++;
                sprintf(parent_path,"%s%sF%d", PARENT_PATH, ((*it3).second).path, i);
            }
            
        
        }
        else { 
            /* User has specified not to care about depth selection for files
               pick randomly! */
            data2 = (long double) rv_parentdir.uniformDiscrete(0, (int)IMP_input->Numdirs-1);
            cur  = DirIDmap.find((int)data2);
            depth = ((*cur).second).depth+1;
            ((*cur).second).files++;
            sprintf(parent_path,"%s%sF%d", PARENT_PATH, ((*cur).second).path, i);
        }
        
        if(IMP_input->Printwhat[pw_depth]==1) {
            print_debug1(1, "FileDepth: %d\n", depth);
        }
        
        //(*li).files++; // increment the file count for this directory
        //sprintf(parent_path,"%s%sF%d", PARENT_PATH, (*li).path, i);
        
        if(IMP_input->Printwhat[pw_tree]==1) {
            print_debug1(1, "tree: %s, filedepth: %d size: %Lf\n",\
                parent_path, depth, data1);
        }
        
        /* ****** End of parent directory selection ************/
       
       *(filearray+ NUM_FILE_ATTRIBS*i + FILE_SIZE)=data1;
       *(filearray+ NUM_FILE_ATTRIBS*i + PARENT_DIR)=data2;

        /* issue file creation for this file */
        total_file_size += make_generic_file(parent_path,data1, depth, fp_log); 
        
        __Ntime gettimeofday(&et, NULL);
        __Ntime total_time += diff_time(st, et)/1000; // in milli seconds
    }
    if(IMP_input->Printwhat[pw_size]==1){
        print_debug1(1, "total_file_size: %Lf (GB), Time(s):%f\n", total_file_size/ScaleByUnit("GB"),total_time/1000);
    }
    
    /* ***********************************************
       Free data structures and state
       Stop timers
    */

    __Ntime gettimeofday(&main_time_end, NULL);
    
    exit();
    
    free(filearray);
    free(IMP_input);
    free(Dirs);
    LD.clear();
    DirIDmap.clear();
    DirDepthmultimap.clear(); 
    
    if(ACTUAL_LOG_CREATION)
        fclose(fp_log);

    return 1;
}
