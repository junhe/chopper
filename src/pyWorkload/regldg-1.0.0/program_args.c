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
** program_args.c
** 4 July 2004
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <unistd.h>
#include <fcntl.h>
#include "char_set.h"
#include "data.h"
#include "debug.h"
#include "memory.h"
#include "program_args.h"
#include "parse_regex.h"

extern gg g;

void program_args_parse(int argc, char ** argv)
{
    char got_regex = 0;
    int useful_int, bufsize = 256, end = 0;
    char ** end_ptr;
    char * buf = NULL, * regex_file = NULL;
    char_set temp_regex;

    /* Get the program name */
    g->progname = (char *) check_malloc (sizeof(char) * (strlen(argv[0]) + 1));
    strcpy(g->progname, argv[0]);
    argv++;

    if (argc < 2)
	program_args_print_usage(g->progname);

    if (argc > 16)
	program_args_print_usage(g->progname);

    end_ptr = (char **) check_malloc (sizeof(char *));
    *end_ptr = (char *) check_malloc (sizeof(char));

    /* Get the arguments */
    while (argv[0] != NULL) {
	if (strcmp(argv[0], "-us") == 0) {
	    argv++;
	    if (argv[0] == NULL) {
		debug_print(D_Error, "missing required number (for -us)");
		program_args_print_usage(g->progname);
	    }

	    /* Setting the character universe */
	    useful_int = strtol(argv[0], end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (-us NNN)");
		debug_print(D_Program_Args, "debug: the first invalid character was %d", *end_ptr[0]);
		program_args_print_usage(g->progname);
	    }
	    char_set_g_free(g->universe);
	    char_set_g_add_universe(g->universe, useful_int);

	    if (g->debug_code & D_Program_Args) {
		debug_print(D_Program_Args, "Set universe_set to:");
		char_set_g_display(g->universe);
	    }
	}
	else if (strncmp(argv[0], "--universe-set=", 15) == 0) {
	    /* Setting the universe set */
	    if (argv[0][11] == '\0') {
		debug_print(D_Error, "missing required number (for --universe-set=NNN)");
		program_args_print_usage(g->progname);
	    }

	    /* Setting the character universe */
	    useful_int = strtol(argv[0]+(15*sizeof(char)), end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for --universe-set=NNN)");
		debug_print(D_Program_Args, "debug: the first invalid character was %d", *end_ptr[0]);
		program_args_print_usage(g->progname);
	    }
	    char_set_g_free(g->universe);
	    char_set_g_add_universe(g->universe, useful_int);

	    if (g->debug_code & D_Program_Args) {
		debug_print(D_Program_Args, "Set universe_set to:");
		char_set_g_display(g->universe);
	    }
	}
	else if (strcmp(argv[0], "-uc") == 0) {
	    /* Setting the universe check code */
	    argv++;
	    if (argv[0] == NULL) {
		debug_print(D_Error, "missing required number (for -uc)");
		program_args_print_usage(g->progname);
	    }

	    useful_int = strtol(argv[0], end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "%s: error in number string (-uc NNN)", g->progname);
		program_args_print_usage(g->progname);
	    }
	    if (useful_int > 3) {
		debug_print(D_Error, "-uc code set too high (max is 3)");
		program_args_print_usage(g->progname);
	    }
	    g->universe_check_code = useful_int;

	    debug_print(D_Program_Args, "Set universe_check_code to %d", useful_int);
	}
	else if (strncmp(argv[0], "--universe-checking=", 20) == 0) {

	    if (argv[0][20] == '\0') {
		debug_print(D_Error, "missing required number (for --universe_checking=NNN)");
		program_args_print_usage(g->progname);
	    }

	    /* Setting the max word length */
	    useful_int = strtol(argv[0]+(20*sizeof(char)), end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for --universe-checking=NNN)");
		program_args_print_usage(g->progname);
	    }
	    if (useful_int > 3) {
		debug_print(D_Error, "--universe-checking code set too high (max is 3)");
		program_args_print_usage(g->progname);
	    }
	    g->universe_check_code = useful_int;
	 
	    debug_print(D_Program_Args, "Set universe_check_code to %d", useful_int);
	}
	else if (strcmp(argv[0], "-m") == 0) {
	    /* Setting the max word length */
	    argv++;
	    if (argv[0] == NULL) {
		debug_print(D_Error, "missing required number (for -u)");
		program_args_print_usage(g->progname);
	    }

	    useful_int = strtol(argv[0], end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "%s: error in number string (-m NNN)", g->progname);
		program_args_print_usage(g->progname);
	    }
	    g->max_word_length = useful_int;

	    debug_print(D_Program_Args, "Set max_word_length to %d", useful_int);
	}
	else if (strncmp(argv[0], "--max-length=", 13) == 0) {

	    if (argv[0][13] == '\0') {
		debug_print(D_Error, "missing required number (for --max-length=NNN)");
		program_args_print_usage(g->progname);
	    }

	    /* Setting the max word length */
	    useful_int = strtol(argv[0]+(13*sizeof(char)), end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for --max-length=NNN)");
		program_args_print_usage(g->progname);
	    }
	    g->max_word_length = useful_int;

	    debug_print(D_Program_Args, "Set max_word_length to %d", useful_int);
	}
	else if (strcmp(argv[0], "-d") == 0) {
	    /* Setting the debug code */
	    argv++;
	    if (argv[0] == NULL) {
		debug_print(D_Error, "missing required number (for -d)");
		program_args_print_usage(g->progname);
	    }

	    useful_int = strtol(argv[0], end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for -d NNN");
		program_args_print_usage(g->progname);
	    }
	    g->debug_code = useful_int;

	    debug_print(D_Program_Args, "Set debug_code to %d", useful_int);
	}
	else if (strncmp(argv[0], "--debug-code=", 13) == 0) {

	    if (argv[0][13] == '\0') {
		debug_print(D_Error, "missing required number (for --debug-code=NNN)");
		program_args_print_usage(g->progname);
	    }

	    /* Setting the debug code */
	    useful_int = strtol(argv[0]+(13*sizeof(char)), end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for --debug-code=NNN)");
		program_args_print_usage(g->progname);
	    }
	    g->debug_code = useful_int;

	    debug_print(D_Program_Args, "Set debug_code to %d", useful_int);
	}
	else if (strcmp(argv[0], "-p") == 0) {
		/* Parse the regex only */
		g->stop_code = 'p';
		debug_print(D_Program_Args, "Stopping after parsing the regex.");
	}
	else if (strncmp(argv[0], "--parse-only", 12) == 0) {
		/* Parse the regex only */
		g->stop_code = 'p';
		debug_print(D_Program_Args, "Stopping after parsing the regex.");
	}
	else if (strcmp(argv[0], "-r") == 0) {
		/* Enable readable output */
		g->readable_output = 1;
	}
	else if (strncmp(argv[0], "--readable-output", 17) == 0) {
		/* Enable readable output */
		g->readable_output = 1;
	}
	else if (strcmp(argv[0], "-u") == 0) {
	    /* Explicitly setting the character universe */
	    argv++;
	    if (argv[0] == NULL) {
			debug_print(D_Error, "missing required number (for -u)");
			program_args_print_usage(g->progname);
	    }

		temp_regex = char_set_g_constructor();
		char_set_g_deep_copy(temp_regex, g->regex);

		/* Read in char class, parse it, and set universe to its results */
		char_set_g_free(g->regex);
		g->regex = char_set_g_constructor();
		char_set_g_init(g->regex, argv[0]);
		/* Make sure it starts with [ */
		if (char_set_g_char_n(g->regex, 0) != '[') {
			debug_print(D_Error, "When explicitly setting a character universe, you must start with [ and end with ]!");
			program_args_print_usage(g->progname);
		}
		
		/* Force universe checking off temporarily */
		useful_int = g->universe_check_code;
		g->universe_check_code &= 2;
		
		g->last_chartype_parsed = CT_CHAR_CLASS_START;
		
		char_set_g_adv_pos(g->regex, 1);
		/* NOTE: Negated character classes will be relative to the current universe,
		** which would be either the default, or the one specified on the command line _iff_
		** it was specified before this -u argument! */
												  /* Should we be verbose in its parse? */
		parse_regex_pass_char_class(g->regex, g->debug_code & D_Program_Args & D_Parse_Regex_Eachstep);

		/* Revert to previous universe checking state */
		g->universe_check_code = useful_int;

		char_set_g_free(g->universe);
		g->universe = char_set_g_constructor();
		char_set_g_deep_copy(g->universe, g->last_class); /* Got it here! */
		
		/* Clean up */
		char_set_g_free(g->regex);
		char_set_g_deep_copy(g->regex, temp_regex);
		char_set_g_free(temp_regex);
		char_set_g_free(g->last_class);
		g->last_class = char_set_g_constructor();
		g->last_chartype_parsed = CT_UNDEFINED;
		g->last_value_parsed = 0;
		g->last_value_parsed_extra = 0;
		g->current_atom_start_pos = 0;
		
	    debug_print(D_Program_Args, "Set character universe to:");
	    if (g->debug_code & D_Program_Args) {
	    	char_set_g_display(g->universe);
	    }
	}
	else if (strncmp(argv[0], "--universe=", 11) == 0) {
	    /* Explicitly setting the character universe */
	    if (argv[0][11] == '\0') {
			debug_print(D_Error, "missing required UNIVERSE (for --universe=[UNIVERSE])");
			program_args_print_usage(g->progname);
	    }

		/* Read in char class, parse it, and set universe to its results */
		temp_regex = char_set_g_constructor();
		char_set_g_deep_copy(temp_regex, g->regex);
		
		char_set_g_free(g->regex);
		g->regex = char_set_g_constructor();
		char_set_g_init(g->regex, argv[0] + 11);
		
		/* Make sure it starts with [ */
		if (char_set_g_char_n(g->regex, 0) != '[') {
			debug_print(D_Error, "When explicitly setting a character universe, you must start with [ and end with ]!");
			program_args_print_usage(g->progname);
		}
		
		/* Force universe checking off temporarily */
		useful_int = g->universe_check_code;
		g->universe_check_code &= 2;
		
		g->last_chartype_parsed = CT_CHAR_CLASS_START;
		
		char_set_g_adv_pos(g->regex, 1);
		/* NOTE: Negated character classes will be relative to the current universe,
		** which would be either the default, or the one specified on the command line _iff_
		** it was specified before this -u argument! */
												  /* Should we be verbose in its parse? */
		parse_regex_pass_char_class(g->regex, g->debug_code & D_Program_Args & D_Parse_Regex_Eachstep);

		/* Revert to previous universe checking state */
		g->universe_check_code = useful_int;

		char_set_g_free(g->universe);
		g->universe = char_set_g_constructor();
		char_set_g_deep_copy(g->universe, g->last_class); /* Got it here! */
		
		/* Clean up */
		char_set_g_free(g->regex);
		char_set_g_deep_copy(g->regex, temp_regex);
		char_set_g_free(temp_regex);
		char_set_g_free(g->last_class);
		g->last_class = char_set_g_constructor();
		g->last_chartype_parsed = CT_UNDEFINED;
		g->last_value_parsed = 0;
		g->last_value_parsed_extra = 0;
		g->current_atom_start_pos = 0;
		
	    debug_print(D_Program_Args, "Set character universe to:");
	    if (g->debug_code & D_Program_Args) {
	    	char_set_g_display(g->universe);
	    }
	}
	else if (strcmp(argv[0], "-n") == 0) {
	    /* Setting the number of words to output */
	    argv++;
	    if (argv[0] == NULL) {
			debug_print(D_Error, "missing required number (for -n)");
			program_args_print_usage(g->progname);
	    }

	    useful_int = strtol(argv[0], end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
			/* error in number string */
			debug_print(D_Error, "error in number string (for -n NNN");
			program_args_print_usage(g->progname);
	    }
	    g->num_words_output = useful_int;

	    debug_print(D_Program_Args, "Set num_words_output to %d", useful_int);
	}
	else if (strncmp(argv[0], "--num-words-output=", 19) == 0) {
	    /* Setting the number of words to output */
	    if (argv[0][19] == '\0') {
			debug_print(D_Error, "missing required number (for --num-words-output=NNN)");
			program_args_print_usage(g->progname);
	    }

	    /* Setting the debug code */
	    useful_int = strtol(argv[0]+(19*sizeof(char)), end_ptr, 10);
	    if (*end_ptr[0] != '\0') {
		/* error in number string */
		debug_print(D_Error, "error in number string (for --num-words-output=NNN)");
		program_args_print_usage(g->progname);
	    }
	    g->num_words_output = useful_int;

	    debug_print(D_Program_Args, "Set num_words_output to %d", useful_int);
	}
	else if (strcmp(argv[0], "-f") == 0) {
	    /* Getting the regex from a file */
  	    if (got_regex == 1) {
			debug_print(D_Error, "read two regular expressions:");
			debug_print(D_Error, "  first: %s", char_set_g_get_set(g->regex));
			debug_print(D_Error, "  second: %s", argv[0]);
			program_args_print_usage(g->progname);
	    }
	    argv++;
	    if (argv[0] == NULL) {
			debug_print(D_Error, "missing required number (for -f)");
			program_args_print_usage(g->progname);
	    }

		regex_file = argv[0];
	    got_regex = 1;
	    
	    debug_print(D_Program_Args, "Will get the regex from file %s", argv[0]);
	}
	else if (strncmp(argv[0], "--file=", 7) == 0) {
	    /* Getting the regex from a file */
	    if (argv[0][7] == '\0') {
			debug_print(D_Error, "missing required number (for --file=filename)");
			program_args_print_usage(g->progname);
	    }

  	    if (got_regex == 1) {
			debug_print(D_Error, "read two regular expressions:");
			debug_print(D_Error, "  first: %s", char_set_g_get_set(g->regex));
			debug_print(D_Error, "  second: %s", argv[0]);
			program_args_print_usage(g->progname);
	    }

		regex_file = argv[0] + (7*sizeof(char));
	    got_regex = 1;
	    
	    debug_print(D_Program_Args, "Will get the regex from file %s", argv[0] + (7*sizeof(char)));
	}
	else {
	    if (got_regex == 1) {
			debug_print(D_Error, "read two regular expressions:");
			debug_print(D_Error, "  first: %s", char_set_g_get_set(g->regex));
			debug_print(D_Error, "  second: %s", argv[0]);
			program_args_print_usage(g->progname);
	    }
	    got_regex = 1;
	    char_set_g_init(g->regex, argv[0]);
	}
	argv++;
    }

	if (!got_regex) {
		debug_print(D_Error, "No regex specified!");
		program_args_print_usage(g->progname);
	}

	if (regex_file != NULL) {
	    if (strncmp(regex_file, "-\0", 2) == 0) {
			useful_int = 0;
	    } else {
	    	useful_int = open(regex_file, O_RDONLY, 444);
	    	if (useful_int < 0) {
	    		debug_print(D_Error, "Couldn't open regex file %s for reading!", regex_file);
	    		exit(-52);
	    	}
	    }
	    buf = (char *) malloc ((bufsize + 1)*sizeof(char));
	   	while (read(useful_int, buf, bufsize)) {
	   		buf[bufsize] = '\0';
	   		if (buf[strlen(buf)-1] == 10) {
	   			buf[strlen(buf)-1] = '\0';
	   			end = 1;
	   		}
		   	char_set_g_insert_string(g->regex, buf);
		   	if (end) {
		   		break;
		   	}
	   	}
	   	free(buf);
	   	close(useful_int);
	   	debug_print(D_Program_Args, "Read in the regular expression as %s", g->regex);
	}

	if (g->stop_code == 'p') {
		g->debug_code |= D_Parse_Regex_Eachstep;
	}
	
    debug_print(D_Program_Args, "using regex: %s", char_set_g_get_set(g->regex));
}

