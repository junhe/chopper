# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import multiprocessing
import Queue
import time
from multiprocessing.managers import SyncManager
import exp_executor
import pprint
import sys
import socket
import random

PORTNUM=8848
AUTHKEY='11'
nodeinfo=None

def experiment_worker(treatment):
    """
    This function simple take one job (a treatment)
    and return the result as a dict
    """
    df = exp_executor.exp_exe.run_and_get_df( treatment, 
                                         savedf = False )
    return df

def batch_worker(shared_job_q, shared_result_q):
    """
    This function takes a batch of jobs from 
    the job and and work on them one by one. 
    Then the result to shared_result_q together
    """
    myhostname = '.'.join(socket.gethostname().split('.')[0:2])
    nodeinfo = 'WORKERINFO ['+str(myhostname)+']:'
    print nodeinfo, 'start'
    sys.stdout.flush()
    while True:
        batchjobs = []
        
        fetchsize = 1 # get one job group at a time 
        for i in range(fetchsize):
            # we wait for a while,
            # if no other jobs, we do a smaller batch
            try:
                # decompose the groups to jobs and 
                # put them to batchjobs
                group = shared_job_q.get(block=True, timeout=2)
                print nodeinfo, 'Grabbed group', group['groupid'], \
                        'with', len(group['joblist']), 'jobs'
                sys.stdout.flush()
                for job in group['joblist']:
                    batchjobs.append( job )
            except Queue.Empty:
                break
            except  EOFError:
                print nodeinfo, 'master is closed'
                sys.stdout.flush()
                time.sleep(1)
                break
            except:
                exit(0)

        results = []
        for treatment in batchjobs:
            #results.append(1)
            #continue

            df = experiment_worker( treatment )
            result_pack = {
                            'treatment':treatment,
                            'response.data.frame'       :df.toDic()
                          }
            results.append( result_pack )
            #print nodeinfo, "just finished", treatment
        
        for result in results:
            shared_result_q.put( result )

        if len(results) > 0:
            print nodeinfo, myhostname, 'just finished', \
                    len(results), 'jobs'
            sys.stdout.flush()

def runclient(masterip):
    manager = make_client_manager(masterip, PORTNUM, AUTHKEY)
    job_q = manager.get_job_q()
    result_q = manager.get_result_q()
    batch_worker(job_q, result_q)


def make_client_manager(ip, port, authkey):
    """ Create a manager for a client. This manager connects to a server on the
        given address and exposes the get_job_q and get_result_q methods for
        accessing the shared queues from the server.
        Return a manager object.
    """
    class ServerQueueManager(SyncManager):
        pass

    ServerQueueManager.register('get_job_q')
    ServerQueueManager.register('get_result_q')

    manager = ServerQueueManager(address=(ip, port), authkey=authkey)
    manager.connect()

    print nodeinfo, 'Client connected to %s:%s' % (ip, port)
    return manager


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'usage:', sys.argv[0], 'masterip'
        exit(0)
    masterip = sys.argv[1]
    runclient(masterip)


