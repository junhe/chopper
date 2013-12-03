<html>

<head>

<title>regldg home</title>

<style type="text/css">
h2 { font-family: optima,tahoma; font-size: 15pt; color: #3c2168 }
td { font-family: garamond; font-size: 12pt; color: #000 }
.version { font-family: garamond; font-size: 9pt; color: #fff }
a { color: #f3eb1c }
a:visited { color: #3c2168 }
</style>

</head>

<body bgcolor="#43AFCA">

<table border=0 cellpadding=0 cellspacing=0 width=760 align="center">
<tr>
	<td rowspan=11 valign="top" align="right" width=144><img src="regldg_header_left.gif"><br></td>
	<td colspan=2 height=6></td> <!-- top blue stripe -->
</tr>
<tr>
	<td colspan=2 height=3 bgcolor="#ffffff"></td> <!-- top white stripe -->
</tr>
<tr>
	<td colspan=2 height=105 valign="middle" align="center"><img src="regldg_header_name.gif"><br></td> <!-- second blue stripe -->
</tr>
<tr>
	<td colspan=2 height=22><img src="regldg_header_description.gif"><br></td>
</tr>
<tr>
	<td rowspan=7 height=149 width=207 valign="top" valign="left"><img src="regldg_header_book.gif"><br></td>
	<td height=13></td>
</tr>
<tr>
	<td height=3 bgcolor="#ffffff"></td>
</tr>
<tr>
	<td height=56>
	
	<!-- Info, Download, Documentation, Contact table -->
	<table border=0 cellpadding=0 cellspacing=0 width="100%" height="100%" valign="middle" align="center">
	<tr>
		<td rowspan=2 width="15%">&nbsp;</td>
		<td width="40%"><a href="index.html"><img src="regldg_header_info.gif" border=0></a><br></td>
		<td rowspan=2 width="10%">&nbsp;</td>
		<td width="45%"><a href="download.html"><img src="regldg_header_download.gif" border=0></a><br></td>
	</tr>
	<tr>
		<td><a href="docs/index.html"><img src="regldg_header_documentation.gif" border=0></a><br></td>
		<td><a href="contact.html"><img src="regldg_header_contact.gif" border=0></a><br></td>
	</tr>
	</table>
	
	</td>
</tr>
<tr>
	<td height=3 bgcolor="#ffffff"></td>
</tr>
<tr>
	<td height="33">
	
	<!-- Try it -->
	<table border=0 cellpadding=0 cellspacing=0 width="100%" height="100%" valign="middle" align="center">
	<form method="post" action="tryit.php">
	<tr>
		<td width="15%">&nbsp;</td>
		<td width="15%" valign="middle"><img src="regldg_header_tryit.gif"></td>
		<td width="40%" valign="middle"><input type="text" size=20 name="regex" value="<?php if (!empty($_REQUEST['regex'])) { print htmlspecialchars(stripslashes($_REQUEST['regex'])); } else { print '(a|b)[cd]{2}\1'; } ?>"></td>
		<td width="30%" valign="middle">&nbsp; <input type="submit" value="generate"></td>
	</tr>
	</form>
	</table>
	
	</td>
</tr>
<tr>
	<td height=3 bgcolor="#ffffff"></td>
</tr>
<tr>
	<td align="right" valign="middle" class="version">Current version: 1.0.0</td>
</tr>
<tr>
	<td colspan=3>
	<h2>Your results</h2><hr>
<?php
/* Get parameters */
$regldg_dir = '/Users/pcronin/briefcase/Projects/passwords/regldg-1.0.0';
$debug_code = 1;
if (isset($_REQUEST['debug_code'])) { $debug_code = $_REQUEST['debug_code']; }
$universe_set = 7;
if (isset($_REQUEST['universe_set'])) { $universe_set = $_REQUEST['universe_set']; }
$universe_checking = 3;
if (isset($_REQUEST['universe_checking'])) { $universe_checking = $_REQUEST['universe_checking']; }
$max_length = 8;
if (isset($_REQUEST['max_length'])) { $max_length = $_REQUEST['max_length']; }
$parse_only = 0;
if (isset($_REQUEST['parse_only'])) { $parse_only = 1; }
$readable_output = 1; /* no exceptions with web use on this one */
$num_words_output = 100; /* no exceptions with web use on this one */
$universe = '';
if (isset($_REQUEST['universe'])) { $universe = stripslashes($_REQUEST['universe']); }
$regex = '';
if (isset($_REQUEST['regex'])) { $regex = stripslashes($_REQUEST['regex']); }

/* Verify parameters */
$broken_input = array();
if (!preg_match('/^\d+$/', $debug_code)) { $broken_input[] = "Debug code must be a number."; }
if (!preg_match('/^\d+$/', $universe_set)) { $broken_input[] = "Universe set must be a number."; }
if (!preg_match('/^\d+$/', $universe_checking)) { $broken_input[] = "Universe checking code must be a number."; }
if (!preg_match('/^\d+$/', $max_length)) { $broken_input[] = "Max length must be a number."; }
if (!preg_match('/^[01]$/', $parse_only)) { $broken_input[] = "Parse-only flag must be checked or unchecked."; }
if ($regex == '') { $broken_input[] = "You must enter a regular expression."; }

if (count($broken_input)) {
	print "<b>Problem(s) in your entry:</b><br><ul><li>\n";
	print implode("\n<li>", $broken_input) . "</ul><br>\n";
} else {
	/* Formulate command */
	$command = array('./regldg',
					 "--debug-code=$debug_code",
					 "--universe-set=$universe_set",
					 "--universe-checking=$universe_checking",
					 "--max-length=$max_length",
					 "--readable-output",
					 "--num-words-output=$num_words_output");
	if ($parse_only) { array_push($command, '--parse-only'); }
	if ($universe != '') { array_push($command, escapeshellarg("--universe=$universe")); }
	array_push($command, '--file=-');
	#array_push($command, escapeshellarg($regex));
	
	/* Re-direct output */
	$pid = getmypid();
	array_push($command, '1>/tmp/regldg.stdout.' . $pid );
	array_push($command, '2>/tmp/regldg.stderr.' . $pid );
	
	/* Run command */
	chdir($regldg_dir);
	$handle = popen( implode(' ', $command), "w" );
	fwrite($handle, $regex);
	pclose($handle);
	
	/* Read and delete output files */
	$stdout = file('/tmp/regldg.stdout.' . $pid);
	$stderr = file('/tmp/regldg.stderr.' . $pid);
	unlink('/tmp/regldg.stdout.' . $pid);
	unlink('/tmp/regldg.stderr.' . $pid);
	
	$stdout = preg_replace('/^(.*)$/e', "stripslashes(htmlspecialchars('\\1'))", $stdout);
	$stderr = preg_replace('/^(.*)$/e', "stripslashes(htmlspecialchars('\\1'))", $stderr);
	
	# If it is an (Error) ^^^^ line (or any other ^^^ line), replace the spaces with &nbsp;
	$stdout = preg_replace('/( +)(\^+)$/e', "preg_replace('/ /','&nbsp;', '\\1').'\\2'", $stdout);
	$stderr = preg_replace('/( +)(\^+)$/e', "preg_replace('/ /','&nbsp;', '\\1').'\\2'", $stderr);
	
	/* Display output */
	array_pop($command); array_pop($command); array_pop($command);
	array_push($command, '"' . $regex . '"');
	
	print '<table border=0 cellpadding=0 cellspacing=0 width=533 align="center">' . "\n";
	print '<tr>' . "\n";
	print '	<td colspan=4 width=533 valign="top" height=29><img src="terminal_top.gif"><br></td>' . "\n";
	print '</tr>' . "\n";
	print '<tr>' . "\n";
	print '	<td width=15 background="terminal_left.gif">&nbsp;</td>' . "\n";
	print '	<td width=4 bgcolor="#ffffff"></td>' . "\n";
	print '	<td width=499 bgcolor="#ffffff" style="font-family: monaco; font-size: 9pt">' . "\n";
	print '&gt; ' . htmlspecialchars(implode(' ', $command)) . "<br>\n";
	if (count($stdout)) {
		print implode("<br>\n", $stdout) . "<br>\n<br>\n";
	}
	if (count($stderr)) {
		print implode("<br>\n", $stderr) . "<br>\n<br>\n";
	}
	print '	</td>' . "\n";
	print '	<td width=15 background="terminal_right.gif">&nbsp;</td>' . "\n";
	print '</tr>' . "\n";
	print '<tr>' . "\n";
	print '	<td colspan=4 width=512 height=24><img src="terminal_bottom.gif"></td>' . "\n";
	print '</tr>' . "\n";
	print '</table>' . "\n";
}

?>
	<h2>Everything you hoped for?</h2><hr>
	If yes, great!  Otherwise, consider the options' default values, and how they affect the run
	of the program.  Expecting more than 100 lines of output (sorry, not on the web!), or lines of output longer than
	--max-length?  Expected the space character to be in the character universe?  Check below for advanced options, or better yet,
	download the program and use it on your computer to avoid some limitations!
	<p>
	There are also some safeguards in place to prevent hacking and cross-site scripting, so if
	you are expecting characters usable in HTML to work perfectly, they may not (or, they might!).
	The stripslashes() function is used (in addition to other methods) to clean the output here on
	this webpage.
	<p><br>
	
	<h2>Advanced usage options</h2><hr>
	<table border=0 cellpadding=3 cellspacing=0>
	<form method="post" action="tryit.php">
	<tr><td colspan=2>&gt; ./regldg &nbsp; &nbsp;<input type="text" size=30 name="regex" value="<?php if (!empty($_REQUEST['regex'])) { print htmlspecialchars(stripslashes($_REQUEST['regex'])); } else { print '(a|b)[cd]{2}\1'; } ?>"> &nbsp; <input type="submit" value="generate"></td></tr>
	<tr><td width="10%" rowspan=6></td>
		<td>--debug-code=<input type="text" size=2 maxlength=2 name="debug_code" value="<?php if (isset($_REQUEST['debug_code'])) { print $_REQUEST['debug_code']; } else { print '1'; } ?>"></td></tr>
	<tr><td>--parse-only<input type="checkbox" name="parse_only" <?php if (isset($_REQUEST['parse_only'])) { print 'checked'; } ?>></td></tr>
	<tr><td>--universe-set=<input type="text" size=3 maxlength=3 name="universe_set" value="<?php if (isset($_REQUEST['universe_set'])) { print $_REQUEST['universe_set']; } else { print '7'; } ?>"></td></tr>
	<tr><td>--universe-checking=<input type="text" size=1 maxlength=1 name="universe_checking" value="<?php if (isset($_REQUEST['universe_checking'])) { print $_REQUEST['universe_checking']; } else { print '3'; } ?>"></td></tr>
	<tr><td>--max-length=<input type="text" size=3 maxlength=3 name="max_length" value="<?php if (isset($_REQUEST['max_length'])) { print $_REQUEST['max_length']; } else { print '8'; } ?>"></td></tr>
	<tr><td>--universe=<input type="text" size=25 name="universe" value="<?php if (isset($_REQUEST['universe'])) { print htmlspecialchars(stripslashes($_REQUEST['universe'])); } ?>"></td></tr>	
	</form>
	</table>
	
	</td>
</tr>
</table>

</body>

</html>