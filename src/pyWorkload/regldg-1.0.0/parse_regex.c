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
** parse_regex.c
** Functions for parsing the specified regex into a tnode tree.
** 10 July 2004
*/

/* Parsing a regex
** Do the following:
** 1. Scan the string for alternations in the top level.  If one
**    is found, then cut the string into two parts as child nodes,
**    and start parsing from step 1 on each of the child nodes.
** 2. Scan the string for characters, meta-characters, character
**    classes, and groups.  A child from this node class (#2) will
**    be a character, a meta-character, a character class, or a
**    group.  The child may have a quantifier following it.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include "data.h"
#include "debug.h"
#include "memory.h"
#include "parse_regex.h"
#include "silist.h"
#include "tnode.h"

extern gg g;

void parse_regex (char_set regex, tnode t, int group_flag) {

    tnode child;
    int alt_count = 0;
    char find_alternation_string[] = "|)";
    char parsing_string[] = ")";
    gg status_vars = data_constructor();
    int pos = char_set_g_get_pos(regex);
    int perm_pos = pos;

    if (!group_flag) {
	find_alternation_string[1] = '\0';
	parsing_string[0] = '\0';
    }

    data_somehow_copy(status_vars, g);

    if ((parse_regex_scan(regex, NULL, find_alternation_string) == 1) &&
	(char_set_p_char_n(regex, 0) == '|'))
    {
	if (t) {
	    tnode_set_split_type(t, SplitType_Alternation);
	    tnode_set_alternation_id(t, g->num_alternation_strings);
	    silist_insert(g->parsing_alt_list, g->num_alternation_strings);
	    g->num_alternation_strings++;
	}
	do {
	    data_somehow_copy(g, status_vars);
	    if (t) {
		silist_insert(g->parsing_alt_pos_list, alt_count);
		alt_count++;
		child = tnode_constructor();
		tnode_set_id(child, g->tnodes);
		g->tnodes++;
		parse_regex_copy_chars(tnode_get_chars(child), regex, pos, char_set_g_get_pos(regex) - pos);
		char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
		tnode_set_node_type(child, NodeType_General);
		silist_free(tnode_get_alt_list(child));
		tnode_set_alt_list(child, silist_copy_deep(g->parsing_alt_list));
		silist_free(tnode_get_alt_pos_list(child));
		tnode_set_alt_pos_list(child, silist_copy_deep(g->parsing_alt_pos_list));
		silist_free(tnode_get_group_list(child));
		tnode_set_group_list(child, silist_copy_deep(g->last_group_started));
		tnode_add_child(t, child);
		parse_regex_scan(regex, child, find_alternation_string);
		silist_remove_last(g->parsing_alt_pos_list);
	    } else {
		char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
		parse_regex_scan(regex, NULL, find_alternation_string);
	    }
	    parse_regex_pass_alternation(regex, t);
	    pos = char_set_g_get_pos(regex);
	    data_somehow_copy(status_vars, g);
	} while ((parse_regex_scan(regex, NULL, find_alternation_string) == 1) &&
		 (char_set_p_char_n(regex, 0) == '|'));
	/* Last time */
	data_somehow_copy(g, status_vars);
	if (t) {
	    silist_insert(g->parsing_alt_pos_list, alt_count);
	    alt_count++;
	    child = tnode_constructor();
	    tnode_set_id(child, g->tnodes);
	    g->tnodes++;
	    parse_regex_copy_chars(tnode_get_chars(child), regex, pos, char_set_g_get_pos(regex) - pos);
	    char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
	    tnode_set_node_type(child, NodeType_General);
	    silist_free(tnode_get_alt_list(child));
	    tnode_set_alt_list(child, silist_copy_deep(g->parsing_alt_list));
	    silist_free(tnode_get_alt_pos_list(child));
	    tnode_set_alt_pos_list(child, silist_copy_deep(g->parsing_alt_pos_list));
	    silist_free(tnode_get_group_list(child));
	    tnode_set_group_list(child, silist_copy_deep(g->last_group_started));
	    tnode_add_child(t, child);
	    parse_regex_scan(regex, child, parsing_string);
	    silist_remove_last(g->parsing_alt_pos_list);
	    silist_remove_last(g->parsing_alt_list);
	    /* fill the alternation node with the chars */
	    parse_regex_copy_chars(tnode_get_chars(t), regex, perm_pos, char_set_g_get_pos(regex) - perm_pos);
	} else {
	    char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
	    parse_regex_scan(regex, NULL, parsing_string);
	}
    } else {
	data_somehow_copy(g, status_vars);
	if (t) {
	    parse_regex_copy_chars(tnode_get_chars(t), regex, pos, char_set_g_get_pos(regex) - pos);
	    char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
	    parse_regex_scan(regex, t, parsing_string);
	} else {
	    char_set_g_adv_pos(regex, pos - char_set_g_get_pos(regex));
	    parse_regex_scan(regex, NULL, parsing_string);
	}
    }
}

void parse_regex_copy_chars(char_set dest, char_set src, int start_pos, int num_bytes)
/* this function does no error checking */
{
    int i = start_pos;
    
    while (i < num_bytes + start_pos) {
	char_set_g_insert_char(dest, char_set_g_char_n(src, i));
	i++;
    }
}

