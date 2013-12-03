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
** silist.c
** A simple list structure for integers.
** Best for small lists -- the list is stored in consecutive
** memory addresses.
** 27 February 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h> // for memmove()
#include "memory.h"
#include "silist.h"

silist silist_constructor(void)
{
    silist newsilist = (silist) check_malloc (sizeof(silist_struct));
    silist_init (newsilist);
    return (newsilist);
}

void silist_init(silist s)
{
    s->size = 0;
    s->list = NULL;
}

int silist_find(silist s, int n)
{
    int c=0;
    
    while (c < s->size) {
	if (s->list[c] == n) {
	    return(c);
	}
	c++;
    }
    /* not found */
    return(-1);
}

int silist_get_size(silist s)
{
    return (s->size);
}

int silist_get_element_n(silist s, int n)
{
    if (n >= s->size) {
	fprintf(stderr, "silist: a non-existant element was requested. (non-fatal)\n");
	return (-1);
    }
    return (s->list[n]);
}

void silist_insert(silist s, int n)
{
    s->list = (int *) check_realloc (s->list, sizeof(int) * (s->size + 1));
    s->list[s->size] = n;
    s->size++;
}

void silist_free(silist s)
{
    if (s->list != NULL) {
	free (s->list);
	s->list = NULL;
    }
    free(s);
}

void silist_display(silist s)
{
    int c;
    printf("list size: %d\n", s->size);
    for(c=0; c<s->size; c++) {
	printf("element %d: %d\n", c, s->list[c]);
    }
}

silist silist_copy_deep(silist oldlist)
{
    int n;
    silist newlist = silist_constructor();
    
    newlist->size = oldlist->size;
    newlist->list = (int *) check_malloc (sizeof(int) * (newlist->size));

    for (n = 0; n < oldlist->size; n++) {
	newlist->list[n] = oldlist->list[n];
    }

    return (newlist);
}

void silist_remove_last (silist s)
{
    if (s->size == 0) {
	fprintf(stderr, "silist: tried to delete non-existant element");
	exit(-1);
    }

    s->size--;
    s->list = (int *) realloc (s->list, sizeof(int) * s->size);
}

