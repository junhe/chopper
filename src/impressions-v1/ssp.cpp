
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


//#include <stdio.h>
//#include <math.h>
//#include "stat.h"
#include "impress.h"

/* THIS IS THE ONLY VALUE YOU NEED TO CHANGE IN THE CODE */
//#define N 1000       // max entries in original sample
//#define MAX_ALPHA (N*1) // can be changed 

/* max iterations allowed to converge suggested in the paper 
"A Fast Approximation Algorithm for the Subset-Sum Problem"
Bartosz Przydatek
IFORS 1999
*/

//#define MAX_RAND_TRIALS (N*100)

#define BETA_MAX 0.010   // maximum error allowed
#define BETA_MAX_1 0.020 // half of max error reached

/* To check if the constrained distribution is maintained
    print the original N and the oversampled final N
*/
#define Accuracy_Mode 

// #define PRINTER

long double binsize_1[50], binsize_2[50];
int bincounter_1[50], bincounter_2[50];

// For the hybrid tail selection bias 
extern double poisson_mu;
extern double poisson_sigma;

extern double alpha1;
extern double pareto_base1;
extern double pareto_shape1;
extern double bias;


int compfunc_ld(const void *x, const void *y) 
{
    long double pp,qq;
    int t;
    pp = (long double)(*(long double *)x);
    qq = (long double)(*(long double *)y);
    //print_debug(0,"%d %d\n", pp, qq);
    if (pp < qq) t = -1; 
    else if (pp == qq) t = 0;
    else  t = 1;
    return t;
}


int experimental_center_1 (double data1) {
    if(data1!=0) {
        bincounter_1[(int)floor(log2(data1))+1]++;
        binsize_1[(int)floor(log2(data1))+1]+=data1;
    }
    else
        bincounter_1[0]++;
}

int experimental_center_2 (double data1) {
    if(data1!=0) {
        bincounter_2[(int)floor(log2(data1))+1]++;
        binsize_2[(int)floor(log2(data1))+1]+=data1;
    }
    else
        bincounter_2[0]++;
}

