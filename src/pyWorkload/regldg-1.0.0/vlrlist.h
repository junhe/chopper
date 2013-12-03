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
** vlrlist.h
** A list of vlrs.
** 21 August 2004
*/

#ifndef VLRLIST_H
#define VLRLIST_H

#include <stdio.h>
#include "vlr.h"

struct _vlrlist {
    vlr * list;
    int size;
};
typedef struct _vlrlist vlrlist_struct;
typedef struct _vlrlist *vlrlist;

vlrlist vlrlist_constructor (void);
void vlrlist_insert (vlrlist, vlr);
void vlrlist_free (vlrlist);
int vlrlist_get_cur_length(vlrlist, int);

#endif
