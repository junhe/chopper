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
#ifndef __WorkloadPlayer_H__
#define __WorkloadPlayer_H__

#include <map>
#include <fstream>

class WorkloadEntry;

// WorkloadPlayer grabs a workload entry and execute it 
class WorkloadPlayer {
    public:
        void play( const WorkloadEntry &wl_entry );

        WorkloadPlayer();
        ~WorkloadPlayer();
        
        std::ofstream _logfile;
        
        // member vars
        std::map<std::string, int> _path2fd_dict; // hole opened file's fd
    private:
        void logwrite(std::string msg);
};

#endif