int parse_regex_scan (char_set c, tnode node, char * top_stop_chars)
{
    tnode child;
    int chars_read = 0;
    char * buf;
    int bufsize = 0;

    char_set_p_assert_usability(c, "parse_regex_scan_for_errors", "Premature end of regex!");

    while (char_set_g_get_pos(c) < char_set_g_size(c)) {
		/* ending group return */
		if ( (index(top_stop_chars, ')') != NULL) &&
			 (char_set_p_char_n(c, 0) == ')') )
		{
			if (chars_read == 0) {
			char_set_g_adv_pos(c, 1);
			parse_regex_print_c(c, D_Error, "parse_regex_scan: empty group");
			exit(-16);
			}
			g->last_chartype_parsed = CT_GROUP_FINISH;
			return (1);
		} 
		/* topstring stop char return */
		else if (index(top_stop_chars, char_set_p_char_n(c, 0)) != NULL)
		{
			return (1);
		}
		g->current_atom_start_pos = char_set_g_get_pos(c);
		switch (char_set_p_char_n(c, 0)) {
		case '\\': /* na! */
			char_set_g_adv_pos(c, 1);
			parse_regex_pass_escape_sequence(c, L_GENERAL, node);
			if (node) {
				parse_regex_add_child_node(c, node);
			}
			chars_read++;
			break;
		case '(': /* !na */
			g->num_groups_started++;
			silist_insert(g->group_start_g_pos, char_set_g_offset(c) + char_set_g_get_pos(c));
			silist_insert(g->last_group_started, g->num_groups_started);
			g->last_chartype_parsed = CT_GROUP_START;
			char_set_g_adv_pos(c, 1);
			if (node) {
				bufsize = 14 + ((int) log10(g->num_groups_started)) + 1 + 1;
				buf = (char *) check_malloc (sizeof(char) * bufsize);
				sprintf(buf, "Started group %d", g->num_groups_started);
				buf[bufsize-1] = '\0';
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
				free(buf);
				child = tnode_constructor();
				tnode_set_id(child, g->tnodes);
				g->tnodes++;
				tnode_set_node_type(child, NodeType_Group);
				tnode_set_group_id(child, g->num_groups_started-1);
				tnode_set_min_length(child, 1);
				tnode_set_max_length(child, 0);
				silist_free(tnode_get_group_list(child));
				tnode_set_group_list(child, silist_copy_deep(g->last_group_started));
				tnode_add_child(node, child);
				parse_regex(c, child, PR_IN_GROUP);
			} else {
				parse_regex(c, NULL, PR_IN_GROUP);
			}
	
			// pop the last element in last_group_started, 
			// and push it onto finished groups
			silist_insert(g->finished_groups, silist_get_element_n(g->last_group_started, silist_get_size(g->last_group_started) - 1));
			silist_remove_last(g->last_group_started);
	
			g->num_groups_completed++;
			char_set_g_adv_pos(c, 1);
			if (node) {
				parse_regex_print_group(c);
			}
			g->last_chartype_parsed = CT_GROUP_FINISH;
			chars_read++;
			break;
		case '*': /* !na */
		case '+':
		case '?':
		case '{':
			parse_regex_pass_quantifier(c);
			if (node) {
				parse_regex_modify_last_child(node);
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed quantifier");
			}
			break;
		case '[': /* !na */
			g->num_char_classes_started++;
			g->char_class_start = char_set_g_get_pos(c) + char_set_g_offset(c);
			char_set_g_adv_pos(c, 1);
			if (node) {
				bufsize = 24 + ((int) log10(g->num_char_classes_started)) + 1 + 1;
				buf = (char *) check_malloc (sizeof(char) * bufsize);
				sprintf(buf, "Started character class %d", g->num_char_classes_started);
				buf[bufsize-1] = '\0';
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
				free(buf);
			}
			parse_regex_pass_char_class(c, node);
			if (node) {
				parse_regex_add_child_node(c, node);
				parse_regex_print_char_class(c);
			}
			chars_read++;
			break;
		case '.': /* !na */
			parse_regex_pass_mcc(c);
			if (node) {
				parse_regex_add_child_node(c, node);
			}
			chars_read++;
			break;
		case '|':
			parse_regex_pass_alternation(c, node);
			//debug_print(D_Error, "should we be here in alternation?");
			break;
		case ']': /* !na */
			parse_regex_print_c(c, D_Error, "parse_regex_scan_for_errors: unmatched ] in regex!");
			exit(-13);
			break;
		case ')': /* !na */
			parse_regex_print_c(c, D_Error, "parse_regex_scan_for_errors: unmatched ) in regex!");
			exit(-13);
			break;
		case '}': /* !na */
			parse_regex_print_c(c, D_Error, "parse_regex_scan_for_errors: unmatched } in regex!");
			exit(-13);
			break;
		default: /* !na */
			parse_regex_pass_char(c);
			if (node) {
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above character");
				parse_regex_add_child_node(c, node);
			}
			chars_read++;
			break;
		}
    }

    if (g->num_groups_completed != g->num_groups_started) {
		parse_regex_print_c(c, D_Error, "parse_regex_scan_for_errors: premature end of group!");
		exit(-13);
    }
    return (0);
}

void parse_regex_modify_last_child(tnode node)
{
    tnode child = tnode_get_last_child(node);
    tnode_set_min_length(child, g->last_value_parsed);
    tnode_set_max_length(child, g->last_value_parsed_extra);
}

void parse_regex_add_child_node (char_set c, tnode node)
{
    char_set cs1, cs2;
    tnode child = tnode_constructor();
    tnode_set_id(child, g->tnodes);
    g->tnodes++;
    silist_free(tnode_get_alt_list(child));
    tnode_set_alt_list(child, silist_copy_deep(g->parsing_alt_list));
    silist_free(tnode_get_group_list(child));
    tnode_set_group_list(child, silist_copy_deep(tnode_get_group_list(node)));

    switch(g->last_chartype_parsed) {
	case CT_CHAR:
	case CT_METACHAR:
	case CT_NSC:
	case CT_CONTROL:
	    char_set_g_add_char(tnode_get_chars(child), g->last_value_parsed);
	    tnode_set_node_type(child, NodeType_Leaf);
	    tnode_set_min_length(child, 1);
	    tnode_set_max_length(child, 0);
	    tnode_add_child(node, child);
	    break;
	case CT_MCC:
	    cs1 = char_set_g_constructor();
	    cs2 = char_set_g_constructor();
	    switch (g->last_value_parsed) {
		case 'w': case 's': case 'd': case 'u': case '.':
		case 'W': case 'S': case 'D': case 'U':
		    char_set_g_deep_copy(tnode_get_chars(child), g->last_class);
		    tnode_set_node_type(child, NodeType_Leaf);
		    tnode_set_min_length(child, 1);
		    tnode_set_max_length(child, 0);
		    tnode_add_child(node, child);
		    parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed metacharacter class");
		    if (g->debug_code & D_Parse_Regex_Eachstep) {
			debug_print(D_Parse_Regex_Eachstep, "Metacharacter class contains:");
			char_set_g_display(g->last_class);
		    }
		    break;
		default:
		    debug_print(D_Error, "parse_regex_add_child_node: unknown metacharacter set");
		    exit(-31);
		    break;
	    }
/*	    if (g->universe_check_code & K_CHECK_CHARS) {
		char_set_g_free(cs2);
		cs2 = char_set_g_create_intersection(cs1, g->universe);
		char_set_g_union_char_set(tnode_get_chars(child), cs2);
	    } else {
		char_set_g_union_char_set(tnode_get_chars(child), cs1);
	    }
	    tnode_set_node_type(child, NodeType_Leaf);
	    tnode_set_min_length(child, 1);
	    tnode_set_max_length(child, 0);
	    tnode_add_child(node, child); */
	    char_set_g_free(cs1);
	    char_set_g_free(cs2);
	    break;
	case CT_CHAR_CLASS_FINISH:
	    char_set_g_deep_copy(tnode_get_chars(child), g->last_class);
	    tnode_set_node_type(child, NodeType_Leaf);
	    tnode_set_min_length(child, 1);
	    tnode_set_max_length(child, 0);
	    tnode_add_child(node, child);
	    break;
	case CT_BACKREF:
	    tnode_set_node_type(child, NodeType_Leaf);
	    tnode_set_backref_id(child, g->last_value_parsed);
	    tnode_set_min_length(child, 1);
	    tnode_set_max_length(child, 0);
	    parse_regex_copy_chars(tnode_get_chars(child), c, g->current_atom_start_pos, char_set_g_get_pos(c) - g->current_atom_start_pos);
	    /* set the size and type information */
	    tnode_add_child(node, child);
	    parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed backreference");
	    break;
	default:
	    debug_print(D_Error, "parse_regex_add_child_node: unknown last character type");
	    exit(-31);
	    break;
    }
}

void parse_regex_print_group (char_set c)
{
    char * buf;
    int bufsize = 0;
    int group_id = silist_get_element_n(g->finished_groups, silist_get_size(g->finished_groups) - 1);
    int saved = g->current_atom_start_pos;

    bufsize = 14 + ((int) log10(g->num_groups_started - (g->num_groups_completed - 1))) + 1 + 1;
    buf = (char *) check_malloc (sizeof(char) * bufsize);
    sprintf(buf, "Parsed group %d", group_id);
    buf[bufsize-1] = '\0';
    g->current_atom_start_pos = silist_get_element_n(g->group_start_g_pos, group_id - 1);
    parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
    g->current_atom_start_pos = saved;
    free(buf);
}

