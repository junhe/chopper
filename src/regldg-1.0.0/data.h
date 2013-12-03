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
** data.h
** A single node of the tree that must be built by parsing the regular
** expression.
** 4 July 2004
*/

#ifndef REGLDG_DATA_H
#define REGLDG_DATA_H

#include "char_set.h"
#include "silist.h"

typedef enum { CT_UNDEFINED, CT_CHAR, CT_ESCAPE_SEQUENCE, CT_NSC, CT_MCC, CT_BACKREF, CT_GROUP_START, CT_GROUP_FINISH, CT_QUANTIFIER, CT_BRACED_QUANTIFIER_START, CT_BRACED_QUANTIFIER_FINISH, CT_CHAR_CLASS_START, CT_CHAR_CLASS_FINISH, CT_ALTERNATION, CT_RANGE, CT_RANGE_END, CT_CONTROL, CT_NEGATE_CHAR_CLASS, CT_METACHAR } char_type;

struct _global_glob {
    char * progname;
    int max_word_length;
    char_set universe;
    char_set regex;
    char_set last_class;
    int debug_code;
    int max_universe_num;
    int num_alternation_strings;
    int num_groups_started;
    int num_groups_completed;
    silist group_start_g_pos;
    silist last_group_started;
    silist finished_groups;
    int num_char_classes_started;
    int char_class_start;
    char_type last_chartype_parsed;
    int last_value_parsed;
    int last_value_parsed_extra;
    int parse_regex_mark;
    int current_atom_start_pos;
    int universe_check_code;
    char stop_code;
    int num_words_output;
    int readable_output;
    int tnodes;
    silist parsing_alt_list;
    silist parsing_alt_pos_list;
};
typedef struct _global_glob global_glob;
typedef struct _global_glob *gg;

gg data_constructor (void);
void data_somehow_copy (gg, gg);
void data_free (gg);

#endif
