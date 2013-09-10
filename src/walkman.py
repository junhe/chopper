# walkman is the driver/integrator of the MetaWalker.
# the workflow is like:
#   0. format the whole system
#   1. genearate workloads by Producer
#   2. For each workload:
#       2. play workload by player
#       3. monitor the FS status
# 
#
# Possible ways to make more fragments:
#   1. delete previous files
#   2. append previous files
import subprocess
import MWpyFS
import pyWorkload
import time
import shutil
import os
import socket
import sys
from ConfigParser import SafeConfigParser
import itertools
import pprint

class Walkman:
    def __init__(self, confparser):
        "confparser must be ready to use get()"
        self.confparser = confparser

        self.confparser.set('system','hostname', socket.gethostname())
        self.confparser.set('system','jobid', 
            self.confparser.get('system','hostname') + "-" +
            time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))

        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))
        self.confparser.set('system','resultdir', 
                "./results." + self.confparser.get('system','hostname') + '/')
        if not os.path.exists(self.confparser.get('system','resultdir')):
            os.makedirs(self.confparser.get('system','resultdir'))

        # monitor
        self.monitor = MWpyFS.Monitor.FSMonitor(self.confparser.get('system','partition'), 
                                                 self.confparser.get('system','mountpoint'),
                                                 ld = self.confparser.get('system','resultdir')) # logdir
        # producer
        self.wl_producer = pyWorkload.producer.Producer()


    def displayandsaveConfig(self):
        colwidth = 30
        conflogpath = os.path.join(self.confparser.get('system','resultdir'),
                    "walkmanJOB-"+self.confparser.get('system','jobid')+".conf")

        header_items = []
        data_items = []
        
        for section_name in self.confparser.sections():
            print '[',section_name,']'
            for name, value in self.confparser.items(section_name):
                print '  %s = %s' % (name.ljust(colwidth), value.ljust(colwidth))
                header_items.append(name)
                data_items.append(value)
            print

        with open(conflogpath+".rows", 'w') as f: 
            self.confparser.write(f)

        header = [ str(x).ljust(colwidth) for x in header_items ]
        header = " ".join(header) + "\n"
        datas = [ str(x).ljust(colwidth) for x in data_items ]
        datas = " ".join(datas) + "\n"

        with open(conflogpath+".cols", 'w') as f:
            f.write(header+datas)

    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.confparser.get('system','devname'),
                mountpoint=self.confparser.get('system','mountpoint'), 
                confpath=self.confparser.get('system','diskconf'), 
                username=self.confparser.get('system','username'),
                groupname=self.confparser.get('system','groupname'))

    def remakeExt4(self):
        blockscount = self.confparser.getint('system', 'blockscount')
        blocksize = self.confparser.getint('system', 'blocksize')
            
        loodevsizeMB = blockscount*blocksize/(1024*1024)

        if self.confparser.get('system', 'makeloopdevice') == 'yes':
            MWpyFS.FormatFS.makeLoopDevice(
                    devname=self.confparser.get('system', 'partition'),
                    tmpfs_mountpoint=self.confparser.get('system', 'tmpfs_mountpoint'),
                    sizeMB=loodevsizeMB)

        MWpyFS.FormatFS.remakeExt4(partition  =self.confparser.get('system','partition'),
                                   mountpoint =self.confparser.get('system','mountpoint'),
                                   username   =self.confparser.get('system','username'),
                                   groupname   =self.confparser.get('system','groupname'),
                                   blockscount=blockscount,
                                   blocksize=blocksize)
    def makeFragmentsOnFS(self):
        MWpyFS.mkfrag.makeFragmentsOnFS(
                partition=self.confparser.get('system', 'partition'),
                mountpoint=self.confparser.get('system', 'mountpoint'),
                alpha=self.confparser.getfloat('fragment', 'alpha'),
                beta=self.confparser.getfloat('fragment', 'beta'),
                sumlimit=self.confparser.getint('fragment', 'sum_limit'),
                seed=self.confparser.getint('fragment', 'seed'),
                tolerance=self.confparser.getfloat('fragment', 'tolerance'))

    #def produceWorkload_rmdir(self, rootdir):
        #self.wl_producer.produce_rmdir(np=self.confparser.get('system','np'),
                                       #ndir_per_pid=self.ndir_per_pid,
                                       #rootdir=self.mountpoint+rootdir,
                                       #tofile=self.workloadbufpath)

    def produceWorkload(self, rootdir):
        self.wl_producer.produce(np=self.confparser.getint('workload','np'), 
            startOff=self.confparser.getint('workload','startOff'),
            nwrites_per_file = self.confparser.getint('workload','nwrites_per_file'), 
            nfile_per_dir=self.confparser.getint('workload','nfile_per_dir'), 
            ndir_per_pid=self.confparser.getint('workload','ndir_per_pid'),
            wsize=self.confparser.getint('workload','wsize'), 
            wstride=self.confparser.getint('workload','wstride'), 
            rootdir=os.path.join(self.confparser.get('system','mountpoint')+rootdir),
            tofile=self.confparser.get('system','workloadbufpath'))
    def play(self):
        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def getrootdirByIterIndex(self, i):
        rootdir = "season"+str(i).zfill(3)+"/"   #TODO: fix the "/" must thing
        return rootdir

    def getYearSeasonStr(self, year, season):
        return "year"+str(year).zfill(5)+\
                    ".season"+str(season).zfill(5)
    def getLogFilenameBySeasonYear(self, season, year):
        return "walkmanJOB-"+self.confparser.get('system','jobid')+\
                ".result.log." + self.getYearSeasonStr(year, season)

    def displayFreeFrag():
        e2ff = self.monitor.e2freefrag()
        print e2ff[0]
        print e2ff[1]
        return 

    def walk(self):
        """
        This is the main function of walkman. It takes a
        ConfigParser as input, run a walkman for this input.
        By doing so, I can pass different config to walkman
        to make it do different things, making walkman a better module.
        """
        self.displayandsaveConfig()

        if self.confparser.get('system', 'makeloopdevice') == 'yes'\
                and self.confparser.get('system', 'formatfs') != 'yes':
            print "you asked to make loop device without formatting FS. i cannot do this"
            exit(1)

        if self.confparser.get('system', 'formatfs').lower() == "yes":
            self.remakeExt4()
        else:
            print "skipped formating fs"

        # save the fs summary so I can traceback if needed
        fssumpath = os.path.join(self.confparser.get('system', 'resultdir'),
                        "walkmanJOB-"+self.confparser.get('system','jobid')+".FS-summary")
        with open(fssumpath, 'w') as f:
            f.write( self.monitor.dumpfsSummary())

        # Making fragments oh year~
        print "making fragments....."
        if self.confparser.get('fragment', 'createfragment').lower() == 'yes':
            self.makeFragmentsOnFS()

        # for short
        NYEARS = self.confparser.getint('workload','nyears')
        NSEASONS_PER_YEAR = self.confparser.getint('workload', 'nseasons_per_year')
        
        print "start looping..."
        for y in range(NYEARS):
            for s in range(NSEASONS_PER_YEAR):
                self.monitor.display(savedata=True, 
                                    logfile=self.getLogFilenameBySeasonYear(s,y),
                                    monitorid=self.getYearSeasonStr(year=y, season=s),
                                    jobid=self.confparser.get('system','jobid')
                                    )


                rootdir = self.getrootdirByIterIndex(s)
                self.produceWorkload(rootdir=rootdir)

                self.play()
     
                # now, delete the previous dir if it exists
                pre_s = (s - (NSEASONS_PER_YEAR-1))%NSEASONS_PER_YEAR
                pre_s_rootdir = self.getrootdirByIterIndex(pre_s)
                fullpath = os.path.join(self.confparser.get('system', 'mountpoint'),
                                pre_s_rootdir)
                try:
                    print "removing ", fullpath
                    shutil.rmtree(fullpath)
                except:
                    print "failed to rmtree (but should be OK):", fullpath

                print "------ End of this year, sleep 2 sec ----------"

        # monitor the last
        self.monitor.display(savedata=True, 
                            logfile=self.getLogFilenameBySeasonYear(999,999),
                            monitorid=self.getYearSeasonStr(year=999, season=999),
                            jobid=self.confparser.get('system','jobid')
                            )



