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
** data.c
** A single node of the tree that must be built by parsing the regular
** expression.
** 4 July 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "data.h"
#include "memory.h"
#include "silist.h"

gg data_constructor (void)
{
    /* set defaults */
    gg newgg = (gg) check_malloc (sizeof(global_glob));
    newgg->progname = NULL;
    newgg->max_word_length = 8;
    newgg->universe = char_set_g_constructor();
    newgg->regex = char_set_g_constructor();
    newgg->last_class = char_set_g_constructor();
    newgg->debug_code = 1;
    newgg->max_universe_num = ((int) pow(2, K_NUM_UNIVERSE_SETS)) - 1;
    newgg->num_alternation_strings = 0;
    newgg->num_groups_started = 0;
    newgg->num_groups_completed = 0;
    newgg->group_start_g_pos = silist_constructor();
    newgg->last_group_started = silist_constructor();
    newgg->finished_groups = silist_constructor();
    newgg->char_class_start = -1;
    newgg->num_char_classes_started = 0;
    newgg->last_chartype_parsed = CT_UNDEFINED;
    newgg->last_value_parsed = 0;
    newgg->last_value_parsed_extra = 0;
    newgg->parse_regex_mark = -1;
    newgg->current_atom_start_pos = 0;
    newgg->universe_check_code = 3;
    newgg->stop_code = '\0';
    newgg->num_words_output = -1;
    newgg->readable_output = 0;
    newgg->parsing_alt_list = silist_constructor();
    newgg->parsing_alt_pos_list = silist_constructor();
    newgg->tnodes = 0;

    /* Set the default universe to the letters A-Z, a-z, and numbers
    ** 0-9.
    ** Change the first number to the desired default universe
    ** number. The meanings of the numbers can be found inside
    ** the function being called. */
    char_set_g_add_universe(newgg->universe, 7);

    newgg->progname = NULL;

    return (newgg);
}

void data_somehow_copy (gg dest, gg src)
{
    silist_free(dest->group_start_g_pos);
    silist_free(dest->last_group_started);
    silist_free(dest->finished_groups);
    dest->num_groups_started = src->num_groups_started;
    dest->num_groups_completed = src->num_groups_completed;
    dest->group_start_g_pos = silist_copy_deep(src->group_start_g_pos);
    dest->last_group_started = silist_copy_deep(src->last_group_started);
    dest->finished_groups = silist_copy_deep(src->finished_groups);
    dest->num_char_classes_started = src->num_char_classes_started;
    dest->char_class_start = src->char_class_start;
    dest->last_chartype_parsed = src->last_chartype_parsed;
    dest->last_value_parsed = src->last_value_parsed;
    dest->last_value_parsed_extra = src->last_value_parsed_extra;
    dest->current_atom_start_pos = src->current_atom_start_pos;
}

void data_free (gg g)
{
    free(g->progname);
    char_set_g_free(g->universe);
    char_set_g_free(g->regex);
    silist_free(g->group_start_g_pos);
    free(g);
}
