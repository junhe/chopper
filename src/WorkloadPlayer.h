#ifndef __WorkloadPlayer_H__
#define __WorkloadPlayer_H__

#include <map>

class WorkloadEntry;

// WorkloadPlayer grabs a workload entry and execute it 
class WorkloadPlayer {
    public:
        void play( const WorkloadEntry &wl_entry );

        WorkloadPlayer();
        ~WorkloadPlayer();
        
        ofstream _logfile;
        
        // member vars
        std::map<std::string, int> _path2fd_dict; // hole opened file's fd
    private:
        void logwrite(std::string msg);
};

#endif

