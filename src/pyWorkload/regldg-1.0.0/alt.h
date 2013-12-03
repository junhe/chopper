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
** alt.h
** A record to keep track of alternation nodes.
** 21 August 2004
** Updated 15 April 2006 - added a new id section
**   id1 for tnode
**   id2 for same tnode, different occurrence
**   used in regexps with a multiple/variable length group with alternation like (a|b){2}
*/

#ifndef ALT_H
#define ALT_H

struct _alternationrecord {
    int id1;
    int id2;
    int min;
    int max;
    int cur;
};
typedef struct _alternationrecord alternationrecord;
typedef struct _alternationrecord *alt;

alt alt_constructor (void);

void alt_set_id1 (alt, int);
void alt_set_id2 (alt, int);
void alt_set_min (alt, int);
void alt_set_max (alt, int);
void alt_set_cur (alt, int);

int alt_get_id1 (alt);
int alt_get_id1 (alt);
int alt_get_min (alt);
int alt_get_max (alt);
int alt_get_cur (alt);

#endif