void parse_regex_pass_alternation (char_set c, tnode node)
{
    /* Can we really put an alternation here? */

    /* 1. check the character type before now */
    switch (g->last_chartype_parsed) {
	case CT_CHAR:
	case CT_NSC:
	case CT_MCC:
	case CT_BACKREF:
	case CT_GROUP_FINISH:
	case CT_QUANTIFIER:
	case CT_BRACED_QUANTIFIER_FINISH:
	case CT_CONTROL:
	case CT_METACHAR:
	case CT_CHAR_CLASS_FINISH:
	    /* these above character types are OK */
	    break;
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_alternation: character type preceeding alternation is invalid");
	    exit(-35);
	    break;
    }

    g->current_atom_start_pos = char_set_g_get_pos(c);
    char_set_g_adv_pos(c, 1);

    g->last_chartype_parsed = CT_ALTERNATION;
    
    if (node) {
		parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed alternation");
	}
}

void parse_regex_pass_escape_sequence (char_set c, int in_char_class, tnode node)
{
    char_set_p_assert_usability(c, "parse_regex_pass_escape sequence", "Premature end of escape sequence");

    if (in_char_class) {
	switch(char_set_p_char_n(c, 0)) {
	    case '(': case '*': case '+': case '?': case '{':
	    case '[': case '|': case ')': case '}':
		/* these characters should not be escaped for a character class */
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: unnecessary escape in character class");
		exit(-38);
		break;
	    case '^': case '-': case ']': case '\\': case '.':
		/* these are just regular characters */
		parse_regex_pass_char(c);
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above escaped character");
		}
		break;
	    case 't': case 'n': case 'r': case 'f': case 'a':
	    case 'e': case 'b': case 'v':
		/* these are metacharacters */
		parse_regex_pass_metachar(c);
		if (node != NULL) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above metacharacter");
		}
		break;
	    case 'o': case 'z': case 'x':
		/* these are Numerically Specified Characters */
		parse_regex_pass_nsc(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above numerically-specified character");
		}
		break;
	    case 'w': case 'W': case 's': case 'S': case 'd':
	    case 'D': case 'u': case 'U':
		/* these are MetaCharacter Classes */
		parse_regex_pass_mcc(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above metacharacter class");
		}
		break;
	    case '1': case '2': case '3': case '4': case '5':
	    case '6': case '7': case '8': case '9': case '!':
		/* these are attempted backreferences */
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: backreferences are not allowed in character classes");
		exit(-31);
		break;
	    case 'c':
		/* it is a control character */
		char_set_g_adv_pos(c, 1);
		parse_regex_pass_control_char(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above control-character");
		}
		break;
	    case '0':
		/* somebody is trying to specify an octal character in a
		** depricated manner */
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: invalid esacpe sequence.\nIf you want to specify an octal character, use \\o (\\ - letter \"o\"");
		exit(-31);
		break;
	    default:
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: unknown escape sequence in character class");
		exit(-31);
		break;
	}
    } else {
	switch (char_set_p_char_n(c, 0)) {
	    case '|': case '\\': case '*': case '?': case '+':
	    case '.': case '(': case ')': case '[': case ']':
	    case '{': case '}':
		/* these are just regular characters */
		parse_regex_pass_char(c);  /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above escaped character");
		}
		break;
	    case 't': case 'n': case 'r': case 'f': case 'a':
	    case 'e': case 'b': case 'v':
		/* these are metacharacters */
		parse_regex_pass_metachar(c);
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above metacharacter");
		}
		break;
	    case 'o': case 'z': case 'x':
		/* these are Numerically Specified Characters */
		parse_regex_pass_nsc(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above numerically-specified character");
		}
		break;
	    case 'w': case 'W': case 's': case 'S': case 'd':
	    case 'D': case 'u': case 'U':
		/* these are MetaCharacter Classes */
		parse_regex_pass_mcc(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above metacharacter class");
		}
		break;
	    case '1': case '2': case '3': case '4': case '5':
	    case '6': case '7': case '8': case '9': case '!':
		/* these are for backreferences */
		parse_regex_pass_backref(c); /* !Na */
		break;
	    case 'c':
		/* it is a control character */
		char_set_g_adv_pos(c, 1);
		parse_regex_pass_control_char(c); /* !Na */
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above contorl-character");
		}
		break;
	    case '0':
		/* somebody is trying to specify an octal character in a
		** depricated manner */
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: invalid esacpe sequence.\nIf you want to specify an octal character, use \\o (\\ - letter \"o\"");
		exit(-31);
		break;
	    default:
		/* Unknown escape sequence */
		char_set_g_adv_pos(c,1);
		parse_regex_print_c(c, D_Error, "parse_regex_pass_escape_sequence: invalid esacpe sequence.");
		exit(-31);
		break;
	}
    }
}

void parse_regex_pass_metachar (char_set c)
{
    char_set_p_assert_usability(c, "parse_regex_pass_metachar", "Premature end of metachar");
    
    switch (char_set_p_char_n(c, 0)) {
	case 'a': /* alarm / bell */
	    g->last_value_parsed = 7;
	    break;
	case 'b': /* backspace */
	    g->last_value_parsed = 8;
	    break;
	case 't': /* horizontal tab */
	    g->last_value_parsed = 9;
	    break;
	case 'n': /* newline / line feed */
	    g->last_value_parsed = 10;
	    break;
	case 'v': /* vertical tab */
	    g->last_value_parsed = 11;
	    break;
	case 'f': /* form feed */
	    g->last_value_parsed = 12;
	    break;
	case 'r': /* carriage return */
	    g->last_value_parsed = 13;
	    break;
	case 'e': /* escape */
	    g->last_value_parsed = 27;
	    break;
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_metachar: unknown metacharacter");
	    break;
    }

    if ( (g->universe_check_code & K_CHECK_CHARS) &&
	 (char_set_g_index(g->universe, g->last_value_parsed) == -1) )
    {
    char_set_g_adv_pos(c,1);
	parse_regex_print_c(c, D_Error, "parse_regex_pass_metachar: metacharacter is not in the current universe");
	exit(-36);
    }

    g->last_chartype_parsed = CT_METACHAR;
    char_set_g_adv_pos(c, 1);
}

void parse_regex_pass_mcc (char_set c)
{
    switch (char_set_p_char_n(c, 0)) {
	case 'w':
	    parse_regex_pass_positive_mcc(c, char_set_g_add_word_mcc);
	    g->last_value_parsed = 'w';
	    break;
	case 'W':
	    parse_regex_pass_negative_mcc(c, char_set_g_add_word_mcc);
	    g->last_value_parsed = 'W';
	    break;
	case 's':
	    parse_regex_pass_positive_mcc(c, char_set_g_add_space_mcc);
	    g->last_value_parsed = 's';
	    break;
	case 'S':
	    parse_regex_pass_negative_mcc(c, char_set_g_add_space_mcc);
	    g->last_value_parsed = 'S';
	    break;
	case 'd':
	    parse_regex_pass_positive_mcc(c, char_set_g_add_digit_mcc);
	    g->last_value_parsed = 'd';
	    break;
	case 'D':
	    parse_regex_pass_negative_mcc(c, char_set_g_add_digit_mcc);
	    g->last_value_parsed = 'D';
	    break;
	case 'u':
	    char_set_g_adv_pos(c, 1);
	    parse_regex_pass_universe_mcc(c);
	    g->last_value_parsed = 'u';
	    /* last_value_parsed_extra is set in the called function */
	    break;
	case 'U':
	    char_set_g_adv_pos(c, 1);
	    parse_regex_pass_nonuniverse_mcc(c);
	    g->last_value_parsed = 'U';
	    /* last_value_parsed_extra is set in the called function */
	    break;
	case '.':
	    parse_regex_pass_dot_mcc(c);
	    g->last_value_parsed = '.';
	    break;
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_mcc: unknown metacharacter class");
	    exit(-32);
	    break;
    }
    g->last_chartype_parsed = CT_MCC;
}

