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
** tnode.h (Tree node for regldg)
** A single node of the tree that must be built by parsing the regular
** expression.
** 4 July 2004
*/

#ifndef REGLDG_TNODE_H
#define REGLDG_TNODE_H

#include "char_set.h"
#include "silist.h"

typedef enum {NodeType_General, NodeType_Leaf, NodeType_Group} node_type;
typedef enum {SplitType_General, SplitType_Alternation} split_type;

struct _tnode {
    int id;
    char_set chars;
    int length_max;
    int length_min;
    int group_id;
    int alternation_id;
    int backref_id;
    node_type nt;
    split_type st;
    void ** child_list;
    int num_children;
    silist sub_alternations;
    silist sub_alt_positions;
    silist sub_groups;
};
typedef struct _tnode regldg_tnode;
typedef struct _tnode *tnode;

/* Function prototypes */
tnode tnode_constructor            (void);

int   tnode_is_length_variable     (tnode);

void  tnode_set_max_length         (tnode, int);
int   tnode_get_max_length         (tnode);

void  tnode_set_min_length         (tnode, int);
int   tnode_get_min_length         (tnode);

void tnode_set_id (tnode, int);
int tnode_get_id (tnode);

void  tnode_set_group_id           (tnode, int);
int   tnode_get_group_id           (tnode);

void tnode_set_alternation_id (tnode, int);
int tnode_get_alternation_id (tnode);

void tnode_set_backref_id (tnode, int);
int tnode_get_backref_id (tnode);

void  tnode_set_node_type   (tnode, node_type);
node_type tnode_get_node_type   (tnode);

void  tnode_set_split_type   (tnode, split_type);
split_type tnode_get_split_type   (tnode);

void tnode_add_child (tnode, tnode);
tnode tnode_get_last_child (tnode);

char_set tnode_get_chars (tnode);

void tnode_display_tree (tnode);
void tnode_display_node (tnode);

silist tnode_get_alt_list (tnode);
void tnode_set_alt_list (tnode, silist);

silist tnode_get_alt_pos_list (tnode);
void tnode_set_alt_pos_list (tnode, silist);

silist tnode_get_group_list (tnode);
void tnode_set_group_list(tnode, silist);

tnode tnode_find_node_by_id (tnode, int);

#endif
