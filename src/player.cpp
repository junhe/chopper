#include <iostream>
#include <mpi.h>

#include "WorkloadFetcher.h"
#include "WorkloadPlayer.h"

using namespace std;

int main(int argc, char **argv)
{
    WorkloadFetcher wf(1000, "/home/junhe/workdir/metawalker/src/pyWorkload/workload.sample");
    
    WorkloadPlayer wl_player;
    WorkloadEntry wl_entry;
    
    while (wf.fetchEntry(wl_entry) == 1) {
        cout << wl_entry._entry_str << "---" 
            << wl_entry._tokens.size() << "==" << wl_entry.isHEAD() << "Pid" << wl_entry._pid
            << endl;
        wl_player.play(wl_entry);
    }

    cout << "end of program" << endl;
    return 0;
}



