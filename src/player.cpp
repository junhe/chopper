#include <iostream>
#include <mpi.h>

#include "WorkloadFetcher.h"

using namespace std;

int main(int argc, char **argv)
{
    WorkloadFetcher wf(1000, "/home/junhe/workdir/metawalker/src/pyWorkload/workload.sample");
    
    WorkloadEntry we;
    
    while (wf.fetchEntry(we) == 1) {
        cout << we._entry_str << "---" 
            << we._tokens.size() << "==" << we.isHEAD() << "Pid" << we._pid
            << endl;
    }

    cout << "end of program" << endl;
    return 0;
}



