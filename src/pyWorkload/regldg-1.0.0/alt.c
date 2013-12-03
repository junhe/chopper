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
** alt.c
** A record to keep track of alternation nodes.
** 15 August 2004
** Updated 15 April 2006
*/

#include <stdio.h>
#include <stdlib.h>
#include "alt.h"
#include "memory.h"

alt alt_constructor (void)
{
    alt newalt = (alt) check_malloc (sizeof(alternationrecord));
    newalt->id1 = 0;
    newalt->id2 = 0;
    newalt->min = 0;
    newalt->max = 0;
    newalt->cur = 0;
    return (newalt);
}

void alt_set_id1 (alt v, int i)
{
    v->id1 = i;
}

void alt_set_id2 (alt v, int i)
{
    v->id2 = i;
}

void alt_set_min (alt v, int i)
{
    v->min = i;
}

void alt_set_max (alt v, int i)
{
    v->max = i;
}

void alt_set_cur (alt v, int i)
{
    v->cur = i;
}

int alt_get_id1 (alt v)
{
    return (v->id1);
}

int alt_get_id2 (alt v)
{
    return (v->id2);
}

int alt_get_min (alt v)
{
    return (v->min);
}

int alt_get_max (alt v)
{
    return (v->max);
}

int alt_get_cur (alt v)
{
    return (v->cur);
}
