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
** build_structs.c
** Read the element tree, and build permutation structures
** for each possible arrangement of the varying length
** quantifiers.
*/

#include <stdio.h>
#include <stdlib.h>
#include "data.h"
#include "build_structs.h"
#include "alt.h"
#include "altlist.h"
#include "grouprecord.h"
#include "grouplist.h"
#include "re_perm.h"
#include "tnode.h"
#include "vlr.h"
#include "vlrlist.h"

extern gg g;

void buildstructs_gvlists (tnode n, grouplist glist, vlrlist vlist, altlist alist)
{
    group gr;
    vlr v;
    alt a;
    tnode * nptr = (tnode *) n->child_list;
    int i;

    /* if node is a leaf, and it is varying length, 
    **   add it to the vlist
    **
    ** if node is a group,
    **   add it to the group list
    **   if the same node is a varying length,
    **      add it to the vlist;
    **
    ** if node has children, visit them recursively
    */

    /* set the unending lengths to the maxlength */
    /* this is ghetto, and out of place! */
    if (n->length_max == -1) {
		n->length_max = g->max_word_length;
	}

    if (n->st == SplitType_Alternation) {
		/* If this node is a multi/variable group with alternation */
		if ((n->nt == NodeType_Group) && ((n->length_max != 0) || (n->length_min != 1))) {
			if (n->length_max == 0) {
				/* it is a fixed length */
				for (i = 0; i < n->length_min; i++) {
					a = alt_constructor();
					alt_set_id1(a, n->id);
					alt_set_id2(a, i);
					alt_set_min(a, 0);
					alt_set_max(a, n->num_children);
					altlist_insert(alist, a);
				}
			} else {
				/* it is a variable length */
				for (i = 0; i < n->length_max; i++) {
					a = alt_constructor();
					alt_set_id1(a, n->id);
					alt_set_id2(a, i);
					alt_set_min(a, 0);
					alt_set_max(a, n->num_children);
					altlist_insert(alist, a);
				}
			}
		} else {
			/* It is a (by all other accounts) normal alternation node */
			a = alt_constructor();
			alt_set_id1(a, n->id);
			alt_set_id2(a, 0);
			alt_set_min(a, 0);
			alt_set_max(a, n->num_children);
			altlist_insert(alist, a);
		}
	}

    if ((n->nt == NodeType_Leaf) && (n->length_max != 0)) {
		v = vlr_constructor();
		vlr_set_id(v, n->id);
		vlr_set_min(v, n->length_min);
		vlr_set_max(v, n->length_max);
		vlr_set_cur(v, n->length_min);
		vlrlist_insert(vlist, v);
    } else if (n->nt == NodeType_Group) {
		gr = group_constructor();
		group_set_node(gr, n);
		group_set_length(gr, 1);
		grouplist_insert(glist, gr);
		if (n->length_max != 0) {
			v = vlr_constructor();
			vlr_set_id(v, n->id);
			vlr_set_min(v, n->length_min);
			vlr_set_max(v, n->length_max);
			vlr_set_cur(v, n->length_min);
			vlrlist_insert(vlist, v);
		}
    }

    while (*nptr) {
		buildstructs_gvlists (*nptr, glist, vlist, alist);
		nptr++;
    }
}

