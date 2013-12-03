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
** parse_regex.h
** Functions for parsing the specified regex into a tnode tree.
** 10 July 2004
*/

#ifndef REGLDG_PARSE_REGEX_H
#define REGLDG_PARSE_REGEX_H

#include "char_set.h"
#include "data.h"
#include "tnode.h"

#define K_CHECK_CHARS 1
#define K_CHECK_CLASSES 2

#define K_NUM_DIGITS_IN_BRACED_QUANTIFIER_NUMBER 3
#define K_MAX_NUM_DIGITS_IN_BACKREFERENCE_NUMBER 3
#define K_ALLOW_RANGE_ENDPOINTS_IN_DIFFERENT_CLASSES 1

#define L_GENERAL 0
#define L_IN_CHAR_CLASS 1

#define PR_NOT_IN_GROUP 0
#define PR_IN_GROUP 1

void parse_regex (char_set, tnode, int);
void parse_regex_add_child_node(char_set, tnode);
void parse_regex_modify_last_child(tnode);
void parse_regex_print_group (char_set);
void parse_regex_print_char_class(char_set);
void parse_regex_print_range(char_set, int);
int parse_regex_scan (char_set, tnode, char *);
void parse_regex_pass_escape_sequence (char_set, int, tnode);
void parse_regex_pass_mcc (char_set);
void parse_regex_pass_metachar (char_set);
void parse_regex_pass_nsc (char_set);
void parse_regex_pass_backref (char_set);
void parse_regex_pass_positive_mcc (char_set, void (*)());
void parse_regex_pass_negative_mcc (char_set, void (*)());
void parse_regex_pass_universe_mcc (char_set);
void parse_regex_pass_nonuniverse_mcc (char_set);
void parse_regex_pass_dot_mcc (char_set );
void parse_regex_pass_alternation (char_set, tnode);
void parse_regex_pass_char_class (char_set, tnode);
int parse_regex_same_char_class(int, int);
char_type parse_regex_char_type (char_set, char);
void parse_regex_pass_quantifier (char_set);
void parse_regex_pass_braced_quantifier (char_set);
int parse_regex_pass_braced_quantifier_number (char_set);
int parse_regex_pass_universe_specifier(char_set);
void parse_regex_pass_backreference(char_set);
void parse_regex_pass_control_char(char_set);
int parse_regex_pass_decimal_char(char_set);
void parse_regex_pass_wide_hex_char(char_set);
int parse_regex_pass_hex_char (char_set);
int parse_regex_pass_octal_char(char_set);
void parse_regex_pass_char (char_set);
void parse_regex_pass_char_charclass(char_set, int);
int parse_regex_read_dec_val (char_set, int, int);
int parse_regex_pass_variable_length_number(char_set, const char *, const char *, int, int, int);
int parse_regex_pass_braced_number(char_set, const char *, const char *, int, int, int);
void parse_regex_print_c (char_set, int, const char *);
int parse_regex_ghetto_trunc(double);
void parse_regex_verify_meta_char(char_set);
void parse_regex_copy_chars(char_set, char_set, int, int);
#endif