void parse_regex_pass_positive_mcc (char_set c, void (*add_mcc)())
{
    char_set cs1, cs2;

    cs1 = char_set_g_constructor();
    add_mcc(cs1);

    if (g->universe_check_code & K_CHECK_CLASSES) {
		cs2 = char_set_g_create_intersection(g->universe, cs1);
		if (char_set_g_size(cs2) == 0) {
			char_set_g_adv_pos(c, 1);
			parse_regex_print_c(c, D_Error, "parse_regex_pass_positive_mcc: metacharacter class is empty in this universe");
			exit(-33);
		}
		char_set_g_deep_copy(g->last_class, cs2);
		char_set_g_free(cs2);
    } else {
		char_set_g_deep_copy(g->last_class, cs1);
    }
    char_set_g_free(cs1);
    char_set_g_adv_pos(c, 1);
}

void parse_regex_pass_negative_mcc (char_set c, void (*add_func)())
{
    char_set cs1, cs2;

    cs1 = char_set_g_constructor();
    add_func(cs1);
    cs2 = char_set_g_create_complement(cs1);
    char_set_g_free(cs1);

    if (g->universe_check_code & K_CHECK_CLASSES) {
	cs1 = char_set_g_create_intersection(g->universe, cs2);
	if (char_set_g_size(cs1) == 0) {
	    char_set_g_adv_pos(c, 1);
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_negative_mcc: nonword metacharacter class is empty in this universe");
	    exit(-33);
	}
	char_set_g_deep_copy(g->last_class, cs1);
	char_set_g_free(cs1);
    } else {
	char_set_g_deep_copy(g->last_class, cs2);
    }
    char_set_g_free(cs2);
    char_set_g_adv_pos(c, 1);
}

void parse_regex_pass_universe_mcc (char_set c)
{
    char_set cs1, cs2;
    int val;

    val = parse_regex_pass_universe_specifier(c); /* !na */

    cs1 = char_set_g_constructor();
    char_set_g_add_universe(cs1, val); /* !na */

    if (g->universe_check_code & K_CHECK_CLASSES) {
	cs2 = char_set_g_create_intersection(g->universe, cs1);
	if (char_set_g_size(cs2) == 0) {
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_universe_mcc: previous universe metacharacter class is empty in this universe");
	    exit(-33);
	}
	char_set_g_deep_copy(g->last_class, cs2);
	char_set_g_free(cs2);
    } else {
	char_set_g_deep_copy(g->last_class, cs1);
    }
    char_set_g_free(cs1);
    g->last_value_parsed_extra = val;
}

void parse_regex_pass_nonuniverse_mcc (char_set c)
{
    char_set cs1, cs2;
    int val;

    val = parse_regex_pass_universe_specifier(c); /* !na */

    cs1 = char_set_g_constructor();
    char_set_g_add_universe(cs1, val); /* !na */
    cs2 = char_set_g_create_complement(cs1);
    char_set_g_free(cs1);

    if (g->universe_check_code & K_CHECK_CLASSES) {
	cs1 = char_set_g_create_intersection(g->universe, cs2);
	if (char_set_g_size(cs1) == 0) {
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_nonuniverse_mcc: nonuniverse metacharacter class is empty in this universe");
	    exit(-33);
	}
	char_set_g_deep_copy(g->last_class, cs1);
	char_set_g_free(cs1);
    } else {
	char_set_g_deep_copy(g->last_class, cs2);
    }

    char_set_g_free(cs2);

    g->last_value_parsed_extra = val;
}

void parse_regex_pass_dot_mcc (char_set c)
{
    char_set cs, cs2;

    cs = char_set_g_constructor();
    char_set_g_add_all_chars(cs);
    if (g->universe_check_code & K_CHECK_CLASSES) {
	cs2 = char_set_g_create_intersection(g->universe, cs);
	if (char_set_g_size(cs2) == 0) {
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_word_mcc: dot metacharacter class is empty in this universe");
	    exit(-33);
	}
	char_set_g_deep_copy(g->last_class, cs2);
	char_set_g_free(cs2);
    } else {
	char_set_g_deep_copy(g->last_class, cs);
    }
    char_set_g_free(cs);

    char_set_g_adv_pos(c, 1);
}

