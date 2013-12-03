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
** grouplist.c
** A list of groups.
** 21 August 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "grouprecord.h"
#include "grouplist.h"
#include "memory.h"

grouplist grouplist_constructor (void)
{
    grouplist newlist = (grouplist) check_malloc (sizeof(grouplist_struct));
    newlist->list = NULL;
    newlist->size = 0;
    return (newlist);
}

void grouplist_insert (grouplist l, group rec)
{
    l->size++;
    l->list = (group *) check_realloc (l->list, sizeof(group) * l->size);
    l->list[l->size-1] = rec;
}

void grouplist_free (grouplist l)
{
    int i;
    
    for (i = 0; i < l->size; i++) {
	free(l->list[i]);
    }
    
    free(l->list);
    l->size = 0;
}

tnode grouplist_get_group_tnode (grouplist glist, int groupnum)
{
    if (groupnum > glist->size) {
	fprintf(stderr, "vlist: getting current length of a non-existent tnode!\n");
	exit (-1);
    }

    return (glist->list[groupnum-1]->node);
}