//int main () {
int subsetsumconstraint(long double * Numbers_orig, int N) {

    int MAX_ALPHA       = N * 1;
    int MAX_RAND_TRIALS = N * 100;

    //double Num_soln[N];
    long double * Numbers = (long double *) malloc(sizeof(long double)*(N+MAX_ALPHA));
    long double * T       = (long double *) malloc(sizeof(long double)*MAX_ALPHA);
    int * soln_vector     = (int *) malloc(sizeof(int)*(N+MAX_ALPHA));
    int * num_vector     = (int *) malloc(sizeof(int)*(N));
    int * t_vector     = (int *) malloc(sizeof(int)*(MAX_ALPHA));
   
    if(!Numbers || !T || !soln_vector || !num_vector || !t_vector) {
        print_debug(1, "ERROR: allocating memory for constraint solving\n");
        return 1;
    }

    /*
    int soln_vector[N+MAX_ALPHA];
    int num_vector[N];
    int t_vector[MAX_ALPHA];
    */
    
    long double Sum_D= IMP_input->FSused; //60000*N;
    long double Sum_C=0, Sum_phase1=0;
    int toggle =1, alpha =0, Na=N, i =0, j=0, num_soln=0;
    double beta=0, best_beta=0, abs_error =0; //allowed error, abs error
    int from_start=0; 
    //double mu= 8.34, sigma = 2.38;
    
    Random rv_constraint(deseeder());

    int LOCKER = 0;

    for (i =0; i< N ; i++) {
        Numbers[i]= Numbers_orig[i]; //floor(rv_constraint.lognormal(0, mu, sigma));
        #ifdef Accuracy_Mode
        //experimental_center_1(Numbers[i]);
        #endif
        
        soln_vector[i]=0; // empty
        Sum_C += (long double) Numbers[i];
        beta = abs(Sum_D - Sum_C)/Sum_D;
    }

    for (i=N; i< N+MAX_ALPHA; i++) {
        soln_vector[i]=0;
    }

    /*
       if (Sum_C < Sum_D ) { // pre-LOCKED!
       LOCKER=1;
       Sum_phase1 = Sum_C;
       print_debug(1,"Prelocked!! ... ");
       }
    */

    print_debug(1,"Initial stat beta: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d\n",\
            beta, Sum_C/1000, Sum_D/1000, num_soln, N);
    if (beta <= BETA_MAX){
        print_debug(1,"beta_0: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d\n",\
                beta, Sum_C/1000, Sum_D/1000, num_soln, N);
        print_debug(1,"Initial success!!!\n");
        return 1;
    }
    else if (beta <= BETA_MAX_1){
        print_debug(1,"beta_1: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d\n",\
                beta, Sum_C/1000, Sum_D/1000, num_soln, N);
        print_debug(1,"Initial Half success!!!\n");
    }

    /* ********************************************************
       
       Start resampling

     * ********************************************************/
    

    i=0; 
    while (i<MAX_ALPHA && beta > BETA_MAX) {
        Na = N + alpha;
        
        if( (bias = (double)(rv_constraint.uniformDiscrete(0, 100000-1))) <= alpha1)
            Numbers[Na] = (long double) floor(rv_constraint.lognormal(0, poisson_mu, poisson_sigma));
        else if (bias > alpha1) //&& bias <= alpha2*100000)
            Numbers[Na] = (long double) floor(rv_constraint.pareto(pareto_shape1)*pareto_base1); 
        
        //Numbers[Na]= floor(rv_constraint.lognormal(0, mu, sigma));

        /* *****************
         * First Phase of Approximation Algorithm 
         * *****************/

        if(LOCKER ==0) {

            for (j=0; j<= Na; j++) {
                soln_vector[j]=0;
            }
            Sum_C=0;
            qsort((void*)&Numbers,(size_t)(Na+1),(size_t)sizeof(long double),compfunc_ld);

            int choice =0, rand_trials=0;
            j=0;
            while(j<N && rand_trials < MAX_RAND_TRIALS)  
            {   
                
                // while we don't have N numbers
                //choice = rand()%N; // 0 to N-1
                choice = j; // 0 to N-1
                
                if(Numbers[choice]+Sum_C <= Sum_D && soln_vector[choice]==0) {
                    soln_vector[choice]=1;
                    Sum_C+=Numbers[choice];

                    //num_vector[j]=choice;
                    //Num_soln[j]=Numbers[choice];// soln array. Not used rgt now
                    j++;
                }
                rand_trials++;
            }
            print_debug(1,"test: J: %d Sum_C: %Lf Sum_D: %Lf rand_trials %d T# %d\n",\
                    j, Sum_C/1000, Sum_D/1000, rand_trials, Na);

            if(j==N)    // Lock the first phase
            {   
                print_debug(1,"LOCKING initial set: J: %d Sum_C: %Lf\n", j, Sum_C/1000);
                LOCKER=1;
            }

            Sum_phase1 = Sum_C;
        }

        /* *****************
         * First Phase Ends, Phase 2 Begins 
         * *****************/

        int k=0;
        Sum_C = Sum_phase1;
        for (k=0; k<N; k++) {
            soln_vector[k]=1;
        }
        for (k=N; k<=Na; k++) {
            soln_vector[k]=0;
        }
        k=0;
        for(int c =0; c <= Na; c++) {
            if(soln_vector[c]==0) {
                t_vector[k]=c;
                T[k]=Numbers[c];
                k++;
            }
        }
        qsort((void*) &T, (size_t) (alpha+1), (size_t) sizeof(long double),compfunc_ld);

        #ifdef PRINTER
        print_debug(1,"\n-------- T -------------------\n");
        for (k =0; k<=alpha ; k++) {
            print_debug(1,"%f ", T[k]/1000);
        }
        
        print_debug(1,"\n-----------N ----------------\n");
        
        for (k =0; k< N ; k++) {
            print_debug(1,"%f ", Num_soln[k]/1000);
        }
        
        for (k =0; k<=Na ; k++) {
            print_debug(1,"%f ", Numbers[k]/1000);
        }
        
        print_debug(1,"\n------------- J: %d\n", j);

        #endif
        
        /*
           Sum_C=0;
           for (k =0; k<= Na; k++) {
           Sum_C += (long double) Numbers[k]*soln_vector[k];
           }
        */

        // REMEMBER THAT SOLUTION ARRAY IS SCATTERED ACROSS N+ALPHA

        if( j== N && Sum_C <= Sum_D) {
            
            /* There exists N random numbers such that their sum < Sum_D
               Phase 2 continues
            */  


            //int random_k=0;
            abs_error = abs(Sum_C - Sum_D);
            for (k=0; k<N; k++) {

                /* Traverse in random order */

                //random_k = rand()%N;
                // do this for all soln_vector entries
                // go in RANDOM ORDER NOT IN SERIAL ORDER IF NUMBERS ARE SORTED
                // do not bias the file sizes to remove smaller numbers

                for(int l= alpha; l>=0; l--) {
                    
                    /* start with the biggest */
                    // if(soln_vector[t_vector[l]]==0 && T[l]> Num_soln[k] && (T[l]-Num_soln[k]) <= abs_error) {
                    
                    if(soln_vector[N+l]==0 && T[l]> Numbers[k] && (T[l]-Numbers[k]) <= abs_error) {
                        /* since our array is sorted we stop at first match */

                        //soln_vector[num_vector[k]]=0;
                        //soln_vector[t_vector[l]]=1;
                        soln_vector[N+l]=1;
                        soln_vector[k]=0;

                        break;
                    }
                }
                
                Sum_C=0;
                num_soln=0;
                
                for (int kk =0; kk<= Na; kk++) {
                    Sum_C += (long double) Numbers[kk]*soln_vector[kk];
                    if(soln_vector[kk]==1) {
                        num_soln++;
                    }
                }
                
                abs_error = abs(Sum_C - Sum_D);
                beta = abs_error/Sum_D;
                
                /* if there is no match move onto the next */
                }

                /* completed one pass of local improvement */
                if(beta < best_beta)
                    best_beta = beta;
            }
            else {
                // if solution is not feasible with current data: resample
                print_debug(0,"Sum_C exceeds Sum_D: resampling...\n");
            }
            
            #ifdef PRINTER
            for (int k =0; k<= Na; k++) {
                print_debug(1,"(%f,%d) ", Numbers[k]/1000, soln_vector[k]);
            }
            #endif
            
            if(beta <= BETA_MAX_1 && toggle) {
                print_debug(1,"beta_2: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d\n",\
                        beta, Sum_C/1000, Sum_D/1000, num_soln, i+1+N);
                toggle=0;
            }

            print_debug(0,"beta_trial: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d\n",\
                beta, Sum_C/1000, Sum_D/1000, num_soln, i+1+N);

            alpha++;
            i++;
            Sum_C =0;
        }
        
        num_soln=0; 
        from_start=0;
        for(j=0; j<= Na; j++){
            if(soln_vector[j]==1) {
                num_soln++;
                Sum_C += Numbers[j]*soln_vector[j];
                Numbers_orig[from_start++]=Numbers[j];
            }
        }
        
        abs_error = abs(Sum_C - Sum_D);
        beta = abs_error/Sum_D;
        
        print_debug(1,"beta_f: %f Sum_C: %Lf Sum_D: %Lf num_soln %d T# %d from_start %d\n",\
                beta, Sum_C/1000, Sum_D/1000, num_soln, i+N, from_start);
        
        #ifdef PRINTER
        for (int k =0; k<= Na; k++) {
            print_debug(1,"(%f,%d) ", Numbers[k]/1000, soln_vector[k]);
        }
        #endif
        
        #ifdef Accuracy_Mode
        for(j=0; j<= Na; j++){
            if(soln_vector[j]==1) {
                print_debug(0,"Number2: %f\n", Numbers[j]);
                experimental_center_2(Numbers[j]); 
            }
        }
        #endif

        #ifdef PRINTER
        for(j =0; j< 40; j++) {
            print_debug(1,"%d \t%d  \t%d \t%Lf \t%Lf\n", j, bincounter_1[j], \
                    bincounter_2[j], binsize_1[j], binsize_2[j]);
        }
        
        print_debug(1,"num_soln %d\n", num_soln);
        #endif
        
        /*
        for(j =0; j< N; j++) {
            print_debug(0,"%Lf ",Num_soln[j]);
            print_debug(1,"%d ", num_vector[j]);
        }
        print_debug(1,"=============================\n");
        print_debug(1,"\n");
        for(j =0; j<= alpha; j++) {
            print_debug(0,"%Lf ",T[j]);
            print_debug(1,"%d ", t_vector[j]);
        }
        print_debug(1,"=============================\n");
        print_debug(1,"\n");
        for(j =0; j<=Na; j++) {
            print_debug(1,"%d ",soln_vector[j]);
        }
        print_debug(1,"\n");
        */
    
    if(Numbers) 
        free(Numbers);
        
    if(T)
        free(T);
        
    if(soln_vector)
        free(soln_vector);
        
    if(num_vector)
        free(num_vector);
        
    if(t_vector)
        free(t_vector);
    return 1;
}
