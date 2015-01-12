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
        WorkloadDispatcher(int rank, int np, string wl_path, int bufsz=4096);
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

    long long cnt = 0;
    if ( _rank == 0 ) {
        WorkloadEntry wl_entry;
        int flag = 1; // 1: one more job to do
                      // 0: nothing to do
        while (_fetcher->fetchEntry(wl_entry) == 1) {
            //cout << wl_entry._entry_str << "---" 
                //<< wl_entry._tokens.size() << "==" << wl_entry.isHEAD() << "Pid" << wl_entry._pid
                //<< endl;

            if ( !wl_entry.isHEAD() && wl_entry._pid == 0) {
                // It is rank0's job
                _wl_player.play(wl_entry);
                //cout << "rank:" << _rank << " job:" << wl_entry._entry_str << endl;
                if (cnt % 1000 == 0)
                    cout << "." ;
                cnt++;
            } else {
                // It is rank 1~(n-1) 's job
                
                // compose a serialized entry
                string enstr = wl_entry._entry_str;
                if ( enstr.size()+1 > _bufsize ) {
                    cout << "size of " << enstr << " " << enstr.size() << "+1<" 
                        << _bufsize << endl;
                    //MPI_Finalize();
                    exit(1);
                }
                strcpy(comm_buf, enstr.c_str());
              
                // tell receiver a job is coming
                MPI_Send(&flag, 1, MPI_INT, 
                        wl_entry._pid, 1, MPI_COMM_WORLD);
                // Send it out
                MPI_Send(comm_buf, _bufsize, MPI_CHAR, 
                        wl_entry._pid, 1, MPI_COMM_WORLD);

            }
        }
        
        //cout << "fetched all entries from workload file" << endl;
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
            //cout << "rank:" << _rank << " flag:" << flag << endl;
            if ( flag == 1 ) {
                // have a workload entry to play
                MPI_Recv( comm_buf, _bufsize, MPI_CHAR,
                        0, 1, MPI_COMM_WORLD, &stat );

                string bufstr = comm_buf;
                //cout << "rank:" << _rank << " job:" << bufstr << endl;
                if (cnt % 1000 == 0)
                    cout << "." ;
                cnt++;
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

    if ( argc != 2 ) {
        if ( rank == 0 )
            cout << "usage: mpirun -np N " << argv[0] << " workload-file" << endl;
        MPI_Finalize();
        return 1;
    }


    WorkloadDispatcher wl_disp (rank, size, argv[1]); 
    wl_disp.run();

    MPI_Finalize();
    return 0;
}



