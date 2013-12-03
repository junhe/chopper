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
** grouprecord.c
** A record to remember features about a group
** 21 August 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "grouprecord.h"
#include "memory.h"
#include "tnode.h"

group group_constructor (void)
{
    group newgroup = (group) check_malloc (sizeof(group_record));
    newgroup->node = NULL;
    newgroup->current_length = 0;
    return (newgroup);
}

tnode group_get_node (group g)
{
    return (g->node);
}

int group_get_length (group g)
{
    return (g->current_length);
}

void group_set_node (group g, tnode t)
{
    g->node = t;
}

void group_set_length (group g, int l)
{
    g->current_length = l;
}
