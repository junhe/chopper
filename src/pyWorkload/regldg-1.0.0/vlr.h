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
** vlr.h
** A record to keep track of alternations and variable length nodes.
** 15 August 2004
*/

#ifndef VLR_H
#define VLR_H

struct _variablelengthrecord {
    int id;
    int min;
    int max;
    int cur;
};
typedef struct _variablelengthrecord variablelengthrecord;
typedef struct _variablelengthrecord *vlr;

vlr vlr_constructor (void);

void vlr_set_id (vlr, int);
void vlr_set_min (vlr, int);
void vlr_set_max (vlr, int);
void vlr_set_cur (vlr, int);

int vlr_get_id (vlr);
int vlr_get_min (vlr);
int vlr_get_max (vlr);
int vlr_get_cur (vlr);

#endif