void buildstructs_fill_perm (re_perm r, tnode t, grouplist glist, vlrlist vlist, altlist alist)
{
    int i,limit;
    perm_atom atom;
    tnode * nptr = (tnode *) t->child_list;

	/* if we are at a group node, parse this node the "length" number of times. */
	if (t->nt == NodeType_Group) {
		if (t->length_max != 0) {
			/* it is a variable length */
			limit = vlrlist_get_cur_length(vlist, t->id);
		} else {
			/* it is fixed length */
			limit = t->length_min;
		}
		
		for (i = 0; i < limit; i++) {
			nptr = (tnode *) t->child_list;
			/* visit the children */
			if (t->st == SplitType_Alternation) {
				/* it is an alternation */
				buildstructs_fill_perm(r, t->child_list[altlist_get_cur(alist, t->id, i)], glist, vlist, alist);
			} else {
				/* it has normal children */
				while (*nptr) {
					buildstructs_fill_perm(r, *nptr, glist, vlist, alist);
					nptr++;
				}
			}
		}
	}

    /* if we are at a leaf node, then put the node into permutation */
    else if (t->nt == NodeType_Leaf) {
		if (t->backref_id == -1) {
			/* it is a normal leaf */
			if (t->length_max != 0) {
				/* it is a variable length */
				limit = vlrlist_get_cur_length(vlist, t->id);
			} else {
				/* it is fixed length */
				limit = t->length_min;
			}
			
			for (i = 0; i < limit; i++) {
				atom = perm_atom_constructor();
				char_set_g_deep_copy(atom->chars, t->chars);
				atom->in_groups = silist_copy_deep(tnode_get_group_list(t));
				re_perm_insert(r, atom);
			}
		} else {
		    /* it is a backref */
			if (t->length_max != 0) {
				/* it is a variable length */
				for (i = 0; i < vlrlist_get_cur_length(vlist, t->id); i++) {
					atom = perm_atom_constructor();
					atom->backref_id = t->backref_id;
					atom->in_groups = silist_copy_deep(tnode_get_group_list(t));
					re_perm_insert(r, atom);
					//buildstructs_fill_perm(r, grouplist_get_group_tnode(glist, t->backref_id), glist, vlist, alist);
				}
			} else {
				/* it is a fixed length */
				for (i = 0; i < t->length_min; i++) {
					atom = perm_atom_constructor();
					atom->backref_id = t->backref_id;
					atom->in_groups = silist_copy_deep(tnode_get_group_list(t));
					re_perm_insert(r, atom);
					//buildstructs_fill_perm(r, grouplist_get_group_tnode(glist, t->backref_id), glist, vlist, alist);
				}
			}
		}
    }

    /* visit the children */
    else if (t->st == SplitType_Alternation) {
		/* it is an alternation */
		buildstructs_fill_perm(r, t->child_list[altlist_get_cur(alist, t->id, 0)], glist, vlist, alist);
	} else {
		/* it has normal children */
		while (*nptr) {
			buildstructs_fill_perm(r, *nptr, glist, vlist, alist);
			nptr++;
		}
    }
}

int buildstructs_new_perm (tnode head, vlrlist vlist, altlist alist)
{
    int vlist_stop;

	/* Perm the vlist */
    vlist_stop = buildstructs_perm_vlist(vlist, 0);
		
    if (vlist_stop == -1) {
		if (buildstructs_perm_alist(alist, 0) == -1) {
			return (0);
		}
    } else {
		if (buildstructs_is_useless_perm(head, vlist, alist, vlist_stop)) {
			buildstructs_new_perm(head, vlist, alist);
		}
    }

    return (1);
}

int buildstructs_perm_vlist (vlrlist vlist, int pos)
{
    if (pos == vlist->size) {
		return(-1);
    }
    /* push pos's cur up one */
    vlist->list[pos]->cur++;
    if (vlist->list[pos]->cur > vlist->list[pos]->max) {
		vlist->list[pos]->cur = vlist->list[pos]->min;
		return (buildstructs_perm_vlist(vlist, pos + 1));
    }
    return(pos);
}

int buildstructs_perm_alist (altlist alist, int pos)
{
    if (pos == alist->size) {
		return(-1);
    }
    alist->list[pos]->cur++;
    if (alist->list[pos]->cur == alist->list[pos]->max) {
		alist->list[pos]->cur = alist->list[pos]->min;
		return (buildstructs_perm_alist(alist, pos + 1));
    }
    return(pos);
}

int buildstructs_is_useless_perm (tnode head, vlrlist vlist, altlist alist, int vlist_stop)
{
    tnode node;
    int n = 0;
    int alt_id = 0;

    node = tnode_find_node_by_id(head, vlist->list[vlist_stop]->id);

    /* for each of that node's sub alternations */
    for (n = 0; n < silist_get_size(node->sub_alternations); n++) {
		/* check if that alternation is in corresponding position */
		alt_id = silist_get_element_n(node->sub_alternations, n);
		if (silist_get_element_n(node->sub_alt_positions, n) != alist->list[n]->cur) {
			return(1);
		}
    }

    return(0);
}
