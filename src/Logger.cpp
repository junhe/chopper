/*
 *  Chopper is a diagnostic tool that explores file systems for unexpected
 *  behaviors. For more details, see paper Reducing File System Tail 
 *  Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
 * 
 *  Please send bug reports and questions to jhe@cs.wisc.edu.
 *
 *  Written by Jun He at University of Wisconsin-Madison
 *  Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */
#include <iostream>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sstream>
#include <fstream>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#include <ctime>
#include <locale>


#include "Logger.h"
using namespace std;

Logger::Logger(const char *logpath)
{
    _logfile.open(logpath, ios::app);
    if ( ! _logfile.is_open() ) {
        // Something may be seriously wrong if you cannot simply
        // open this log file. Treat it seriously.
        cerr << "Cannot Open /tmp/WorkloadPlayer.log" 
             << strerror(errno) << endl;
        exit(1);
    }
}

Logger::~Logger()
{
    _logfile.close();
}

void
Logger::write(const char *msg)
{
    if ( ! _logfile.is_open() ) {
        return;
    }

    std::locale::global(std::locale());
    std::time_t t = std::time(NULL);
    char mbstr[100];
    std::strftime(mbstr, 100, "%x-%X ", std::localtime(&t));

    _logfile << mbstr << msg << endl;
    _logfile.flush();
}


//int main()
//{
    //Logger *logger = new Logger("/tmp/logger.log");

    //logger->write("hello log");
    //logger->write("hello log2");

    //delete logger;
//}



