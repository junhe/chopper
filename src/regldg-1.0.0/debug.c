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
** debug.c
** Debugging print functions.
** 9 July 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <math.h>
#include "data.h"
#include "debug.h"

extern gg g;

void debug_print(int dcode, const char * fmt, ...)
/* This function is the central output function of the program
** for errors or debugging messages. NB: The usage is printed
** without this function. There are certain classes of output,
** defined in debug.h. This function looks at the program's
** current debugging code, which defaults to printing errors,
** and can be changed on the command line with -d code or
** --debug-code=code.  If the current debugging code matches
** the type of message to be printed, then it is printed.
** Otherwise, the message disappears.
*/
{
    va_list ap;
    int num_error_groups = 5;
    char* error_groups[num_error_groups];

    /* iyaloo math! */
    int _d_code = rint(log((double) dcode) / log((double) 2));

    error_groups[0] = "Error";
    error_groups[1] = "D_Program_Args";
    error_groups[2] = "D_Char_Set";
    error_groups[3] = "D_Parse_Regex";
    error_groups[4] = "D_Parse_Regex_Eachstep";

    if (g->debug_code > pow(2, num_error_groups) - 1) {
		fprintf(stderr, "%s: debug_print CATASTROPHE! Debug code set too high! Max is %d, you tried %d\n", g->progname, (int) pow(2, num_error_groups) - 1, g->debug_code);
		exit(-3);
    }

    if (g->debug_code & dcode) {
    	if (dcode & D_Error) {
			fprintf(stderr, "%s: (%s) ", g->progname, error_groups[_d_code]);
		} else {
			fprintf(stdout, "%s: (%s) ", g->progname, error_groups[_d_code]);
		}
		va_start(ap, fmt);
		if (dcode & D_Error) {
			vfprintf(stderr, fmt, ap);
			fprintf(stderr, "\n");
		} else {
			vfprintf(stdout, fmt, ap);
			fprintf(stdout, "\n");
		}
		va_end(ap);
    }
}
