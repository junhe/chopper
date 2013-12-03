/* regldg version 1.0.0
** a regular expression grammar language dictionary generator
** (c) Patrick Cronin 2004-2006
** pcronin@loyola.edu
**
** Permission is granted to use, alter, and distribute this
** code under the terms of the GNU Public License.  A copy
** of this license should have been included with this
** software in the file gpl.txt.  If you need a copy, please
** visit http://www.gnu.org/copyleft/gpl.html.
**
** re_perm.c
** A list of charsets.  When a single character from each of the 
** charsets is selected, a single word of the regular expression
** grammar is created.
** 21 August 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include "data.h"
#include "re_perm.h"
#include "char_set.h"
#include "memory.h"
#include "silist.h"

extern gg g;
extern int num_words_already_output;

perm_atom perm_atom_constructor (void)
{
    perm_atom newatom = (perm_atom) check_malloc (sizeof(perm_atom_struct));
    newatom->chars = char_set_g_constructor();
    newatom->in_groups = silist_constructor();
    newatom->backref_id = 0;
    return(newatom);
}

void perm_atom_free (perm_atom atom)
{
    char_set_g_free(atom->chars);
    silist_free(atom->in_groups);
}

re_perm re_perm_constructor (void)
{
    re_perm newlist = (re_perm) check_malloc (sizeof(re_perm_struct));
    newlist->list = NULL;
    newlist->length = 0;
    return (newlist);
}

void re_perm_insert (re_perm p, perm_atom atom)
{
    p->length++;
    p->list = (perm_atom *) check_realloc (p->list, sizeof(perm_atom) * p->length);
    p->list[p->length-1] = atom;
//    p->list[p->length-1]->chars = char_set_g_constructor();
//    char_set_g_deep_copy(p->list[p->length-1], atom->chars);
}

void re_perm_free (re_perm p)
{
    int x;
    for (x = 0; x < p->length; x++) {
	perm_atom_free(p->list[x]);
    }
    free (p->list);
    p->list = NULL;
    p->length = 0;
}

void re_perm_generate_words (re_perm p)
{    
    char_set word = char_set_g_constructor();

	if ((g->num_words_output < 0) ||
		(num_words_already_output < g->num_words_output)) {
		re_perm_create_word (p, word);
		re_perm_output_word (word);
		char_set_g_free (word);
		num_words_already_output++;
	}

    while ( ((g->num_words_output < 0) ||
    	    (num_words_already_output < g->num_words_output)) &&
    	   re_perm_permute(p, 0)) {
		re_perm_create_word (p, word);
		re_perm_output_word (word);
		char_set_g_free (word);
		num_words_already_output++;
    }
}

int re_perm_permute (re_perm p, int pos_id)
{
    if (pos_id == p->length) {
		return(0);
    } else if (char_set_g_adv_pos(p->list[pos_id]->chars, 1) == 0) {
		/* put char_set's position at zero */
		char_set_g_adv_pos(p->list[pos_id]->chars, 0 - char_set_g_get_pos(p->list[pos_id]->chars));
		return(re_perm_permute (p, pos_id + 1));
    }
    return(1);
}

void re_perm_create_word (re_perm p, char_set word)
{
    int x, br_id;
    for (x = 0; x < p->length; x++) {
		br_id = p->list[x]->backref_id;
		if (br_id != 0) {
			/* we have a backref node */
			/* scan through the previous nodes in the re_perm to find
			** the nodes that are in group br_id.  If there is one,
			** put its current value into the word */
			re_perm_add_backref_text(p, word, br_id, x);
		} else {
			/* we have a regular node */
			char_set_g_insert_char(word, char_set_p_char_n(p->list[x]->chars, 0));
		}
    }
}

void re_perm_add_backref_text (re_perm p, char_set word, int br, int stop)
{
    int y;
    for (y = 0; y < stop; y++) {
		if (silist_find(p->list[y]->in_groups, br) != -1) {
			if (p->list[y]->backref_id != 0) {
				re_perm_add_backref_text(p, word, p->list[y]->backref_id, y);
			} else {
				char_set_g_insert_char(word, char_set_p_char_n(p->list[y]->chars, 0));
			}
		}
    }
}


void re_perm_output_word (char_set word)
{
    int l;
    
    if (char_set_g_size(word) <= g->max_word_length) {
		for (l = 0; l < char_set_g_size(word); l++) {
			if (g->readable_output && !isprint(char_set_g_char_n(word, l))) {
				printf("{%03d}", (unsigned char) char_set_g_char_n(word, l));
			} else {
				printf("%c", char_set_g_char_n(word, l));
			}
		}
		printf("\n");
    }
}

void re_perm_display_current (re_perm p)
{
    ;
}
