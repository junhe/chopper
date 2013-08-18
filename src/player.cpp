#include <iostream>
#include <mpi.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>

#include "WorkloadFetcher.h"
#include "WorkloadPlayer.h"

using namespace std;

// I need this class to:
// At rank0: 
//  fetch workload entries from file
//  send workload entries to all PEs, includeing rank0
// At rank 1~n-1:
//  receive and execute entry
//
// Note that this class does NOT do MPI_init() and 
// MPI_finalize(). You need to use this class between them.
class WorkloadDispatcher {
    public:
        void run();
        WorkloadDispatcher(int rank, int np, string wl_path, int bufsz=512);
        ~WorkloadDispatcher();
    private:
        int _rank;
        int _np;
        size_t _bufsize; // buf to be send between ranks
        WorkloadPlayer _wl_player;
        
        // this is only for rank0
        WorkloadFetcher *_fetcher; 
};

WorkloadDispatcher::WorkloadDispatcher(int rank, int np, string wl_path, int bufsz)
    : _rank(rank), _np(np), _bufsize(bufsz)
{
    if ( _rank == 0 ) {
        _fetcher = new WorkloadFetcher(1000, wl_path.c_str());
    } else {
        _fetcher = NULL;
    }
}

WorkloadDispatcher::~WorkloadDispatcher()
{
    if ( _fetcher != NULL )
        delete _fetcher;
}


void
WorkloadDispatcher::run()
{
    char *comm_buf = (char *) malloc(_bufsize);
    assert(comm_buf != NULL);

    if ( _rank == 0 ) {
        WorkloadEntry wl_entry;
        int flag = 1; // 1: one more job to do
                      // 0: nothing to do
        while (_fetcher->fetchEntry(wl_entry) == 1) {
            cout << wl_entry._entry_str << "---" 
                << wl_entry._tokens.size() << "==" << wl_entry.isHEAD() << "Pid" << wl_entry._pid
                << endl;

            if ( !wl_entry.isHEAD() && wl_entry._pid == 0) {
                // It is rank0's job
                _wl_player.play(wl_entry);
            } else {
                // It is rank 1~(n-1) 's job
                
                // compose a serialized entry
                string enstr = wl_entry._entry_str;
                assert( enstr.size()+1 < _bufsize );
                strcpy(comm_buf, enstr.c_str());
              
                // tell receiver a job is coming
                MPI_Send(&flag, 1, MPI_INT, 
                        wl_entry._pid, 1, MPI_COMM_WORLD);
                // Send it out
                MPI_Send(comm_buf, _bufsize, MPI_CHAR, 
                        wl_entry._pid, 1, MPI_COMM_WORLD);

            }
        }
        
        cout << "fetched all entries from workload file" << endl;
        int dest_rank;
        flag = 0;
        for ( dest_rank = 1 ; dest_rank < _np ; dest_rank++ ) {
            MPI_Send(&flag, 1, MPI_INT, dest_rank, 1, MPI_COMM_WORLD);
        }
    } else {
        int flag;
        MPI_Status stat;
        
        while (true) {
            // get the flag and decide what to do
            MPI_Recv( &flag, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, &stat );
            cout << "rank:" << _rank << " flag:" << flag << endl;
            if ( flag == 1 ) {
                // have a workload entry to play
                MPI_Recv( comm_buf, _bufsize, MPI_CHAR,
                        0, 1, MPI_COMM_WORLD, &stat );

                string bufstr = comm_buf;
                cout << "bufstr:" << bufstr << endl;
                WorkloadEntry wl_entry(bufstr);

                _wl_player.play(wl_entry);
            } else {
                // nothing to do, the end
                break; // don't do return, comm_buf needs to be freed
            }
        }
    }

    free(comm_buf);
}



int main(int argc, char **argv)
{
    int rank, size;

    MPI_Init (&argc, &argv);/* starts MPI */
    MPI_Comm_rank (MPI_COMM_WORLD, &rank);/* get current process id */
    MPI_Comm_size (MPI_COMM_WORLD, &size);/* get number of processes */

    WorkloadDispatcher wl_disp (rank, size, 
            "/home/junhe/workdir/metawalker/src/pyWorkload/workload001");
    wl_disp.run();

    cout << "Hello" << endl;

    MPI_Finalize();

    //WorkloadFetcher wf(1000, "/home/junhe/workdir/metawalker/src/pyWorkload/workload001");
    
    //WorkloadPlayer wl_player;
    //WorkloadEntry wl_entry;
    
    //while (wf.fetchEntry(wl_entry) == 1) {
        //cout << wl_entry._entry_str << "---" 
            //<< wl_entry._tokens.size() << "==" << wl_entry.isHEAD() << "Pid" << wl_entry._pid
            //<< endl;
        //wl_player.play(wl_entry);
    //}

    //cout << "end of program" << endl;
    return 0;
}