void program_args_print_usage(char * progname)
{
	fprintf(stderr, "usage: %s [options] regex\n", progname);
	fprintf(stderr, "options:\n");
	fprintf(stderr, "\t-d NNN\n");
	fprintf(stderr, "\t--debug-code=NNN\n");
	fprintf(stderr, "\t\tSet the debugging code to NNN.\n");
	fprintf(stderr, "\t-us NNN\n");
	fprintf(stderr, "\t--universe-set=NNN\n");
	fprintf(stderr, "\t\tSet the character universe to set NNN.\n");
	fprintf(stderr, "\t-uc NNN\n");
	fprintf(stderr, "\t--universe-checking=NNN\n");
	fprintf(stderr, "\t\tSet the universe checking code to NNN.\n");
	fprintf(stderr, "\t-m NNN\n");
	fprintf(stderr, "\t--max-length=NNN\n");
	fprintf(stderr, "\t\tSet the maximum output length to NNN.\n");
	fprintf(stderr, "\t-p\n");
	fprintf(stderr, "\t--parse-only\n");
	fprintf(stderr, "\t\tOnly parse the regex, and display the parsing.\n");
	fprintf(stderr, "\t-r\n");
	fprintf(stderr, "\t--readable-output\n");
	fprintf(stderr, "\t\tIn output, display ASCII codes for non-printable characters.\n");
	fprintf(stderr, "\t-u [UNIVERSE]\n");
	fprintf(stderr, "\t--universe=[UNIVERSE]\n");
	fprintf(stderr, "\t\tExplicitly set the character universe as a character class.\n");
	fprintf(stderr, "\t-n NNN\n");
	fprintf(stderr, "\t--num-words-output=NNN\n");
	fprintf(stderr, "\t\tSet the number of \"words\" to be output to NNN (default is no limit).\n");
	fprintf(stderr, "\t-f filename\n");
	fprintf(stderr, "\t--file=filename\n");
	fprintf(stderr, "\t\tRead the regex from a file (- is stdin).\n");
	
    exit(-1);
}
