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
** debug.h
** Debugging print options
** 9 July 2004
*/

#ifndef REGLDG_DEBUG_H
#define REGLDG_DEBUG_H

/* Define Output Classes */
#define D_Error 1
#define D_Program_Args 2
#define D_Char_Set 4
#define D_Parse_Regex 8
#define D_Parse_Regex_Eachstep 16

void debug_print(int, const char *, ...);

#endif