void parse_regex_pass_char_class (char_set c, tnode node)
{
    int range_flag = 0;
    int range_start = 0;
    int range_start_pos = 0;
    int range_char = 0;
    int temp_adj = 0;
    char_set cs, cs2, cs3;
    int negate_char_class = 0;
    int num_chars = 0;
    int saved_ucl = g->universe_check_code;
    
    cs = char_set_g_constructor();

    char_set_p_assert_usability(c, "parse_regex_pass_char_class", "Premature end of character class");

	g->current_atom_start_pos = char_set_g_get_pos(c);
	
    /* The ^ has a special meaning if it is the first character of the class */
    if (char_set_p_char_n(c, 0) == '^') {
		g->last_chartype_parsed = CT_NEGATE_CHAR_CLASS;
		negate_char_class = 1;
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed character class negation");
		}
		/* we need to turn off character and class checking while we are
		** in a negated character class */
		g->universe_check_code = 0;
		char_set_g_adv_pos(c, 1);
		g->current_atom_start_pos = char_set_g_get_pos(c);
		char_set_p_assert_usability(c, "parse_regex_pass_char_class", "Premature end of character class");
    }

    if (char_set_p_char_n(c, 0) == '-') {
		/* The - char is to be treated like a real character in the class */
		parse_regex_pass_char(c);
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above character");
		}
		char_set_g_add_char(cs, '-');
		num_chars++;
		g->current_atom_start_pos = char_set_g_get_pos(c);
		char_set_p_assert_usability(c, "parse_regex_pass_char_class", "Premature end of character class");
    } else if (char_set_p_char_n(c, 0) == ']') {
		/* the ] char is to be treated like a real character in the class */
		parse_regex_pass_char(c);
		if (node) {
			parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above character");
		}
		char_set_g_add_char(cs, ']');
		num_chars++;
		g->current_atom_start_pos = char_set_g_get_pos(c);
		char_set_p_assert_usability(c, "parse_regex_pass_char_class", "Premature end of character class");
    }

    while (char_set_p_char_n(c, 0) != ']') {
		switch(char_set_p_char_n(c, 0)) {
		case '.':
			if (range_flag) {
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: invalid range end character");
				exit (-37);
			}
			parse_regex_pass_mcc(c);
			if (node) {
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above dot metacharacter class");
			}
			num_chars++;
			char_set_g_add_all_chars(cs);
			break;
		case '\\': /* na! */
			//g->current_atom_start_pos = char_set_g_get_pos(c);
			//g->parse_regex_mark = char_set_g_get_pos(c) + char_set_g_offset(c);
			if (! range_flag) {
				//range_start_pos = g->parse_regex_mark;
				range_start_pos = g->current_atom_start_pos;
			}
			char_set_g_adv_pos(c, 1);
			parse_regex_pass_escape_sequence(c, L_IN_CHAR_CLASS, node);
			switch(g->last_chartype_parsed) {
			case CT_RANGE_END:
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: Compound ranges are not allowed");
				exit(-31);
				break;
			case CT_CHAR:
			case CT_METACHAR:
			case CT_NSC:
			case CT_CONTROL:
				if (range_flag) {
					if ( (K_ALLOW_RANGE_ENDPOINTS_IN_DIFFERENT_CLASSES) ||
						 (parse_regex_same_char_class(range_start, g->last_value_parsed)))
					{
						if (node) {
							parse_regex_print_range(c, range_start_pos);
						}
						char_set_g_add_range(cs, range_start, g->last_value_parsed);
						g->last_chartype_parsed = CT_RANGE_END;
						range_flag = 0;
					} else {
						parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: Range start and end characters are not in the same class.  The use of this is dangerous and deprecated.");
						exit(-31);
					}
				} else {
					char_set_g_add_char(cs, g->last_value_parsed);
				}
				break;
			case CT_MCC:
				if (range_flag) {
					/* the endpoint of this regex is not a valid range
					** endpoint.  So, let's just make the - a character
					** in the class, as well as the mcc */
	
					/* do a pseudo pass of the '-' */
					if ( (!negate_char_class) && 
					 (g->universe_check_code & K_CHECK_CHARS) &&
					 (char_set_g_index(g->universe, '-') == -1))
					{
					temp_adj = range_char - (char_set_g_offset(c) + char_set_g_get_pos(c)) + 1;
					char_set_g_adv_pos(c, temp_adj);
					g->current_atom_start_pos = range_char;
					parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: '-' understood as a regular character, and is not in the universe");
					exit(-31);
					}
					if (node) {
						temp_adj = range_char - (char_set_g_offset(c) + char_set_g_get_pos(c)) + 1;
						char_set_g_adv_pos(c, temp_adj);
						g->current_atom_start_pos = range_char;
						parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above - as a character, not a range");
						char_set_g_adv_pos(c, 0 - temp_adj);
						g->current_atom_start_pos += 1;
					}
					char_set_g_add_char(cs, '-');
					num_chars++;
					range_flag = 0;
					
					/* the following will be used if we don't want
					** to allow a - char with invalid endpoints */
					/* parse_regex_print_c(D_Error, "parse_regex_pass_char_class: invalid range end character");
					   exit (-37); */
					}
					switch (g->last_value_parsed) {
					case 'w':
						char_set_g_add_word_mcc(cs);
						break;
					case 's':
						char_set_g_add_space_mcc(cs);
						break;
					case 'd':
						char_set_g_add_digit_mcc(cs);
						break;
					case 'u':
						char_set_g_add_universe(cs, g->last_value_parsed_extra);
						break;
					case '.':
						char_set_g_add_all_chars(cs);
						break;
					case 'W':
						cs2 = char_set_g_constructor();
						char_set_g_add_word_mcc(cs2);
						cs3 = char_set_g_create_complement(cs2);
						char_set_g_union_char_set(cs, cs3);
						char_set_g_free(cs2);
						char_set_g_free(cs3);
						break;
					case 'S':
						cs2 = char_set_g_constructor();
						char_set_g_add_space_mcc(cs2);
						cs3 = char_set_g_create_complement(cs2);
						char_set_g_union_char_set(cs, cs3);
						char_set_g_free(cs2);
						char_set_g_free(cs3);
						break;
					case 'D':
						cs2 = char_set_g_constructor();
						char_set_g_add_digit_mcc(cs2);
						cs3 = char_set_g_create_complement(cs2);
						char_set_g_union_char_set(cs, cs3);
						char_set_g_free(cs2);
						char_set_g_free(cs3);
						break;
					case 'U':
						cs2 = char_set_g_constructor();
						char_set_g_add_universe(cs2, g->last_value_parsed_extra);
						cs3 = char_set_g_create_complement(cs2);
						char_set_g_union_char_set(cs, cs3);
						char_set_g_free(cs2);
						char_set_g_free(cs3);
						break;
					default:
						parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: unknown metacharacter set");
						exit(-31);
						break;
				}
				break;
			default:
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: unknown escape sequence");
				exit(-31);
				break;
			}
			num_chars++;
			break;
	    case '-':
			if (range_flag) {
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: invalid range end character");
				exit (-37);
			}
			/* is it a valid range? */
			/* 1. look back.  Is that a valid character? */
			if ( (g->last_chartype_parsed == CT_CHAR) || 
				 (g->last_chartype_parsed == CT_NSC) ||
				 (g->last_chartype_parsed == CT_CONTROL) ||
				 (g->last_chartype_parsed == CT_METACHAR))
			{
				/* 2. prepare for next char */
				range_flag = 1;
				range_start = g->last_value_parsed;
				range_char = char_set_g_offset(c) + char_set_g_get_pos(c);
				char_set_g_adv_pos(c, 1);
			}
			else /*(g->last_chartype_parsed == CT_MCC)*/ {
				/* the range character is to be understood literally */
				parse_regex_pass_char(c);
				if (node) {
					parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above - as a character, not a range");
				}
				num_chars++;
				char_set_g_add_char(cs, '-');
			}
			/* enable if we want to check for invalid startpoints of a range */
			/* else {
				// the range start_char is not a valid range character
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: previous character is an invalid range start character");
				exit(-37);
				} */
			break;
	    default:
			/* it must be a character */
			if (! range_flag) {
				range_start_pos = char_set_g_offset(c) + char_set_g_get_pos(c);
			}
			parse_regex_pass_char(c);
			if (node) {
				parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed above character");
			}
			num_chars++;
			if (range_flag) {
				if ( (K_ALLOW_RANGE_ENDPOINTS_IN_DIFFERENT_CLASSES) ||
				 (parse_regex_same_char_class(range_start, g->last_value_parsed)))
				{
				char_set_g_add_range(cs, range_start, g->last_value_parsed);
				parse_regex_print_range(c, range_start_pos);
				g->last_chartype_parsed = CT_RANGE_END;
				range_flag = 0;
				} else {
					parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: Range start and end characters are not in the same class.  The use of this is dangerous and deprecated.");
					exit(-31);
				}		    
			} else {
				char_set_g_add_char(cs, g->last_value_parsed);
			}
			break;
		}
	
		char_set_p_assert_usability(c, "parse_regex_pass_char_class", "Premature end of character class");
		g->current_atom_start_pos = char_set_g_get_pos(c);
    }

    if (num_chars == 0) {
	parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: This class contains no characters");
	exit(-31);
    }

    g->universe_check_code = saved_ucl;

    if (!negate_char_class) {
		if (g->universe_check_code & K_CHECK_CLASSES) {
			cs2 = char_set_g_create_intersection(g->universe, cs);
			if (char_set_g_size(cs2) == 0) {
				g->current_atom_start_pos = g->char_class_start;
				char_set_g_adv_pos(c, 1);
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: This class contains no characters from the universe set");
				exit(-31);
			}
			char_set_g_deep_copy(g->last_class, cs2);
			char_set_g_free(cs2);
		} else {
			char_set_g_deep_copy(g->last_class, cs);
		}
    } else {
		cs2 = char_set_g_create_complement(cs);
		if (g->universe_check_code & K_CHECK_CLASSES) {
			cs3 = char_set_g_create_intersection(g->universe, cs2);
			if (char_set_g_size(cs3) == 0) {
				g->current_atom_start_pos = g->char_class_start;
				char_set_g_adv_pos(c, 1);
				parse_regex_print_c(c, D_Error, "parse_regex_pass_char_class: This negated class contains no characters from the universe set");
				exit(-31);
			}
			char_set_g_deep_copy(g->last_class, cs3);
			char_set_g_free(cs3);
		} else {
			char_set_g_deep_copy(g->last_class, cs2);
		}
		char_set_g_free(cs2);
    }
    char_set_g_free(cs);

    g->last_chartype_parsed = CT_CHAR_CLASS_FINISH;
    char_set_g_adv_pos(c, 1);
}

