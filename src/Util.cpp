#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string>
#include <time.h>
#include <sys/time.h>
#include <map>
#include <iostream>
#include <sstream>
#include <fstream>
#include <iomanip>
#include <assert.h>
#include <sys/mman.h>
#include <sys/statvfs.h>
#include <stdlib.h>
#include <dirent.h>

#include "Util.h"

using namespace std;


/////////////////////////////////////////////////////////////////////////////
// Util

// Write n bytes from vptr to fd
// returns n or returns -err ( if < n is written, it is an error )
ssize_t
Util::WriteN(const void *vptr, size_t n, int fd)
{
    size_t      nleft;
    ssize_t     nwritten;
    const char  *ptr;
    ptr = (const char *)vptr;
    nleft = n;
    int ret   = n;
    while (nleft > 0) {
        if ( (nwritten = write(fd, ptr, nleft)) <= 0) {
            if (nwritten < 0 && nwritten != -EINTR) {
                ret = nwritten;   /* error! */
                break;
            }
        }
        nleft -= nwritten;
        ptr   += nwritten;
    }
    return ret;
}


int
Util::Open(const char *fname, int flag)
{
    return open(fname, flag, 0666);
}

int
Util::Close(int fd)
{
    return close(fd);
}

int
Util::Flush(int fd)
{
    return fsync(fd);
}

void
Util::replaceSubStr( string del, string newstr, string &line, int startpos) 
{
    size_t found;
    
    found = line.find(del, startpos);
    while (found != string::npos) 
    {
        line.replace(found, del.size(), newstr);  
        found = line.find(del, startpos);
    }
}

struct timeval 
Util::Gettime()
{
    struct timeval t;
    gettimeofday(&t, NULL);
    return t;
}

double
Util::GetTimeDurAB(struct timeval a,
                   struct timeval b)
{
    struct timeval dur;
    timersub(&b, &a, &dur);
    return dur.tv_sec + dur.tv_usec/1000000.0;
}

off_t
Util::GetFileSize(int fd)
{
    return lseek(fd, 0, SEEK_END);
}

void *
Util::GetDataBuf(int fd, size_t length) 
{
    void *b;

    b = mmap(NULL, length, PROT_READ, MAP_SHARED|MAP_NOCACHE, fd, 0);
    if (b == MAP_FAILED) {
        return NULL;
    } else {
        return b;
    }
}

vector<string>
Util::GetIndexFiles(const char *dirpath)
{
    vector<string> fnames, index_files;
    fnames = GetDirFilenames(dirpath);

    // filter out the non-index files
    vector<string>::iterator it;
    for ( it = fnames.begin();
          it != fnames.end();
          ++it )
    {
        if ( it->find("dropping.index.") == 0 ) {
            index_files.push_back(*it);
        }
    }
    
    return index_files;
}


vector<string>
Util::GetDirFilenames(const char *dirpath)
{
    DIR *dpdf;
    struct dirent *epdf;
    vector<string> fnames;

    dpdf = opendir(dirpath);
    if (dpdf != NULL){
       while ( (epdf = readdir(dpdf)) ){
          fnames.push_back( string(epdf->d_name) );
       }
    }
    return fnames; 
}

/////////////////////////////////////////////////////////////////////////////
// Performance

Performance::Performance(int colwidth)
    :_colwidth(colwidth)
{
}

string 
Performance::showColumns()
{
    ostringstream oss;
    map<string, vector<string> >::iterator it;

    // print header
    vector<string>::size_type maxdepth = 0;
    for ( it = _data.begin() ;
          it != _data.end() ;
          ++it )
    {
        oss << setw(_colwidth) << it->first << " ";
        if ( maxdepth < it->second.size() ) {
            maxdepth = it->second.size();
        }
    }
    oss << "MYHEADERROWMARKER" << endl;

    // print performance data
    //
    vector<string>::size_type i;
    for ( i = 0 ; i < maxdepth ; i++ ) {
        for ( it = _data.begin() ;
              it != _data.end() ;
              ++it )
        {
            vector<string> &vals = it->second; // for short
            assert(vals.size() == maxdepth);
            oss << setw(_colwidth) << vals.at(i) << " ";
        }
    }
    oss << "DATAROWMARKER" << endl;
    return oss.str();
}

void 
Performance::put(const char *key, const char *val)
{
    string keystr = string(key);
    if (_data.count(keystr) == 0) {
        _data[keystr] = vector<string>();
    }
    _data[keystr].push_back( string(val) );
}

void
Performance::put(const char *key, int val)
{
    ostringstream oss;
    oss << val;
    put(key, oss.str().c_str());
}

void
Performance::put(const char *key, double val)
{
    ostringstream oss;
    oss << val;
    put(key, oss.str().c_str());
}

void
Performance::put(const char *key, float val)
{
    ostringstream oss;
    oss << val;
    put(key, oss.str().c_str());
}


