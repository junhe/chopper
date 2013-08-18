#include <iostream>
#include <mpi.h>

#include "WorkloadFetcher.h"

using namespace std;

int main(int argc, char **argv)
{
    WorkloadFetcher wf(1000, "/home/junhe/workdir/metawalker/src/pyWorkload/workload.sample");
    WorkloadEntry we;
    wf.fetchEntry(we);

    cout << "end of program" << endl;
    return 0;
}



