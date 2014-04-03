#include <math.h>
#include "montecarlo.h"


#define MAX_WORD_LENGTH 25

// on a scale of 0-3 (less to more)
#define WORD_PRECISION 2

// BNC related
#define bnc_corpus "./bnc_corpus.dat"
#define SIZE_BNC_CORPUS 111
#define SIZE_BNC_MAX_WORDLEN 20
#define BNC_TOTAL_POPULARITY 5339


int init_word_bnc_frequency_list ();
int montecarlo_word(char * random_word);
void set_word_popularity(void);
int random_word_block(char * random_block);
