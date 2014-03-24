import multiprocessing
import Queue
import time
from multiprocessing.managers import SyncManager
import pyWorkload
import pprint
import MWpyFS

# This jobmaster uses workload iterator to find
# jobs and put them to the job queue. The workers
# grab jobs from the queue and put the reults to the 
# result queue. When the master find the job queue
# is empty, it will use the workload iterator to
# generate more jobs.
#
# The results in the result queue will be saved
# to a single file by the master. To prevent the
# queue from taking too much memory, the info saved
# should be de-queued.


PORTNUM=8848
AUTHKEY='11'

def runserver():
    # Start a shared manager server and access its queues
    manager = make_server_manager(PORTNUM, AUTHKEY)
    shared_job_q = manager.get_job_q()
    shared_result_q = manager.get_result_q()


    fresult = open('aggarated_results.txt', 'w')
    hasheader = False

    #jobiter = pyWorkload.exp_design.onefile_iter2()
    jobiter = pyWorkload.exp_design.\
                fourbyfour_iter('./design_blhd-4by4.txt')
    alldispatched = False
    jobcnt = 0
    resultcnt = 0
    job_dispatched_unfinished = set()
    while not (alldispatched == True and jobcnt == resultcnt):
        qmax = 100 
        # Fill the job queue
        qsz = shared_job_q.qsize()
        delta = qmax - qsz
        if delta < 50 or alldispatched:
            delta = 0
        # only add job when delta is large
        for i in range(delta): 
            try:
                # job is actually a treatment
                job = jobiter.next() 
                job['jobid'] = jobcnt
                shared_job_q.put( job )
                job_dispatched_unfinished.add(jobcnt)
                jobcnt += 1
                print 'jobcnt', jobcnt, 'resultcnt', resultcnt
            except StopIteration:
                print 'alldispatched!'
                alldispatched = True
                break

        local_results = []
        # grab to local list
        while not shared_result_q.empty():
            try:
                r = shared_result_q.get(block=True, timeout=1)
                local_results.append( r )
                resultcnt += 1
                print 'jobcnt',jobcnt, 'resultcnt', resultcnt
            except Queue.Empty:
                break
        for result_pack in local_results:
            dfdic = result_pack['response.data.frame']
            treatment = result_pack['treatment']

            jobid = treatment['jobid']
            job_dispatched_unfinished.remove(jobid)
            #pprint.pprint(treatment)
            df = MWpyFS.dataframe.DataFrame() 
            df.fromDic(dfdic)
            if hasheader:
                fresult.write( df.toStr(header=False, table=True) )
            else:
                fresult.write( df.toStr(header=True, table=True) )
                hasheader = True
            fresult.flush()
        if len(local_results) > 0:
            print "dispatched unfinished jobs:", job_dispatched_unfinished

    time.sleep(2)
    manager.shutdown()

def make_server_manager(port, authkey):
    """ Create a manager for the server, listening on the given port.
        Return a manager object with get_job_q and get_result_q methods.
    """
    job_q = Queue.Queue()
    result_q = Queue.Queue()

    # This is based on the examples in the official docs of multiprocessing.
    # get_{job|result}_q return synchronized proxies for the actual Queue
    # objects.
    class JobQueueManager(SyncManager):
        pass

    JobQueueManager.register('get_job_q', callable=lambda: job_q)
    JobQueueManager.register('get_result_q', callable=lambda: result_q)

    manager = JobQueueManager(address=('', port), authkey=authkey)
    manager.start()
    print 'Server started at port %s' % port
    return manager

if __name__ == '__main__':
    runserver()


