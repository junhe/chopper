#ifndef __LOGGER_H_
#define __LOGGER_H_

#include <fstream>


class Logger
{
    public:
        Logger(const char *logpath);
        ~Logger();
        void write(const char *msg);
    private:
        std::ofstream _logfile;
};

#endif

