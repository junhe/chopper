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
** build_structs.h
** Read the element tree, and build permutation structures
** for each possible arrangement of the varying length
** quantifiers.
*/

#ifndef BUILDSTRUCTS_H
#define BUILDSTRUCTS_H

#include <stdio.h>
#include <stdlib.h>
#include "alt.h"
#include "altlist.h"
#include "grouprecord.h"
#include "grouplist.h"
#include "re_perm.h"
#include "tnode.h"
#include "vlr.h"
#include "vlrlist.h"

void buildstructs_gvlists (tnode, grouplist, vlrlist, altlist);
void buildstructs_fill_perm (re_perm, tnode, grouplist, vlrlist, altlist);
int buildstructs_new_perm (tnode, vlrlist, altlist);
int buildstructs_perm_vlist (vlrlist, int);
int buildstructs_perm_alist (altlist, int);
int buildstructs_is_useless_perm (tnode, vlrlist, altlist, int);
#endif
