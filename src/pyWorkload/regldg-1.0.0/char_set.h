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
** char_set.h
** A character set.
** 9 July 2004
*/

#ifndef REGLDG_CHAR_SET_H
#define REGLDG_CHAR_SET_H

#define K_NUM_UNIVERSE_SETS 8

struct _char_set {
    char * set;
    int size;
    int pos;
    int ancestral_offset;
};
typedef struct _char_set char_set_struct;
typedef struct _char_set *char_set;

char_set char_set_g_constructor(void);
void char_set_g_init(char_set, char *);
void char_set_g_insert_string(char_set, char *);
int char_set_g_index(char_set, char);
void char_set_g_add_universe(char_set, int);
int char_set_g_size (char_set);
char char_set_p_char_n (char_set, int);
char char_set_g_char_n (char_set, int);
void char_set_g_display (char_set);
char * char_set_g_get_set (char_set);
void char_set_g_free (char_set);
int char_set_g_adv_pos (char_set, int);
void char_set_g_clip_front_dont_use_this_function (char_set, int);
void char_set_g_deep_copy (char_set, char_set);
int char_set_g_offset (char_set);
int char_set_g_get_pos (char_set);
void char_set_p_assert_usability (char_set, const char *, const char *);
void char_set_g_union_str (char_set, const char *, int);
void char_set_g_union_char_set (char_set, char_set);
char char_set_g_add_char(char_set, char);
void char_set_g_insert_char(char_set, char);
char_set char_set_g_create_intersection (char_set, char_set);
void char_set_g_add_all_chars (char_set);
char_set char_set_g_create_complement (char_set);
void char_set_g_add_word_mcc (char_set);
void char_set_g_add_space_mcc (char_set);
void char_set_g_add_digit_mcc (char_set);
void char_set_g_add_range(char_set, int, int);
#endif
