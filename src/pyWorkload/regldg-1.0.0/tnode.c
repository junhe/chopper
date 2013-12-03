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
** tnode.c (Tree node for regldg)
** A single node of the tree that must be built by parsing the regular
** expression.
** 4 July 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "char_set.h"
#include "grouprecord.h"
#include "grouplist.h"
#include "vlr.h"
#include "vlrlist.h"
#include "tnode.h"
#include "memory.h"

tnode tnode_constructor (void)
/* allocate space and initialize values */
{
    tnode t = (tnode) check_malloc (sizeof(regldg_tnode));

    t->id = -1;
    t->chars = char_set_g_constructor();
    t->length_max = -1;
    t->length_min = -1;
    t->group_id = -1;
    t->alternation_id = -1;
    t->backref_id = -1;
    t->nt = NodeType_General;
    t->st = SplitType_General;
    t->child_list = (void **) check_malloc (sizeof(void *));
    ((tnode *)t->child_list)[0] = NULL;
    t->num_children = 0;
    t->sub_alternations = silist_constructor();
    t->sub_alt_positions = silist_constructor();
    t->sub_groups = silist_constructor();
    return (t);
}

int tnode_is_length_variable (tnode t)
/* If called after initialization, but before use, will return 0 = No */
{
    return (t->length_max == -1);
}

void tnode_set_max_length (tnode t, int i)
{
    t->length_max = i;
}

int tnode_get_max_length (tnode t)
{
    return (t->length_max);
}

void tnode_set_min_length (tnode t, int i)
{
    t->length_min = i;
}

int tnode_get_min_length (tnode t)
{
    return (t->length_min);
}

void tnode_set_id (tnode t, int i)
{
    t->id = i;
}

int tnode_get_id (tnode t)
{
    return (t->id);
}

void tnode_set_group_id (tnode t, int i)
{
    t->group_id = i;
}

int tnode_get_group_id (tnode t)
{
    return (t->group_id);
}

void tnode_set_alternation_id (tnode t, int i)
{
    t->alternation_id = i;
}

int tnode_get_alternation_id (tnode t)
{
    return (t->alternation_id);
}

void tnode_set_backref_id (tnode t, int n)
{
    t->backref_id = n;
}

int tnode_get_backref_id (tnode t)
{
    return (t->backref_id);
}

void tnode_set_node_type (tnode t, node_type nt)
{
    t->nt = nt;
}

node_type tnode_get_node_type (tnode t)
{
    return (t->nt);
}

void tnode_set_split_type (tnode t, split_type s)
{
    t->st = s;
}

split_type tnode_get_split_type (tnode t)
{
    return(t->st);
}

void tnode_add_child (tnode n, tnode child)
{
    n->num_children++;
    n->child_list = (void **) check_realloc (n->child_list, sizeof(void*) *( n->num_children + 1));
    ((tnode *)n->child_list)[n->num_children-1] = child;
    ((tnode *)n->child_list)[n->num_children] = NULL;
}

char_set tnode_get_chars (tnode n)
{
    return (n->chars);
}

tnode tnode_get_last_child (tnode n)
{
    if (n->num_children == 0) {
	fprintf(stderr, "tnode_get_last_child: No children in the node");
	exit(-40);
    }

    return (((tnode *)n->child_list)[n->num_children-1]);
}

void tnode_display_tree (tnode n)
{
    tnode * nptr = (tnode *) n->child_list;
    tnode_display_node(n);
    while (*nptr) {
	tnode_display_tree(*nptr);
	nptr++;
    }
}

void tnode_display_node (tnode n)
{
    int c;
    printf("id: %d\n", n->id);
    printf("chars: ");
    for (c = 0; c < char_set_g_size(n->chars); c++) {
	printf("%c", char_set_g_char_n(n->chars, c));
    }
    printf("\n");
    printf("length_min: %d\n", n->length_min);
    printf("length_max: %d\n", n->length_max);
    printf("group_id: %d\n", n->group_id);
    printf("alternation_id: %d\n", n->alternation_id);
    printf("sub_alternations:\n");
    silist_display(n->sub_alternations);
    printf("sub_alt_positions:\n");
    silist_display(n->sub_alt_positions);
    printf("contained in groups:\n");
    silist_display(n->sub_groups);
    printf("backref_id: %d\n", n->backref_id);
    if (n->nt == NodeType_General) {
	printf("node_type: General\n");
    } else if (n->nt == NodeType_Leaf) {
	printf("node_type: Leaf\n");
    } else {
	printf("node_type: Group\n");
    }
    if (n->st == SplitType_General) {
	printf("split_type: General\n");
    } else {
	printf("split_type: Alternation\n");
    }
    printf("num_children: %d\n", n->num_children);
    printf("*****\n");
}

silist tnode_get_alt_list (tnode node)
{
    return (node->sub_alternations);
}

void tnode_set_alt_list (tnode node, silist s)
{
    node->sub_alternations = s;
}

silist tnode_get_alt_pos_list(tnode node)
{
    return (node->sub_alt_positions);
}

void tnode_set_alt_pos_list(tnode node, silist s)
{
    node->sub_alt_positions = s;
}

silist tnode_get_group_list (tnode node)
{
    return (node->sub_groups);
}

void tnode_set_group_list(tnode node, silist s)
{
    node->sub_groups = s;
}

tnode tnode_find_node_by_id (tnode node, int i)
{
    tnode try;
    tnode * nptr = (tnode *) node->child_list;

    if (node->id == i) {
	return(node);
    } else {
	while (*nptr) {
	    try = tnode_find_node_by_id(*nptr, i);
	    if (try) {
		return(try);
	    } else {
		nptr++;
	    }
	}
	return(NULL);
    }
}
