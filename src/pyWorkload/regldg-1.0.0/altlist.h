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
** altlist.h
** A list of alts.
** 21 August 2004
*/

#ifndef ALTLIST_H
#define ALTLIST_H

#include <stdio.h>
#include "alt.h"

struct _altlist {
    alt * list;
    int size;
};
typedef struct _altlist altlist_struct;
typedef struct _altlist *altlist;

altlist altlist_constructor (void);
void altlist_insert (altlist, alt);
void altlist_free (altlist);
int altlist_get_cur(altlist, int, int);
#endif
