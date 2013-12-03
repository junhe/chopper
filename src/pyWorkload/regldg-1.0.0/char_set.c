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
** char_set.c
** A character set.
** 9 July 2004
*/

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "memory.h"
#include "char_set.h"
#include "data.h"
#include "debug.h"
#include "parse_regex.h"

extern gg g;

char_set char_set_g_constructor(void)
{
    char_set c = (char_set) check_malloc (sizeof(char_set_struct));
    c->set = NULL;
    c->size = 0;
    c->pos = 0;
    c->ancestral_offset = 0;

    return (c);
}

void char_set_g_init(char_set c, char * str)
{
    /* delete current contents if necessary */
    if (c->size > 0) {
		char_set_g_free (c);
    }
    char_set_g_insert_string(c, str);
}

void char_set_g_insert_string(char_set c, char * str)
{
    int size = strlen(str);
    
    c->set = (char *) check_realloc (c->set, sizeof(char) * (c->size + size + 1));
    strncpy(c->set + (sizeof(char) * c->size), str, size + 1);
    c->size += size;

    debug_print(D_Char_Set, "Added %s to char_set", str);
    debug_print(D_Char_Set, "Set char_set size to %d", c->size);
}

int char_set_g_index(char_set c, char ch)
{
    int n = 0;
    while (n < c->size) {
	if (c->set[n] == ch) {
	    return (n);
	}
	n++;
    }
    /* character is not found in the set */
    return (-1);
}