def product(elems):
    prd = 1
    for x in elems:
        prd *= x
    return prd

def getWorkloadParameters():
    targetsize = 1*1024*1024*1024
    nseasons=[4]
    np = [1,4,8]
    ndir_per_pid = [1,4,8]
    nfiles_per_dir = [1,4,16]
    nwrites_per_file = [1024, 4096]
    wstride_factors = ["contigous", "onewritehole"]
    #wsize = 
    #wstride = 


    parameters = [nseasons, np, ndir_per_pid, 
                  nfiles_per_dir, nwrites_per_file, wstride_factors]
    paralist = list(itertools.product(*parameters))

    settingtable = [] # each row is a dictionary
    cnt = 0
    for para in paralist:
        print cnt
        cnt += 1
        para = list(para)
        totaldirs = product(para[0:3])
        totalfiles = product(para[0:4])
        totalwrites = product(para[0:5])

        wsize = targetsize/totalwrites
        if para[5] == "contigous":
            wstride = wsize
        else:
            wstride = wsize*2
        para[5] = wstride
        
        #print para, "totaldirs:", totaldirs, "totalfiles:", \
                #totalfiles, "totalwrites:", totalwrites, "wsize:", \
                #wsize, "wstride:", wstride,\
                #"aggfilesize:", product(para)

        dict = {"nseasons_per_year":para[0]+1,
                "np":para[1],
                "ndir_per_pid":para[2],
                "nfile_per_dir":para[3],
                "nwrites_per_file":para[4],
                "wsize":wsize,
                "wstride":wstride}
        # trim several unrealistic bad ones
        #if wsize > 1*1024*1024:
            #print "Skip this...."
            #continue

        settingtable.append(dict)

    return settingtable

def dict2conf(conf, section_name, dict):
    for key,name in dict.iteritems():
        print key, name
        conf.set(section_name, str(key), str(name))

def main(args):
    if len(args) != 2:
        print 'usage:', args[0], 'config-file'
        exit(1)
    
    confpath = args[1]
    confparser = SafeConfigParser()
    try:
        confparser.readfp(open(confpath, 'r'))
    except:
        print "unable to read config file:", confpath
        exit(1)
    
    settingtable = getWorkloadParameters()
    betadist_parameters = [
            [10,2],
            [5,2],
            [2,5],
            [5,5],
            [1,1],
            [2,10]
            ]
    for para in settingtable:
        for alpha, beta in betadist_parameters:
            confparser.set('fragment', 'alpha', str(alpha))
            confparser.set('fragment', 'beta', str(beta))
            dict2conf(confparser, "workload", para)

            walkman = Walkman(confparser)
            walkman.walk()
            exit(1)

if __name__ == "__main__":
    main(sys.argv)


