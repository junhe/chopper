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
#ifndef __WorkloadFetcher_H__
#define __WorkloadFetcher_H__

#include <queue>
#include <fstream>

class WorkloadEntry {
    public:
        std::string _entry_str;
        std::vector<std::string> _tokens;
        pid_t       _pid;
        std::string _path;
        std::string _operation;

        void setEntry(const std::string &line);
        bool isHEAD() const;
        WorkloadEntry(){};
        WorkloadEntry(const std::string &line);
    private:
        bool setItemCache();
};

class WorkloadFetcher
{
    public:
        int fetchEntry(WorkloadEntry &entry); // only interface

        WorkloadFetcher(int bsize, const char *workloadpath);
        ~WorkloadFetcher();
    private:
        std::ifstream _workloadStream;
        std::queue <WorkloadEntry> _entryBuf;
        int _bufSize; // if _bufSize is 0, then read

        int readEntryFromStream(WorkloadEntry &entry);
        int fillBuffer();
};

#endif

