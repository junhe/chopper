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
** memory.c
** Safe functions for memory usage
*/

#include <stdio.h>
#include <stdlib.h>
#include "memory.h"

void * check_malloc (size_t size)
{
    void * ptr = malloc (size);
    if (!ptr) {
	fprintf(stderr, "check_malloc: out of memory! (fatal)\n");
	exit(-1);
    }
    return ptr;
}

void * check_realloc (void * place, size_t new_size)
{
    place = realloc (place, new_size);
    if (!place) {
	fprintf(stderr, "check_realloc: out of memory! (fatal)\n");
	exit(-1);
    }
    return place;
}

void * check_calloc (size_t num_els, size_t el_size)
{
    void * ptr = calloc (num_els, el_size);

    if (!ptr) {
	fprintf(stderr, "check_malloc: out of memory! (fatal)\n");
	exit(-1);
    }
    return ptr;
}
