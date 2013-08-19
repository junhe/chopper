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

#include "WorkloadFetcher.h"
#include "WorkloadPlayer.h"
#include "Util.h"

using namespace std;

void
WorkloadPlayer::play( const WorkloadEntry &wl_entry )
{
    if (wl_entry.isHEAD())
        return;
   
    //cout << "OPERATION:" << wl_entry._operation << "EOF" << endl;
    if ( wl_entry._operation == "mkdir" ) {
        // make dir
        //cout << "mkdir" << endl;
        string cmd = "mkdir -p ";
        cmd += wl_entry._path;
        string ret = Util::exec(cmd.c_str());
    } else if ( wl_entry._operation == "open" ) {
        // open file
        int fd = open( wl_entry._path.c_str(), O_CREAT|O_RDWR, 0666);
        if ( fd == -1 ) {
            perror(wl_entry._path.c_str());
            exit(1);
        } else {
            cout << wl_entry._path << " opened" << endl;
            _path2fd_dict[wl_entry._path] = fd; 
        }
    } else if ( wl_entry._operation == "close" ) {
        // close file
        //cout << "closing...." << endl;
        if ( _path2fd_dict.count(wl_entry._path) == 0 ) {
            cerr << "File to be closed is not open" << endl;
            exit(1);
        }
        int fd = _path2fd_dict[wl_entry._path];
        int ret = close(fd);
        if (ret == -1) {
            perror(wl_entry._path.c_str());
            exit(1);
        }
    } else if ( wl_entry._operation == "write" ) {
        //cout << "writing..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be written is not open" << endl;
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
        assert( buf != NULL );

        int ret = pwrite(fd, buf, length, offset);
        free(buf);
        assert(ret == (int)length);
    } else if ( wl_entry._operation == "read" ) {
        //cout << "reading..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be read is not open" << endl;
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
        assert( buf != NULL );

        int ret = pread(fd, buf, length, offset);
        free(buf);
        assert(ret == (int)length);
    } else if ( wl_entry._operation == "fsync" ) {
        //cout << "fsyncing..." << endl;
        map<string, int>::const_iterator it;
        it = _path2fd_dict.find( wl_entry._path );
        if ( it == _path2fd_dict.end() ) { 
            cerr << "File to be fsync is not open" << endl;
            exit(1);
        }
        // Now it is safe
        int fd = it->second; // for short
        fsync(fd);
    } else if ( wl_entry._operation == "rm" ) {
        string cmd = "rm -rf ";
        cmd += wl_entry._path;
        string ret = Util::exec(cmd.c_str());
        //cout << ret;
    } else {
        cerr << "Unrecognized Operation in play()" << endl;
    }

    return;
}




