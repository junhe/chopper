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
** altlist.c
** A list of alts.
** 21 August 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "alt.h"
#include "altlist.h"
#include "memory.h"

altlist altlist_constructor (void)
{
    altlist newlist = (altlist) check_malloc (sizeof(altlist_struct));
    newlist->list = NULL;
    newlist->size = 0;
    return (newlist);
}

void altlist_insert (altlist l, alt rec)
{
    l->size++;
    l->list = (alt *) check_realloc (l->list, sizeof(alt) * l->size);
    l->list[l->size-1] = rec;
}

void altlist_free (altlist l)
{
    int i;
    
    for (i = 0; i < l->size; i++) {
	free(l->list[i]);
    }
    
    free(l->list);
    l->size = 0;
}

int altlist_get_cur (altlist alist, int tnode_id, int occurrence_id)
{
    int alist_cnt = 0;

    while (alist_cnt < alist->size) {
		if ((alist->list[alist_cnt]->id1 == tnode_id) && 
			(alist->list[alist_cnt]->id2 == occurrence_id)) {
			return (alist->list[alist_cnt]->cur);
		}
		alist_cnt++;
    }
    
    fprintf(stderr, "alist: getting current length of a non-existent tnode!\n");
    exit (-1);
}
