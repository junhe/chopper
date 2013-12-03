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
** grouplist.h
** A list of group records
** 21 August 2004
*/

#ifndef GROUPLIST_H
#define GROUPLIST_H

#include "grouprecord.h"
#include "tnode.h"

struct _grouplist {
    group * list;
    int size;
};
typedef struct _grouplist grouplist_struct;
typedef struct _grouplist *grouplist;

grouplist grouplist_constructor (void);
void grouplist_insert (grouplist, group);
void grouplist_free (grouplist);
tnode grouplist_get_group_tnode (grouplist, int);

#endif