void parse_regex_print_range (char_set c, int range_start_pos)
{
    int saved = g->current_atom_start_pos;
    
    g->current_atom_start_pos = range_start_pos;
    parse_regex_print_c(c, D_Parse_Regex_Eachstep, "Parsed as a range");
    g->current_atom_start_pos = saved;
}
	
void parse_regex_print_char_class (char_set c)
{
    char * buf;
    int bufsize;
    int saved = g->current_atom_start_pos;
    
    g->current_atom_start_pos = g->char_class_start;
    bufsize = 23 + ((int) log10(g->num_char_classes_started)) + 1 + 1;
    buf = (char *) check_malloc (sizeof(char) * bufsize);
    sprintf(buf, "Parsed character class %d", g->num_char_classes_started);
    buf[bufsize-1] = '\0';
    parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
    g->current_atom_start_pos = saved;
    free(buf);

    if (g->debug_code & D_Parse_Regex_Eachstep) {
	debug_print(D_Parse_Regex_Eachstep, "Character class contains:");
	char_set_g_display(g->last_class);
    }
}

int parse_regex_same_char_class (int a, int b)
{
    if (isupper(a) && isupper(b)) {
	return (1);
    } else if (islower(a) && islower(b)) {
	return (1);
    } else if (isdigit(a) && isdigit(b)) {
	return (1);
    } else {
	return (0);
    }
}

void parse_regex_pass_quantifier (char_set c)  /* !na */
{
    char ch;

    switch(g->last_chartype_parsed) {
	case CT_CHAR:
	case CT_NSC:
	case CT_BACKREF:
	case CT_MCC:
	case CT_GROUP_FINISH:
	case CT_CHAR_CLASS_FINISH:
	case CT_CONTROL:
	case CT_METACHAR:
	    /* these are valid preceeding character types */
	    break;
	default:
	    char_set_g_adv_pos(c, 1);
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_quantifier: quantifier modifier follows invalid character type!");
	    exit(-23);
	    break;
    }

    char_set_p_assert_usability(c, "parse_regex_pass_quantifier", "Premature end of quantifier");
    
    ch = char_set_p_char_n(c, 0);
    switch (ch) {
	case '*':
	case '+':
	case '?':
	    char_set_g_adv_pos(c, 1);
	    g->last_chartype_parsed = CT_QUANTIFIER;
	    /* set min */
	    g->last_value_parsed = (ch == '+') ? 1 : 0;
	    /* set max */
	    g->last_value_parsed_extra = (ch == '?') ? 1 : -1;
	    break;
	case '{':
	    g->current_atom_start_pos = char_set_g_get_pos(c);
	    //g->parse_regex_mark = char_set_g_get_pos(c) + char_set_g_offset(c);
	    char_set_g_adv_pos(c, 1);
	    parse_regex_pass_braced_quantifier(c);
	    g->last_chartype_parsed = CT_BRACED_QUANTIFIER_FINISH;
	    break;
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_quantifier: unknown quantifier!");
	    exit(-8);
    }
}

void parse_regex_pass_braced_quantifier (char_set c)
{
    char_set_p_assert_usability(c, "parse_regex_pass_braced_quantifier", "Premature end of braced quantifier");

    g->last_value_parsed = parse_regex_pass_braced_quantifier_number(c);
    g->last_value_parsed_extra = 0;

    char_set_p_assert_usability(c, "parse_regex_pass_braced_quantifier", "Premature end of braced quantifier");

    if (char_set_p_char_n(c, 0) == '}') {
	/* is fixed length */
	char_set_g_adv_pos(c, 1);
	return;
    } else if (char_set_p_char_n(c, 0) != ',') {
	parse_regex_print_c(c, D_Error, "parse_regex_pass_braced_quantifier: invalid character after first number!");
	exit(-9);
    }
    char_set_g_adv_pos(c, 1);

    char_set_p_assert_usability(c, "parse_regex_pass_braced_quantifier", "Premature end of braced quantifier");
    
    /* is variable length */
    g->last_value_parsed_extra = -1;

    if (char_set_p_char_n(c, 0) == '}') {
	char_set_g_adv_pos(c, 1);
	return;
    } else {
	g->last_value_parsed_extra = parse_regex_pass_braced_quantifier_number(c);
    }
    
    char_set_p_assert_usability(c, "parse_regex_pass_braced_quantifier", "Premature end of braced quantifier");

    if (char_set_p_char_n(c, 0) != '}') {
	parse_regex_print_c(c, D_Error, "parse_regex_pass_braced_quantifier: invalid character after second number (expected })!");
	exit(-9);
    }
    char_set_g_adv_pos(c, 1);
}

int parse_regex_pass_braced_quantifier_number (char_set c)
{
    int n = 0; /* string index */
    int val = 0;

    char_set_p_assert_usability(c, "parse_regex_pass_braced_quantifier_number", "Premature end of braced quantifier number (no number specified!)");

    while ((char_set_g_get_pos(c) + n < char_set_g_size(c)) &&
	   (index("0123456789", char_set_p_char_n(c, n)) != NULL))
    {
	n++;
	if (n > K_NUM_DIGITS_IN_BRACED_QUANTIFIER_NUMBER) {
	    char_set_g_adv_pos(c, n-1);
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_braced_quantifier_number: Number of digits in braced quantifier number is too many.  (Last character pointed to is the first invalid character)");
	    exit(-10);
	}
    }

    val = parse_regex_read_dec_val (c, n, 10);
    char_set_g_adv_pos(c, n);
    
    return(val);
}

int parse_regex_pass_universe_specifier (char_set c) /* !na */
/* starts after the \u */
{
    int unum = 0;
    int max_num_digits;

    char_set_p_assert_usability(c, "parse_regex_pass_universe_specifier", "Premature end of universe specifier");

    max_num_digits = (parse_regex_ghetto_trunc(log10 (g->max_universe_num)) + 1);
    debug_print(D_Parse_Regex, "The max universe specifier length is calculated at %d", max_num_digits);

    if (char_set_p_char_n(c, 0) == '{') {
	char_set_g_adv_pos(c, 1);
	char_set_p_assert_usability(c, "parse_regex_pass_universe_specifier", "Premature end of universe specifier");
	unum = parse_regex_pass_braced_number(c, "universe specifier", "0123456789", max_num_digits, -1, g->max_universe_num);
    } else {
	unum = parse_regex_pass_variable_length_number(c, "universe specifier", "0123456789", max_num_digits, -1, g->max_universe_num);
    }

    return (unum);
}