void char_set_g_add_universe(char_set c, int universe_int)
{
    /*
      Universe 1:   The letters A-Z
      Universe 2:   The numbers 0-9
      Universe 4:   The digits
      Universe 8:   The shift-number-characters without brackets: !@#$%^&*
      Universe 16:   Punctuation marks: ;:`'" ,.?_   (don't miss space)
      Universe 32:  Brackets: (){}[]
      Universe 64:  Other random characters: ~\/|
      Universe 128:  Math +-=
    */
    int two_power = K_NUM_UNIVERSE_SETS;
   
    char universe_1[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    char universe_2[] = "abcdefghijklmnopqrstuvwxyz";
    char universe_4[] = "0123456789";
    char universe_8[] = "!@#$%^&*";
    char universe_16[] = ";:`'\" ,.?_";
    char universe_32[] = "(){}[]";
    char universe_64[] = "~\\/|";
    char universe_128[] = "+-=";
   
    char *all_universes[K_NUM_UNIVERSE_SETS] = { universe_1, universe_2, universe_4, universe_8, universe_16, universe_32, universe_64, universe_128 };

    int universe_set_sizes[K_NUM_UNIVERSE_SETS] = { 26, 26, 10, 8, 10, 6, 4, 3 };

    if (universe_int > pow(2, K_NUM_UNIVERSE_SETS) - 1) {
	debug_print(D_Error, "Number given to char_set_add_universe is too large.  Max is %d.", (int) (pow(2, K_NUM_UNIVERSE_SETS) - 1));
	exit(-2);
    }

    while (two_power > 0) {
	two_power--;
	if (universe_int >= pow(2, two_power)) {
	    char_set_g_union_str(c, all_universes[two_power], universe_set_sizes[two_power]);
	    universe_int -= pow(2, two_power);
	}
    }
}

int char_set_g_size (char_set c)
{
    return (c->size);
}

char char_set_p_char_n (char_set c, int n)
{
/* Set starts at char 0 */
    if (c->pos + n >= c->size) {
	debug_print(D_Error, "char_set_p_char_n: char %d from postion was requested, but set is too small (global_size %d, position_at %d)", n, c->size, c->pos);
	exit(-2);
    }
    return (c->set[c->pos + n]);
}

char char_set_g_char_n (char_set c, int n)
{
/* Set starts at char 0 */
    if (n >= c->size) {
	debug_print(D_Error, "char_set_g_char_n: char %d was requested, but set is too small (size is %d)", n, c->size);
	exit(-2);
    }
    return (c->set[n]);
}

void char_set_g_display (char_set c) {
    int n;
    int numrows = (int) ceil((double) c->size / 4); /* 4 chars per row */
    for (n=0; n < numrows; n++) {
		if (n + 1 <= c->size) {
			if (isprint(c->set[n])) {
				printf("char %3d: %.3d=%c    ", n + 1, c->set[n], c->set[n]);
			} else {
				printf("char %3d: %.3d(np)  ", n + 1, c->set[n]);
			}
			if (n + 1 + numrows <= c->size) {
				if (isprint(c->set[n+numrows])) {
					printf("char %3d: %.3d=%c    ", n + 1 + numrows, c->set[n + numrows], c->set[n + numrows]);
				} else {
					printf("char %3d: %.3d(np)  ", n + 1 + numrows, c->set[n + numrows]);
				}
				if (n + 1 + (2 * numrows) <= c->size) {
					if (isprint(c->set[n + (2*numrows)])) {
						printf("char %3d: %.3d=%c    ", n + 1 + (2 * numrows), c->set[n + (2*numrows)], c->set[n + (2*numrows)]);
					} else {
						printf("char %3d: %.3d(np)  ", n + 1 + (2 * numrows), c->set[n + (2*numrows)]);
					}
					if (n + 1 + (3 * numrows) <= c->size) {
						if (isprint(c->set[n + (3*numrows)])) {
							printf("char %3d: %.3d=%c    ", n + 1 + (3 * numrows), c->set[n + (3*numrows)], c->set[n + (3*numrows)]);
						} else {
							printf("char %3d: %.3d(np)  ", n + 1 + (3 * numrows), c->set[n + (3*numrows)]);
						}
					} printf("\n");
				} else printf("\n");
			} else printf("\n");
		} else printf("\n");
    }
}

char * char_set_g_get_set (char_set c)
{
    return (c->set);
}

void char_set_g_free (char_set c)
{
    free (c->set);
    c->set = NULL;
    c->size = 0;
    c->pos = 0;
    c->ancestral_offset = 0;
}

int char_set_g_adv_pos (char_set c, int n)
{
    /* Should we allow the position to be pushed past the end
    ** of the string? */
//    if (c->pos + n >+ c->size) {
//	parse_regex_print(c, D_Error, "char_set_g_adv_pos: trying to advance the position past the end of the character set!");
//	exit(-18);
//    }

    c->pos += n;

    if (c->pos >= c->size) {
	return(0);
    }

    return(1);
}

void char_set_g_clip_front_dont_use_this_function (char_set c, int n)
{
    if (n > c->size) {
	debug_print(D_Error, "char_set_clip_front: trying to clip more characters than are in the set!");
	exit(-14);
    }
    
    /* if we are clipping the whole buffer */
    if (c->size == n) {
	free (c->set);
	c->set = NULL;
	c->size = 0;
    }
    else {
	/* move the characters and resize the char set buffer */
	c->size -= n;
	memcpy(c->set, c->set + n, c->size);
	c->set = (char *) check_realloc (c->set, sizeof(char) * c->size);
    }
    c->ancestral_offset += n;
}

void char_set_g_deep_copy (char_set dest, char_set src)
{
    dest->size = src->size;
    dest->pos = src->pos;
    dest->ancestral_offset = src->ancestral_offset;
    dest->set = (char *) check_realloc (dest->set, sizeof(char) * dest->size);
    memcpy(dest->set, src->set, dest->size);
}

int char_set_g_offset (char_set c)
{
    return (c->ancestral_offset);
}

int char_set_g_get_pos (char_set c)
{
    return (c->pos);
}

void char_set_p_assert_usability (char_set c, const char * func_name, const char * err)
{
    /* the set is usable from pos if the set is non-empty, and
    ** the pos is pointing to a char in the set */
    if (c->size <= 0) {
	parse_regex_print_c(c, D_Error, err);
	debug_print(D_Char_Set, "char_set_p_assert_usability: empty char_set! (called by %s)", func_name);
	debug_print(D_Char_Set, "Size = %d", c->size);
	exit(-20);
    }
    else if ((c->pos < 0) || (c->pos >= c->size)) {
	parse_regex_print_c(c, D_Error, err);
	debug_print(D_Char_Set, "char_set_p_assert_usability: invalid char_set position! (called by %s)", func_name);
	debug_print(D_Char_Set, "Size = %d, Position = %d", c->size, c->pos);
	exit(-20);
    }
    
    /* if we reach here to return, then the set is good! */
}

void char_set_g_union_str (char_set c, const char * str, int str_len)
{
    int i = 0;
    
    while (i < str_len) {
	char_set_g_add_char(c, str[i]);
	i++;
    }
}

void char_set_g_union_char_set (char_set dest, char_set src)
{
    int i = 0;
    int src_size = char_set_g_size(src);

    while (i < src_size) {
	char_set_g_add_char(dest, char_set_p_char_n(src, i));
	i++;
    }
}

char char_set_g_add_char(char_set c, char ch)
/* this function returns 0 if the added character was new, and 1 if it was a duplicate */
{
    if (char_set_g_index(c, ch) == -1) {
	c->size += 1;
	c->set = (char *) check_realloc (c->set, sizeof(char) * c->size);
	c->set[c->size - 1] = ch;
	return (0);
    } else {
	return (1);
    }
}

void char_set_g_insert_char(char_set c, char ch)
{
    c->size += 1;
    c->set = (char *) check_realloc (c->set, sizeof(char) * c->size);
    c->set[c->size - 1] = ch;
}

char_set char_set_g_create_intersection (char_set c1, char_set c2)
{
    int i = 0;
    int c2_size = char_set_g_size(c2);
    char_set intersection = char_set_g_constructor();

    while (i < c2_size) {
		if (char_set_g_index(c1, c2->set[i]) != -1) {
				char_set_g_add_char(intersection, c2->set[i]);
		}
		i++;
    }

    return (intersection);
}

void char_set_g_add_all_chars (char_set c)
{
    int i = 0;

    if (c->size != 0) {
	char_set_g_free(c);
    }

    c->size = 256;
    c->set = (char *) check_malloc (sizeof(char) * 256);

    for (i = 0; i < 256; i++) {
	c->set[i] = i;
    }
}

char_set char_set_g_create_complement (char_set c)
/* references the character set 0 -> 255, not the program universe! */
{
    int i;
    int u_size;
    char_set all_chars, complement;

    all_chars = char_set_g_constructor();
    char_set_g_add_all_chars(all_chars);

    complement = char_set_g_constructor();

    u_size = char_set_g_size(all_chars);
    
    for (i = 0; i < u_size; i++) {
	if (char_set_g_index(c, all_chars->set[i]) == -1) {
	    char_set_g_add_char(complement, all_chars->set[i]);
	}
    }

    char_set_g_free(all_chars);

    return (complement);
}

void char_set_g_add_word_mcc (char_set c)
{
    char_set_g_union_str (c, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_", 63);
}

void char_set_g_add_space_mcc (char_set c)
{
    char_set_g_union_str (c, " \t\v\r\f\n", 6);
}

void char_set_g_add_digit_mcc (char_set c)
{
    char_set_g_union_str (c, "0123456789", 10);
}

void char_set_g_add_range(char_set c, int start, int end)
{
    int t;

    if (start > end) { /* swap */
	t = start;
	start = end;
	end = t;
    }

    for (t = start; t <= end; t++) {
	char_set_g_add_char(c, t);
    }
}
