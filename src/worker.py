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
IP='127.0.0.1'
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
    myhostname = socket.gethostname().split('.')[0]
    nodeinfo = 'WORKERINFO ['+str(myhostname)+']:'
    while True:
        batchjobs = []
        
        #batchsize = random.randint(10,20)
        batchsize = 1
        for i in range(batchsize):
            # we wait for a while,
            # if no other jobs, we do a smaller batch
            try:
                batchjobs.append(
                    shared_job_q.get(block=True, timeout=2)) 
            except Queue.Empty:
                break
            except  EOFError:
                print nodeinfo, 'master is closed'
                time.sleep(1)
                break
            except:
                exit(0)

        results = []
        for treatment in batchjobs:
            #results.append(1)
            #continue

            print nodeinfo, myhostname, treatment
            df = experiment_worker( treatment )
            #result_pack = {
                            #'treatment':treatment,
                            #'df'       :df.toDic()
                          #}
            results.append( df.toDic() )
        
        for result in results:
            shared_result_q.put( result )

        if len(results) > 0:
            print nodeinfo, myhostname, 'just finished', \
                    len(results), 'jobs'

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