void parse_regex_pass_backref (char_set c)
/* Note: we got here because the first character was a 123456789 or ! */
{
    int val;

    if (char_set_p_char_n(c, 0) == '!') {
	char_set_g_adv_pos(c, 1);
	char_set_p_assert_usability(c, "parse_regex_pass_backreference", "Premature end of backreference");
	if (char_set_p_char_n(c, 0) == '{') {
	    char_set_g_adv_pos(c, 1);
	    val = parse_regex_pass_braced_number(c, "backreference", "0123456789", K_MAX_NUM_DIGITS_IN_BACKREFERENCE_NUMBER, -1, -1);
	} else {
	    val = parse_regex_pass_variable_length_number(c, "backreference", "0123456789", K_MAX_NUM_DIGITS_IN_BACKREFERENCE_NUMBER, -1, -1);
	}
    } else {
	val = parse_regex_pass_variable_length_number(c, "backreference", "0123456789", K_MAX_NUM_DIGITS_IN_BACKREFERENCE_NUMBER, -1, -1);
    }

    /* does it point to a valid group? */
    if (silist_find(g->finished_groups, val) == -1) {
	parse_regex_print_c(c, D_Error, "parse_regex_pass_backref: above backreferences is for a non-existant group");
	exit(-34);
    }

    g->last_chartype_parsed = CT_BACKREF;
    g->last_value_parsed = val;
}

void parse_regex_pass_control_char (char_set c)
{
    int val = 0;

    char_set_p_assert_usability(c, "parse_regex_pass_control_char", "Premature end of control character");

    switch (char_set_p_char_n(c, 0)) {
	/* put in different valid cases here! */
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_control_char: specified control character is not recognized by this program!");
	    exit(-18);
	    break;
    }

    g->last_value_parsed = val;
    g->last_chartype_parsed = CT_CONTROL;
    char_set_g_adv_pos(c, 1);
}
	      
int parse_regex_pass_decimal_char(char_set c)
{
    char_set_p_assert_usability(c, "parse_regex_pass_decimal_char", "Premature end of octal charcter");

    if (char_set_p_char_n(c, 0) == '{') {
	char_set_g_adv_pos(c, 1);
	return (parse_regex_pass_braced_number(c, "decimal", "0123456789", 3, -1, 255));
    } else {
	return (parse_regex_pass_variable_length_number(c, "decimal", "0123456789", 3, -1, 255));
    }
}

void parse_regex_pass_nsc (char_set c)
{
    char ch;
    int val;

    char_set_p_assert_usability(c, "parse_regex_pass_nsc", "Premature end of numerically specified character");

    ch = char_set_p_char_n(c, 0);
    char_set_g_adv_pos(c, 1);

    switch (ch) {
	case 'o': /* number is octal -- base 8 */
	    val = parse_regex_pass_octal_char(c);
	    break;
	case 'z':
	    val = parse_regex_pass_decimal_char(c);
	    break;
	case 'x':
	    val = parse_regex_pass_hex_char(c);
	    break;
	default:
	    parse_regex_print_c(c, D_Error, "parse_regex_pass_nsc: specified number type is unknown. (fatal)");
	    exit(-37);
	    break;
    }

    if ( (g->universe_check_code & K_CHECK_CHARS) &&
	 (char_set_g_index(g->universe, val) == -1) )
    {
	parse_regex_print_c(c, D_Error, "parse_regex_pass_nsc: specified character is not in the current universe");
	exit(-37);
    }

    g->last_value_parsed = val;
    g->last_chartype_parsed = CT_NSC;
}

int parse_regex_pass_hex_char (char_set c)
/* responsible for both hex and wide hex chars */
{
    char_set_p_assert_usability(c, "parse_regex_pass_hex_char", "Premature end of hex character");

    if (char_set_p_char_n(c, 0) == 'w') { /* handle a wide hex character */
	char_set_g_adv_pos(c, 1);
	char_set_p_assert_usability(c, "parse_regex_pass_hex_char", "Premature end of wide hex character");
	if (char_set_p_char_n(c, 0) == '{') {
	    char_set_g_adv_pos(c, 1);
	    return (parse_regex_pass_braced_number(c, "wide hex", "0123456789abcdef", 4, -1, 65535));
	} else {
	    return (parse_regex_pass_variable_length_number(c, "wide hex", "0123456789abcdef", 4, -1, 65535));
	}
    } else { /* handle a normal hex character */
	if (char_set_p_char_n(c, 0) == '{') {
	    char_set_g_adv_pos(c, 1);
	    return (parse_regex_pass_braced_number(c, "hex", "0123456789abcdef", 2, -1, 255));
	} else {
	    return (parse_regex_pass_variable_length_number(c, "hex", "0123456789abcdef", 2, -1, 255));
	}
    }
}

int parse_regex_pass_octal_char (char_set c)
{
    char_set_p_assert_usability(c, "parse_regex_pass_octal_char", "Premature end of octal charcter");

    if (char_set_p_char_n(c, 0) == '{') {
	char_set_g_adv_pos(c, 1);
	return (parse_regex_pass_braced_number(c, "octal", "01234567", 3, -1, 255));
    } else {
	return (parse_regex_pass_variable_length_number(c, "octal", "01234567", 3, -1, 255));
    }
}

int parse_regex_read_dec_val (char_set c, int num_chars, int base)
/* This function does no error checking!  Any calls to this
** function must have been preceeded by a valid pass!
** This function works with characters from 0-9, a-f, and A-F */
{
    int dec_val = 0;
    char digit;
    int val;
    int i;
    
    for (i=num_chars - 1; i >= 0; i--) {
	digit = char_set_p_char_n(c, i);
	switch (digit) {
	    case '0': case '1': case '2': case '3': case '4':
	    case '5': case '6': case '7': case '8': case '9':
		val = digit - 48;
		break;
	    case 'a': case 'b': case 'c':
	    case 'd': case 'e': case 'f':
		val = digit - 87;
		break;
	    case 'A': case 'B': case 'C':
	    case 'D': case 'E': case 'F':
		val = digit - 55;
		break;
	    default:
		parse_regex_print_c(c, D_Error, "parse_regex_read_dec_val: unknown character in acceptible characters string. (fatal)");
		exit(-39);
		break;
	};
	debug_print(D_Parse_Regex, "val is %d", val);
	dec_val += (int) (pow(base, num_chars-1-i) * val);
	debug_print(D_Parse_Regex, "new dec_val is %d", dec_val);
    }

    return (dec_val);
}

void parse_regex_pass_char (char_set c) /* !Na */
/* make sure the current character at pos is in the universe! */
{
    char_set_p_assert_usability(c, "parse_regex_pass_char", "Premature end of character");

    if ( (g->universe_check_code & K_CHECK_CHARS) &&
	 (char_set_g_index(g->universe, char_set_p_char_n(c, 0)) == -1) )
    {
    char_set_g_adv_pos(c, 1);
	parse_regex_print_c(c, D_Error, "parse_regex_pass_char: specified character is not in the universe!");
	exit(-21);
    }

    g->last_value_parsed = char_set_p_char_n(c, 0);
    g->last_chartype_parsed = CT_CHAR;
    
    char_set_g_adv_pos(c, 1);
}

