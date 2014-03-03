import multiprocessing
import Queue
import time
from multiprocessing.managers import SyncManager
import exp_executor
import pprint

PORTNUM=8848
AUTHKEY='11'
IP='127.0.0.1'


def factorizer_worker(job_q, result_q):
    """ A worker function to be launched in a separate process. Takes jobs from
        job_q - each job a list of numbers to factorize. When the job is done,
        the result (dict mapping number -> list of factors) is placed into
        result_q. Runs until job_q is empty.
    """
    while True:
        try:
            job = job_q.get_nowait()
            result_q.put(job)
        except Queue.Empty:
            return

def mp_factorizer(shared_job_q, shared_result_q, nprocs):
    """ Split the work with jobs in shared_job_q and results in
        shared_result_q into several processes. Launch each process with
        factorizer_worker as the worker function, and wait until all are
        finished.
    """
    procs = []
    for i in range(nprocs):
        p = multiprocessing.Process(
                target=factorizer_worker,
                args=(shared_job_q, shared_result_q))
        procs.append(p)
        p.start()

    for p in procs:
        p.join()



def experiment_worker(treatment):
    """
    This function simple take one job (a treatment)
    and return the result as a dict
    """
    df = exp_executor.exp_exe.run_and_get_df( treatment, 
                                         savedf = False )
    print df.toStr()
    return df

def batch_worker(shared_job_q, shared_result_q):
    """
    This function takes a batch of jobs from 
    the job and and work on them one by one. 
    Then the result to shared_result_q together
    """
    batchsize = 2
    while True:
        batchjobs = []
        
        for i in range(batchsize):
            # we wait for a while,
            # if no other jobs, we do a smaller batch
            try:
                batchjobs.append(
                    shared_job_q.get(block=True, timeout=10)) 
            except:
                break

        results = []
        for treatment in batchjobs:
            pprint.pprint(treatment)
            df = experiment_worker( treatment )
            results.append( df.table )
        
        for result in results:
            shared_result_q.put( result )

def runclient():
    manager = make_client_manager(IP, PORTNUM, AUTHKEY)
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

    print 'Client connected to %s:%s' % (ip, port)
    return manager


if __name__ == '__main__':
    runclient()


