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
** vlr.c
** A record to keep track of alternations and variable length nodes.
** 15 August 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "vlr.h"
#include "memory.h"

vlr vlr_constructor (void)
{
    vlr newvlr = (vlr) check_malloc (sizeof(variablelengthrecord));
    newvlr->id = 0;
    newvlr->min = 0;
    newvlr->max = 0;
    newvlr->cur = 0;
    return (newvlr);
}

void vlr_set_id (vlr v, int i)
{
    v->id = i;
}

void vlr_set_min (vlr v, int i)
{
    v->min = i;
}

void vlr_set_max (vlr v, int i)
{
    v->max = i;
}

void vlr_set_cur (vlr v, int i)
{
    v->cur = i;
}

int vlr_get_id (vlr v)
{
    return (v->id);
}

int vlr_get_min (vlr v)
{
    return (v->min);
}

int vlr_get_max (vlr v)
{
    return (v->max);
}

int vlr_get_cur (vlr v)
{
    return (v->cur);
}
