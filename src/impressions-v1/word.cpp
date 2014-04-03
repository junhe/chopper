
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


#include "word.h"
#include "impress.h"

char bnc_words[SIZE_BNC_CORPUS][SIZE_BNC_MAX_WORDLEN];
int bnc_wordlen[SIZE_BNC_CORPUS];
float bnc_popularity[SIZE_BNC_CORPUS];

char random_word[MAX_WORD_LENGTH];
double word_popularity[MAX_WORD_LENGTH];
//extern inputset * IMP_input;
int precision = 1;

/* ****************************************************

   Initialize word popularity according to the power
   distribution in Studia Linguistica 2004 Vol 58(1) 
   by Sigurd, Eeg-Olofsson, Weijer
   F(L) = a * pow(L,b) * pow(c,L
   a,b,c are language specific constants)

 **************************************************** */
void set_word_popularity () {
    int L;
    double a=11.74; 
    double b=3;
    double c=0.4;
    int i=0;
    for (L = 1; L <= MAX_WORD_LENGTH; L++) {
        word_popularity[L-1] = a * pow(L,b) * pow(c,L);
    }  

    // 100 is the total word popularity with 3 decimal precision 
    while(i<WORD_PRECISION) 
    {
        precision*=10; 
        i++;
    }
}

/* ****************************************************
   
   According to the BNC frequency list, "THE" is most 
   popular and so on. Read from file and populate array
   of word popularity. The 111 word long corpus takes 
   care of 53.35% of the words, for the rest we use the 
   word length model.
   Cutoff word popularity at least 0.1% or 0.001 fraction.
   Expects the bnc corpus file in the same folder.

 **************************************************** */
int init_word_bnc_frequency_list () {
    FILE * bnc_fp;
    char bnc_file[100];
    char word[SIZE_BNC_MAX_WORDLEN], len[2], freq[20];
    int i =0;
    sprintf(bnc_file, "%s",bnc_corpus);
    if( (bnc_fp = fopen(bnc_file, "r")) == NULL) {
        printf("Error opening BNC corpus file for word popularity\n");
        return -1;
    }
    else { // success
        while(!feof(bnc_fp)) {
            fscanf(bnc_fp, "%s %s %s\n", word, len, freq);
            strcpy(bnc_words[i], word);
            bnc_wordlen[i] = atoi(len);
            bnc_popularity[i] = atof(freq);
            i++;
        }
    }

    fclose(bnc_fp);
    return 1;
}

/* ****************************************************

   Generate a single word according to the work length 
    model by Sigurd Et. Al.

 **************************************************** */
int montecarlo_word(char * random_word) {
    /* relative popularity of extensions*/
    int i=0, wc=0;
    int rand_char;
    srand(deseeder());
    int token = rand() % (100 * precision); 
    double token_until_now=word_popularity[i]*precision;
    while (token_until_now < token) {
        i++;
        token_until_now+=word_popularity[i]*precision;
    } 

    for(wc =0; wc < i+1; wc ++) {
        rand_char = ( rand()% 26);
        print_debug(0, "%d %c ", rand_char, (char) (rand_char+97 ));
        random_word[wc] = (char) (rand_char+97);
    }
    
    //random_word[wc] = ' '; // blank space at the end
    random_word[wc] = '\0';
    
    print_debug(0, "Length %d token %Ld word %s\n", i+1, token, random_word); 
    return i+1;
} 

/* ****************************************************

   Generate a single word according to the BNC popularity
    for the head, and resort to the Sigurd model for the 
    tail.

 **************************************************** */
int bnc_popular_word(char * random_word) {
    int word_len=0;
    srand(deseeder());
    
    /* relative popularity of words*/
    int i=0, wc=0;
    int rand_char;

    /* precision of 100 => token can be 0-10,000)
       in which case TOTAL of 5339 can be matched */
    int token = rand() % (100 * precision); 

    /* default to word length for tail words */
    if(token >= BNC_TOTAL_POPULARITY) { // currently 5339
        word_len = montecarlo_word(random_word);
    }
    else {
        double token_until_now=bnc_popularity[i]*precision;
        while (token_until_now < token) {
            i++;
            token_until_now+=bnc_popularity[i]*precision;
        }
        strncpy(random_word, bnc_words[i], bnc_wordlen[i]);
        word_len = bnc_wordlen[i];
    }
    return word_len;
}


/* ****************************************************

   Generate a block of words for the buffer pointed to 
    by buf. Choice of model selection is specified in
    input file.

 **************************************************** */
int random_word_block(char * buf) {

    int buf_len = 0, word_len=0;
    while(buf_len < MY_BLOCK_SIZE) {
        if(IMP_input->Flag[sf_wordfreq]==1) { // Sigurd Et. Al.
            word_len = montecarlo_word(random_word);
        }
        else if(IMP_input->Flag[sf_wordfreq]==2) { // BNC word popularity
            word_len = bnc_popular_word(random_word);
        }
        else {
            word_len = 7;
            strncpy(random_word, "impress", 7);
        }

        if(buf_len + word_len >= MY_BLOCK_SIZE)
            word_len = MY_BLOCK_SIZE - buf_len;

        strncpy(buf + buf_len, random_word, word_len);
        strncpy(buf + buf_len + word_len , " ", 1);
        buf_len+=word_len+1;
    }
    
    print_debug(0, "random block -- : %s\n", buf);
}
