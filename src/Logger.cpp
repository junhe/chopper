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



