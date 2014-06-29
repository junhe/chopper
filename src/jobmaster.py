import multiprocessing
import Queue
import time
from multiprocessing.managers import SyncManager
import pyWorkload
import pprint
import MWpyFS
import os
import sys

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
                #fourbyfour_iter('./designs/blhd-12-factors-4by4.txt')
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

def runserver_locality(resultpath, jobtag, arg_usefinished):
    # Start a shared manager server and access its queues
    manager = make_server_manager(PORTNUM, AUTHKEY)
    shared_job_q = manager.get_job_q()
    shared_result_q = manager.get_result_q()

    resultpath = resultpath + '-' + jobtag

    # whether we should continue the previous
    # unfinished jobs?
    finished_joblist = []
    finishedpath = resultpath+'.finished'
    if os.path.isfile(finishedpath):
        #choice = \
                #raw_input(finishedpath+" exist, use it? [y|n]")
        print 'OPTION arg_usefinished:', arg_usefinished
        if arg_usefinished == 'usefinished':
            choice = 'y'
        elif arg_usefinished == 'notusefinished':
            choice = 'n'
        else:
            print 'wrong arg for arg_usefinished'
            exit(1)

        f_finished_job = open(finishedpath, 'r+')
        if choice == 'y':
            for line in f_finished_job:
                finished_joblist.append(int(line.strip()))

            fresult = open(resultpath, 'a')
            hasheader = True
        else:
            f_finished_job.truncate()
            print "finished_joblist will be not used."\
                    " new finished jobs will put in it"
            f_finished_job.flush()
            
            # open result file
            fresult = open(resultpath, 'w')
            fresult.truncate()
            hasheader = False
        time.sleep(1)
    else:
        fresult = open(resultpath, 'w')
        fresult.truncate()
        hasheader = False
        f_finished_job = open(finishedpath, 'w+')
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
            df.addColumn(key="jobtag", value=jobtag)
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
                    'job_total', job_total, 'resultcnt', resultcnt, \
                    'at', resultpath, '***',
            print 'polled, no result this time. sleep for a while ...'
            time.sleep(2)

    time.sleep(2)
    manager.shutdown()
    f_finished_job.close()
    fresult.close()

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
    if len(sys.argv) != 4:
        print "Usage:", sys.argv[0], "resultpath jobtag usefinished|notusefinished"
        exit(1)
    resultpath = sys.argv[1]
    jobtag = sys.argv[2]
    arg_usefinished = sys.argv[3]
    runserver_locality(resultpath, jobtag, arg_usefinished)