int parse_regex_pass_variable_length_number (char_set c, const char * format, const char * allowed_chars, int max_length, int min_val, int max_val)
{
    int n = 0;
    char * buf;
    int bufsize;
    int dec_val;

    /* prepare an error string */
    bufsize = 27 + strlen(format) + 1;
    buf = (char *) check_malloc (sizeof(char) * bufsize);
    sprintf(buf, "Premature end of %s character", format); 
    buf[bufsize-1] = '\0';

    char_set_p_assert_usability(c, "parse_regex_pass_variable_length_number", buf);

    while ( (char_set_g_get_pos(c) + n < char_set_g_size(c)) &&
	    (n < max_length) &&
	    (index(allowed_chars, tolower(char_set_p_char_n(c, n))) != NULL))
    {
	n++;
    }

    if (n == 0) {
		bufsize = 64 + strlen(format) + 1;
		buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
		sprintf(buf, "parse_regex_pass_variable_length_number: No %s character specified!", format);
		buf[bufsize-1] = '\0';
		char_set_g_adv_pos(c, n);
		parse_regex_print_c(c, D_Error, buf);
		exit(-6);
    }

    dec_val = parse_regex_read_dec_val (c, n, strlen(allowed_chars));

    if (min_val != -1) {
		if (dec_val < min_val) {
			bufsize = 67 + strlen(format) + 1;
			buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
			sprintf(buf, "parse_regex_pass_braced_number: %s is too small! (Min is decimal %d)", format, max_val);
			buf[bufsize-1] = '\0';
			char_set_g_adv_pos(c, n);
			parse_regex_print_c(c, D_Error, buf);
			exit(-22);
		}
    }

    if (max_val != -1) {
		if (dec_val > max_val) {
			bufsize = 70 + strlen(format) + 1;
			buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
			sprintf(buf, "parse_regex_pass_variable_length_number: %s's value is too large!", format);
			buf[bufsize-1] = '\0';
			char_set_g_adv_pos (c, n);
			parse_regex_print_c(c, D_Error, buf);
			debug_print(D_Parse_Regex, "parse_regex_pass_variable_length_number: %s's value is %d", format, dec_val);
			exit(-6);
		}
    }

    /* move to the end of the number */
    char_set_g_adv_pos(c, n);

/* take out for updates 
    bufsize = 23 + strlen(format) + 1;
    sprintf(buf, "Parsed variable length %s", format);
    buf[bufsize-1] = '\0';
    parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
*/
    free(buf);
    return (dec_val);
}

int parse_regex_pass_braced_number (char_set c, const char * format, const char * allowed_chars, int max_length, int min_val, int max_val)
/* we start at the character after the first { */
{
    int n = 0;
    char * buf;
    int bufsize;
    int dec_val;

    /* prepare an error string */
    bufsize = 27 + strlen(format) + 1;
    buf = (char *) check_malloc (sizeof(char) * bufsize);
    sprintf(buf, "Premature end of %s character", format); 
    buf[bufsize-1] = '\0';

    char_set_p_assert_usability(c, "parse_regex_pass_braced_number", buf);

    while ( (char_set_g_get_pos(c) + n < char_set_g_size(c)) &&
	    (char_set_p_char_n(c, n) != '}') )
    {
	/* if there is an invalid character, vomit! */
	if (index(allowed_chars, tolower(char_set_p_char_n(c,n))) == NULL) {
	    bufsize = 50 + strlen(format) + 1;
	    buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
	    sprintf(buf, "parse_regex_pass_braced_number: invalid %s character", format);
	    buf[bufsize-1] = '\0';
	    char_set_g_adv_pos(c, n + 1);
	    parse_regex_print_c(c, D_Error, buf);
	    exit(-22);
	}
	/* if the valid characters are too many */
	if (n >= max_length) {
	    bufsize = 72 + strlen(format) + 1;
	    buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
	    sprintf(buf, "parse_regex_pass_braced_number: %s number is too long! Missing closing '}'", format);
	    buf[bufsize-1] = '\0';
	    char_set_g_adv_pos(c, n + 1);
	    parse_regex_print_c(c, D_Error, buf);
	    exit(-22);
	}
	n++;
    }

    /* if we finished looking for characters because we are at 
    ** the end of the char_set */
    if (char_set_g_get_pos(c) + n >= char_set_g_size(c)) {
	bufsize = 63 + strlen(format) + 1;
	buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
	sprintf(buf, "parse_regex_pass_braced_number: Premature end of braced %s number!", format);
	buf[bufsize-1] = '\0';
	char_set_g_adv_pos(c, n + 1);
	parse_regex_print_c(c, D_Error, buf);
	exit(-22);
    }

    /* otherwise, we stopped because we found a '}' */

    if (n == 0) {
		bufsize = 63 + strlen(format) + 1;
		buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
		sprintf(buf, "parse_regex_pass_braced_number: Premature end of braced %s number!", format);
		buf[bufsize-1] = '\0';
		char_set_g_adv_pos(c, n + 1);
		parse_regex_print_c(c, D_Error, buf);
		exit(-22);
    }

    /* calculate the value of the character */
    dec_val = parse_regex_read_dec_val(c, n, strlen(allowed_chars));

    if (min_val != -1) {
		if (dec_val < min_val) {
			bufsize = 80 + strlen(format) + 1;
			buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
			sprintf(buf, "parse_regex_pass_braced_number: %s's value is too small! (Min is decimal %d)", format, max_val);
			buf[bufsize-1] = '\0';
			char_set_g_adv_pos(c, n);
			parse_regex_print_c(c, D_Error, buf);
			exit(-22);
		}
    }

    if (max_val != -1) {
		if (dec_val > max_val) {
			bufsize = 80 + strlen(format) + 1;
			buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
			sprintf(buf, "parse_regex_pass_braced_number: %s's value is too large! (Max is decimal %d)", format, max_val);
			buf[bufsize-1] = '\0';
			char_set_g_adv_pos(c, n);
			parse_regex_print_c(c, D_Error, buf);
			exit(-22);
		}
    }
    
    /* pass the last '}' */

    char_set_g_adv_pos(c, n + 1);

/* take out for updates
    bufsize = 14 + strlen(format) + 1;
    buf = (char *) check_realloc (buf, sizeof(char) * bufsize);
    sprintf(buf, "Parsed braced %s", format);
    buf[bufsize-1] = '\0';
    parse_regex_print_c(c, D_Parse_Regex_Eachstep, buf);
*/

    free(buf);

    return (dec_val);
}

void parse_regex_print_c (char_set c, int dlevel, const char * msg)
/* print the global regex and an error finding line */
{
    int n=0, bufsize = 0;
    char* buf = NULL;

    /* print the regex into the char buf */
    bufsize = char_set_g_size(g->regex) + 1;
    buf = (char*) check_malloc (sizeof(char) * (bufsize));
    
    while (n < char_set_g_size(g->regex)) {
		sprintf(buf + n, "%c", char_set_g_char_n(g->regex, n));
		n++;
    }
    buf[n] = '\0';
    debug_print(dlevel, buf);

    /* print the error finding line into the char buf */
    bufsize = char_set_g_offset(c) + char_set_g_get_pos(c) + 2;
    buf = (char*) check_realloc (buf, sizeof(char) * bufsize);

    n = 0;
    while (n < char_set_g_offset(c) + g->current_atom_start_pos) {
		sprintf(buf + n, " ");
		n++;
    }
    while (n < char_set_g_offset(c) + char_set_g_get_pos(c)) {
		sprintf(buf + n, "^");
		n++;
    }
    buf[n] = '\0';

    debug_print(dlevel, buf);
    debug_print(dlevel, msg);
    
    free (buf);
}

int parse_regex_ghetto_trunc(double d)
{
    debug_print(D_Parse_Regex, "parse_regex_ghetto_trunc: %f becomes %d", d, (int) d);
    return ((int) d);
}
