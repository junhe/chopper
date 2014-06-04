import multiprocessing
import Queue
import time
from multiprocessing.managers import SyncManager
import pyWorkload
import pprint
import MWpyFS
import os

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


def get_joblist():
    jobiter = pyWorkload.exp_design.\
                fourbyfour_iter('./designs/blhd-12-factors-4by7.txt')
                #fourbyfour_iter('./designs/blhd-11-factors-4by7.txt')
                #fourbyfour_iter('./designs/design_blhd-4by4.tmp.txt')
                #fourbyfour_iter('./design_blhd-4by4.txt')
    joblist = list(jobiter) 
    for id, treatment in enumerate(joblist):
        treatment['jobid'] = id

    return joblist


def remove_finished_jobs(joblist, finished_joblist ):
    ret_joblist = [treatment for treatment in joblist \
                    if not (treatment['jobid'] in finished_joblist)]
    return ret_joblist

def groupby_signature( joblist ):
    """
    structure of one group:
        {
            'groupid':
            'joblist':[treatment1, treatment2....]
        }
    """
    jobbuckets = {} 
    for treatment in joblist:
        signature = ( 
                treatment['filesystem'],
                treatment['disksize'],
                treatment['disk_used'],
                treatment['layoutnumber']
                )
        #signature = ( 
                #str(treatment)
                #)
        if not jobbuckets.has_key(signature):
            jobbuckets[signature] = [ treatment ]
        else:
            jobbuckets[signature].append( treatment )
    jobgroups = []
    for id, (sig, joblist) in enumerate(jobbuckets.items()):
        d = {
                'groupid'  :id,
                'signature':sig,
                'joblist'  :joblist
            }
        #print sig
        jobgroups.append(d)
    #pprint.pprint( jobgroups ) 
    #print jobbuckets
    #print jobgroups
    return jobgroups


def runserver_locality():
    # Start a shared manager server and access its queues
    manager = make_server_manager(PORTNUM, AUTHKEY)
    shared_job_q = manager.get_job_q()
    shared_result_q = manager.get_result_q()

    # whether we should continue the previous
    # unfinished jobs?
    finished_joblist = []
    f_finished_job = open('finished_joblist.txt', 'r+')
    if os.path.isfile('finished_joblist.txt'):
        choice = \
                raw_input("finished_joblist.txt exist, use it? [y|n]")

        if choice == 'y':
            for line in f_finished_job:
                finished_joblist.append(int(line.strip()))

            fresult = open('aggarated_results.txt', 'a')
            hasheader = True
        else:
            f_finished_job.truncate()
            print "finished_joblist will be not used."\
                    " new finished jobs will put in it"
            f_finished_job.flush()
            
            # open result file
            fresult = open('aggarated_results.txt', 'w')
            fresult.truncate()
            hasheader = False
        time.sleep(1)
    else:
        exclude_finished_jobs = False

    joblist = get_joblist()
    print 'finished_joblist', finished_joblist
    joblist = remove_finished_jobs(joblist, finished_joblist)
    jobgroups = groupby_signature( joblist )
    #pprint.pprint( jobgroups )
    #exit(0)

    # put all job groups into job queue
    job_total = 0
    for group in jobgroups:
        job_total += len( group['joblist'] )
        #print group['groupid'], len(group['joblist'])
        shared_job_q.put( group )
    #pprint.pprint( jobgroups )
    print 'All groups have been put into job queue'

    resultcnt = 0
    while resultcnt < job_total: 
        # some results have not been returned

        # grab to local list
        local_results = []
        while not shared_result_q.empty():
            try:
                r = shared_result_q.get(block=True, timeout=1)
                local_results.append( r )
                resultcnt += 1
                #print 'total groups:', len(jobgroups), \
                        #job_total', job_total, 'resultcnt', resultcnt
            except Queue.Empty:
                break

        # put results to file
        for result_pack in local_results:
            dfdic = result_pack['response.data.frame']
            treatment = result_pack['treatment']

            result_jobid = treatment['jobid']
            df = MWpyFS.dataframe.DataFrame() 
            df.fromDic(dfdic)
            if hasheader:
                fresult.write( df.toStr(header=False, table=True) )
            else:
                fresult.write( df.toStr(header=True, table=True) )
                hasheader = True
            fresult.flush()

            f_finished_job.write( str(result_jobid) + '\n')
            f_finished_job.flush()
        if len(local_results) > 0:
            print 'Wow, just got', len(local_results), 'results from workers'
        else:
            print '*** total groups:', len(jobgroups), \
                    'job_total', job_total, 'resultcnt', resultcnt, '***',
            print 'polled, no result this time. sleep for a while ...'
            time.sleep(2)

    time.sleep(2)
    manager.shutdown()
    f_finished_job.close()
    fresult.close()


