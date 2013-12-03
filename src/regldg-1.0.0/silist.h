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
** silist.h
** A simple list structure for integers.
** Best for small lists -- the list is stored in consecutive
** memory addresses.
** 27 February 2004
*/

#ifndef SIMPLE_INTEGER_LIST
#define SIMPLE_INTEGER_LIST

struct _silist {
    int size;
    int * list;
};
typedef struct _silist silist_struct;
typedef struct _silist * silist;

silist silist_constructor(void);
void silist_init(silist);
int silist_find(silist, int);
int silist_get_size(silist);
int silist_get_element_n(silist, int);
void silist_insert(silist, int);
void silist_free(silist);
void silist_display(silist);
silist silist_copy_deep(silist);
void silist_remove_last(silist);

#endif
