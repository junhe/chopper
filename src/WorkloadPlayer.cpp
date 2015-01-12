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


#include "WorkloadFetcher.h"
#include "WorkloadPlayer.h"
#include "Util.h"

using namespace std;

WorkloadPlayer::WorkloadPlayer()
{
    _logfile.open("/tmp/WorkloadPlayer.log", ios::app);
    if ( ! _logfile.is_open() ) {
        // Something may be seriously wrong if you cannot simply
        // open this log file. Treat it seriously.
        cerr << "Cannot Open /tmp/WorkloadPlayer.log" << strerror(errno) << endl;

        exit(1);
    }
}

WorkloadPlayer::~WorkloadPlayer()
{
    if ( _logfile.is_open() ) {
        _logfile.close();
    }
}


void
WorkloadPlayer::logwrite(std::string msg)
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


void
WorkloadPlayer::play( const WorkloadEntry &wl_entry )
{
    if (wl_entry.isHEAD())
        return;
   
    //cout << "OPERATION:" << wl_entry._operation << "EOF" << endl;
    if ( wl_entry._operation == "mkdir" ) {
        // make dir
        //cout << "mkdir" << endl;

        //string cmd = "mkdir -p ";
        //cmd += wl_entry._path;
        //string ret = Util::exec(cmd.c_str());
        int ret = mkdir(wl_entry._path.c_str(), 0777);
        if ( ret == -1 ) {
            //logwrite( wl_entry._entry_str + " Failed to mkdir.");
            ostringstream oss;
            oss << wl_entry._entry_str << " Failed to mkdir.";
            oss << " error msg:" << strerror(errno);
            logwrite(oss.str());
            exit(1);
        }
    } else if ( wl_entry._operation == "open" ) {
        // open file
        int fd = open( wl_entry._path.c_str(), O_CREAT|O_RDWR, 0666);
        if ( fd == -1 ) {
            ostringstream oss;
            oss << wl_entry._entry_str << " Failed to open file.";
            oss << " error msg:" << strerror(errno);
            logwrite(oss.str());
            exit(1);
        } else {
            //cout << wl_entry._path << " opened" << endl;
            _path2fd_dict[wl_entry._path] = fd; 
        }
    } else if ( wl_entry._operation == "close" ) {
        // close file
        //cout << "closing...." << endl;
        if ( _path2fd_dict.count(wl_entry._path) == 0 ) {
            cerr << "File to be closed is not open" << endl;
            logwrite( wl_entry._entry_str + " File to be closed is not open.");
            exit(1);
        }
        int fd = _path2fd_dict[wl_entry._path];
        int ret = close(fd);
        if (ret == -1) {
            perror(wl_entry._path.c_str());
            logwrite( wl_entry._entry_str + " Failed to close file.");
            exit(1);
        }
    } else if ( wl_entry._operation == "write" ) {
        //cout << "writing..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be written is not open" << endl;
            logwrite( wl_entry._entry_str + " File to be written is not open.");
            exit(1);
        }
        assert( wl_entry._tokens.size() == 5 );
        // Now it is safe
        int fd = it->second; // for short
        off_t offset;
        size_t length;
        istringstream( wl_entry._tokens[3] ) >> offset;
        istringstream( wl_entry._tokens[4] ) >> length;

        //cout << fd << "PWRITE: " << offset << " " << length << endl;

        // allocate buffer
        char * buf = (char *)malloc(length);
        if ( buf == NULL ) {
            logwrite( wl_entry._entry_str + " Failed to allocate mem buf.");
            exit(1);
        }
        
        size_t remain = length;
        off_t  cur_off = offset;
        while ( remain > 0 ) {
            int ret = pwrite(fd, buf, remain, cur_off);
            if ( ret != int(remain) ) {
                ostringstream oss;
                oss << "ret=" << ret << ", remain=" << remain << ", cur_off=" << cur_off;
                if ( ret == -1 ) {
                    oss << " error msg:" << strerror(errno);
                }
                logwrite( wl_entry._entry_str + " " + oss.str());
                if ( ret == -1 ) {
                    exit(1);
                }
            }
            remain -= ret;
            cur_off += ret;
        }
        free(buf);
    } else if ( wl_entry._operation == "read" ) {
        //cout << "reading..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be read is not open" << endl;
            logwrite( wl_entry._entry_str + " File to be read is not open.");
            exit(1);
        }
        assert( wl_entry._tokens.size() == 5 );
        // Now it is safe
        int fd = it->second; // for short
        off_t offset;
        size_t length;
        istringstream( wl_entry._tokens[3] ) >> offset;
        istringstream( wl_entry._tokens[4] ) >> length;

        // allocate buffer
        char * buf = (char *)malloc(length);
        if ( buf == NULL ) {
            logwrite( wl_entry._entry_str + " Failed to allocate mem buf.");
            exit(1);
        }

        size_t remain = length;
        off_t  cur_off = offset;
        while ( remain > 0 ) {
            int ret = pread(fd, buf, remain, cur_off);
            if ( ret != int(length) ) {
                ostringstream oss;
                oss << "ret=" << ret << ", remain=" << remain << ", cur_off=" << cur_off;
                if ( ret == -1 ) {
                    oss << " error msg:" << strerror(errno);
                }
                logwrite( wl_entry._entry_str + " " + oss.str());
                if ( ret == -1 ) {
                    exit(1);
                }
            }
            remain -= ret;
            cur_off += ret;

            if ( ret == 0 ) {
                // the read reached the end of file.
                // we break here to avoid infinite loop
                break;
            }
        }
        free(buf);
    } else if ( wl_entry._operation == "fsync" ) {
        //cout << "fsyncing..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be fsync is not open" << endl;
            logwrite( wl_entry._entry_str + " File to be fsync is not open.");
            exit(1);
        }
        // Now it is safe
        int fd = it->second; // for short
        int ret = fsync(fd);
        if ( ret == -1 ) {
            ostringstream oss;
            oss << wl_entry._entry_str << " error msg:" << strerror(errno);
            logwrite(oss.str());
            exit(1); // so serious?
        }
    } else if ( wl_entry._operation == "rm" ) {
        string cmd = "rm -rf ";
        cmd += wl_entry._path;
        string ret = Util::exec(cmd.c_str());
        if ( ret == "ERROR" ) {
            logwrite( wl_entry._entry_str + " File to remove file.");
            exit(1);
        }
        //cout << ret;
    } else if ( wl_entry._operation == "sync" ) {
        sync(); // This never fails
        //string cmd = "sync";
        //string ret = Util::exec(cmd.c_str());
        //if ( ret == "ERROR" ) {
            //logwrite( wl_entry._entry_str + " Faile sync os.");
            //exit(1);
        //}
        //cout << ret;
    } else if ( wl_entry._operation == "sched_setaffinity" ) {
        int cpuid;

        istringstream( wl_entry._tokens[3] ) >> cpuid;
        int ret = Util::set_to_cpu(cpuid);

        //ostringstream oss;
        //oss << sched_getcpu();
        //logwrite( "current cpu:" + oss.str() );
        if ( ret == -1 ) {
            logwrite( wl_entry._entry_str + " Fail to setaffinity.");
            exit(1);
        }

    } else {
        logwrite( wl_entry._entry_str + "Unrecognized Operation in play()" );
        exit(1);
    }

    return;
}