def runserver():
    # Start a shared manager server and access its queues
    manager = make_server_manager(PORTNUM, AUTHKEY)
    shared_job_q = manager.get_job_q()
    shared_result_q = manager.get_result_q()


    #jobiter = pyWorkload.exp_design.onefile_iter2()
    jobiter = pyWorkload.exp_design.\
                fourbyfour_iter('./designs/blhd-11-factors-4by7.txt')
                #fourbyfour_iter('./designs/design_blhd-4by4.tmp.txt')
                #fourbyfour_iter('./design_blhd-4by4.txt')
    alldispatched = False
    jobid = 0
    resultcnt = 0
    job_dispatched_unfinished = set()
    if os.path.isfile('finished_joblist.txt'):
        choice = \
                raw_input("finished_joblist.txt exist, use it? [y|n]")
        if choice == 'y':
            exclude_finished_jobs = True
            print "finished_joblist will be used"
        else:
            exclude_finished_jobs = False
            print "finished_joblist will be not used"
        time.sleep(1)
    else:
        exclude_finished_jobs = False

    # finished_joblist.txt will store the jobid
    # that has been finished so far. And it will add
    # more jobid to it as more runs have been done.
    # If the user chooses not to use the joblist file
    # the contents of the file will be overwritten by
    # the new finished jobs
    f_finished_job = open('finished_joblist.txt', 'r+')
    finished_joblist = []
    if exclude_finished_jobs:
        # fill the list, and not do them later
        # new finished job ids will be added to it
        # this list will later be saved to the file
        for line in f_finished_job:
            finished_joblist.append(int(line.strip()))
    else:
        f_finished_job.truncate()
    print finished_joblist
    #exit(0)

    if exclude_finished_jobs == True:
        fresult = open('aggarated_results.txt', 'a')
        hasheader = True
    else:
        fresult = open('aggarated_results.txt', 'w')
        hasheader = False

    while not (alldispatched == True \
               and len(job_dispatched_unfinished)==0):
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
                job['jobid'] = jobid

                if not jobid in finished_joblist:
                    shared_job_q.put( job )
                    print 'last dispatched jobid', jobid, 'resultcnt', resultcnt
                    job_dispatched_unfinished.add(jobid)
                jobid += 1
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
                print 'last dispatched jobid',jobid, 'resultcnt', resultcnt
            except Queue.Empty:
                break
        for result_pack in local_results:
            dfdic = result_pack['response.data.frame']
            treatment = result_pack['treatment']

            result_jobid = treatment['jobid']
            job_dispatched_unfinished.remove(result_jobid)
            #pprint.pprint(treatment)
            df = MWpyFS.dataframe.DataFrame() 
            df.fromDic(dfdic)
            if hasheader:
                fresult.write( df.toStr(header=False, table=True) )
            else:
                fresult.write( df.toStr(header=True, table=True) )
                hasheader = True
            fresult.flush()

            f_finished_job.write( str(result_jobid) + '\n')
            f_finished_job.flush()
        if len(local_results) > 0:
            print "dispatched unfinished jobs:", job_dispatched_unfinished

    time.sleep(2)
    manager.shutdown()
    f_finished_job.close()

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
    runserver_locality()


