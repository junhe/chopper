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

/* ********************************
    
    Depth bias for file count and size
    is currently hard coded based
    on data from FAST 2007 paper
    The arrays depthcount_prob[] and
    depth_meansize[] can be changed 
    here itself to provide different
    depth biases as needed by the user

   ********************************/


/* ********************************
    
    probability of a file being at depth. 
    depth = index of array+1 
    i.e. first entry is for depth 1 P(D==1)
    last entry is P(D>=20)

   ********************************/

#define Total_depthcount_prob 10002

double depthcount_prob[] = {
2,
65,
695,
840,
1244,
1308,
2268,
1239,
861,
604,
425,
231,
108,
52,
26,
14,
7,
7,
4,
2
};


/* ********************************
    
    Mean file size at depth i;
    last entry is mean for D>=20 

   ********************************/

double depth_meansize[] = {
24.86384,
21.09487,
18.4079,
18.56599,
17.91258,
17.3991,
16.78398,
16.69379,
16.55786,
16.44346,
16.21963,
16.14762,
16.51491,
16.39439,
16.40987,
15.76278,
15.58079,
14.625,
14.68678,
14.0497 // average of depths 20 to 25
};



/* ********************************
    
    Multiplicative model for the placement of
    a file at a given depth taking into
    account the mean bytes at the depth
    and the count of files at that depth

   ********************************/
int fn_depthsize_prob (long double filesize) {

    double meansizediff[DEPTH_ENTRIES];
    double final_prob[DEPTH_ENTRIES];
    double totalsize_prob=0, totalprob=0;
    double sum1=0, sum2=0, sum3=0;
    int i =0;
    float token_until_now=0;
    int token;
    int factor = 100000;
    double depthsize_prob[DEPTH_ENTRIES];
    
    srand(deseeder());

    if(filesize ==0) 
        return rand()%max_dir_depth+1;

    for(i=0; i< DEPTH_ENTRIES; i++) {
        meansizediff[i]=(double) 1/fabsl(log2l(filesize)-(long double)depth_meansize[i]);
        
        print_debug(0,"%Lf %Lf %f\n", log2l(filesize), (long double)depth_meansize[i], meansizediff[i]);
        totalsize_prob+=meansizediff[i];
    }
    
    for(i=0; i< DEPTH_ENTRIES; i++) {
        final_prob[i]=(depthcount_prob[i]/Total_depthcount_prob)*\
            (meansizediff[i]/totalsize_prob);
    }
    
    for(i=0; i< DEPTH_ENTRIES; i++) {
        totalprob+=final_prob[i];
    }
    
    for(i=0; i< DEPTH_ENTRIES; i++) {
        print_debug(0, "Probsize[%d] %f; Probcount %f; Finalprob %f\n", i+1, \
            meansizediff[i]/totalsize_prob*100, depthcount_prob[i]/Total_depthcount_prob*100,\
                final_prob[i]/totalprob*100);
        sum1+= meansizediff[i]/totalsize_prob;
        sum2+= depthcount_prob[i]/Total_depthcount_prob;
        sum3+= final_prob[i]/totalprob;
    }
    print_debug(0,"sums %f, sumc %f sumt %f\n", sum1, sum2, sum3);
    
    i=0;
    do {
        token_until_now=0;
        token = rand() % factor;
        i=0;
        token_until_now=final_prob[i]/totalprob*factor;
        while (token_until_now < token) {
            print_debug(0,"%f %d\n", token_until_now , token);
            i++;
            token_until_now+=final_prob[i]/totalprob*factor;
        }
        if(i== DEPTH_ENTRIES-1) { // last bin is actually 20 to infinite ..not just 20
            i+= rand()%10;        // e.g., any depth between 20 and 30, if DEPTH_ENTRIES=20
        }
        print_debug(0,"Chosen %d, max_dir %d\n", i, max_dir_depth);
    }
    while(i > max_dir_depth);
    
    return i+1;
}

