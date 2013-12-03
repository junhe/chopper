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
** main.c
** A single node of the tree that must be built by parsing the regular
** expression.
** 4 July 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include "tnode.h"
#include "build_structs.h"
#include "char_set.h"
#include "data.h"
#include "parse_regex.h"
#include "program_args.h"
#include "altlist.h"
#include "grouplist.h"
#include "vlrlist.h"

/* Global glob g */
gg g;
int num_words_already_output = 0;

int main (int argc, char ** argv)
{
    /* Prepare storage structures */
    tnode head = tnode_constructor();
    vlrlist vlist = vlrlist_constructor();
    grouplist glist = grouplist_constructor();
    altlist alist = altlist_constructor();
    re_perm grammar = re_perm_constructor();
    
    g = data_constructor();

    tnode_set_id(head, g->tnodes);
    g->tnodes++;

    /* Parse program arugments */
    program_args_parse(argc, argv);

    /* Parse regular expression grammar */
    parse_regex(g->regex, head, PR_NOT_IN_GROUP);
    
    /* Stop if -p was given */
    if (g->stop_code == 'p') {
    	return (0);
    }
    
    /* Scan the tnode tree for varying lengths and groups */
    buildstructs_gvlists (head, glist, vlist, alist);

	/* Display the tree of regex elements -- for debugging */
    // tnode_display_tree(head);
    
    /* Begin building the dictionary */

    do {
		buildstructs_fill_perm (grammar, head, glist, vlist, alist);
		re_perm_generate_words(grammar);
		re_perm_free(grammar);
    } while (  ((g->num_words_output < 0) ||
    		   (num_words_already_output < g->num_words_output)) &&
    		 buildstructs_new_perm (head, vlist, alist));

    return (0);
}
