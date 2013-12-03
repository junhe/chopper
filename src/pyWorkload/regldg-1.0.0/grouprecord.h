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
** grouprecord.h
** A record to remember features about a group
** 21 August 2004
*/

#ifndef GROUP_RECORD_H
#define GROUP_RECORD_H

#include "tnode.h"

struct _group_record {
    tnode node;
    int current_length;
};
typedef struct _group_record group_record;
typedef struct _group_record *group;


group group_constructor (void);
tnode group_get_node (group);
int group_get_length (group);
void group_set_node (group, tnode);
void group_set_length (group, int);

#endif
