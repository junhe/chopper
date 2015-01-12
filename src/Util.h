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
#ifndef __Util_H__
#define __Util_H__

#include <vector>
#include <map>

#ifndef MAP_NOCACHE
// this is a way to tell mmap not to waste buffer cache.  since we just
// read the index files once sequentially, we don't want it polluting cache
// unfortunately, not all platforms support this (but they're small)
#define MAP_NOCACHE 0
#endif


class Util {
    public:
        static ssize_t WriteN(const void *vptr, size_t n, int fd);
        static int Open(const char *fname, int flag);
        static int Close(int fd);
        static int Flush(int fd);
        static int set_to_cpu(int cpuid);
        static void replaceSubStr( std::string del, 
                                   std::string newstr, 
                                   std::string &line, int startpos = 0 );
        static struct timeval Gettime();
        static double GetTimeDurAB(struct timeval a,
                                   struct timeval b);
        static off_t GetFileSize(int fd);
        static void *GetDataBuf(int fd, size_t length);
        static std::vector<std::string> GetIndexFiles(const char *dirpath);
        static std::vector<std::string> GetDirFilenames(const char *dirpath);
        static std::vector<std::string> split(const std::string &s, char delim);
        static std::vector<std::string> &split(const std::string &s, 
                                                char delim, 
                                                std::vector<std::string> &elems);
        static std::string exec(const char* cmd);
};

class Performance {
    public:
        std::map<std::string, std::vector<std::string> > _data;
        int _colwidth; // column width
        
        void put(const char *key, const char *val);
        void put(const char *key, int val);
        void put(const char *key, double val);
        void put(const char *key, float val);
        std::string showColumns();

        Performance(int colwidth=15);
};


#endif

