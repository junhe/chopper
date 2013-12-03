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
** memory.h
** Safe functions for memory usage
*/


#ifndef REGLDG_MEMORY_H
#define REGLDG_MEMORY_H

#include <stdio.h>

void * check_malloc (size_t);
void * check_realloc (void *, size_t);
void * check_calloc (size_t, size_t);

#endif
