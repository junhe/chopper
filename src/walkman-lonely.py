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
    """
    Ideally, Walkman class should be just a wrapper. It 
    setups environment for the workload, monitors and 
    records the status of the system. It is like:
    WRAPPER:
        SetupEnv()
        RecordStatus()
        workload.Run()
        RecordStatus()

    One walkman should just have just one run.
    """
    def __init__(self, confparser, jobcomment=""):
        "confparser must be ready to use get()"
        self.confparser = confparser
       
        ############################
        # Setup Env of Walkman

        # Set jobid
        self.jobcomment = jobcomment
        self.confparser.set('system','hostname', socket.gethostname())
        self.confparser.set('system','jobid', 
            self.confparser.get('system','hostname') + "-" +
            time.strftime("%Y-%m-%d-%H-%M-%S" + "-" +
            self.jobcomment, time.localtime()))

        # Set resultdir and make the dir
        self.confparser.set('system','resultdir', 
                "./results." + self.confparser.get('system','hostname') + '/')
        if not os.path.exists(self.confparser.get('system','resultdir')):
            os.makedirs(self.confparser.get('system','resultdir'))

        ############################
        # Setup Monitor

        # monitor
        self.monitor = MWpyFS.Monitor.FSMonitor(self.confparser.get('system','partition'), 
                                                 self.confparser.get('system','mountpoint'),
                                                 ld = self.confparser.get('system','resultdir')) # logdir

    def RecordWalkmanConfig(self):
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

    def remakeExt4(self):
        blockscount = self.confparser.getint('system', 'blockscount')
        blocksize = self.confparser.getint('system', 'blocksize')
            
        loodevsizeMB = blockscount*blocksize/(1024*1024)


        if self.confparser.get('system', 'makeloopdevice') == 'yes':
            MWpyFS.FormatFS.makeLoopDevice(
                    devname=self.confparser.get('system', 'partition'),
                    tmpfs_mountpoint=self.confparser.get('system', 'tmpfs_mountpoint'),
                    sizeMB=loodevsizeMB)


        if not os.path.exists(self.confparser.get('system','mountpoint')):
            os.makedirs(self.confparser.get('system','mountpoint'))

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

    def getYearSeasonStr(self, year, season):
        return "year"+str(year).zfill(5)+\
                    ".season"+str(season).zfill(5)

    def getLogFilenameBySeasonYear(self, season, year):
        return "walkmanJOB-"+self.confparser.get('system','jobid')+\
                ".result.log." + self.getYearSeasonStr(year, season)

    def RecordStatus(self, year, season):
        self.monitor.display(savedata=True, 
                    logfile=self.getLogFilenameBySeasonYear(season,year),
                    monitorid=self.getYearSeasonStr(year=year, season=season),
                    jobid=self.confparser.get('system','jobid')
                    )

    def SetupEnv(self):
        # Make loop device
        if self.confparser.get('system', 'makeloopdevice') == 'yes'\
                and self.confparser.get('system', 'formatfs') != 'yes':
            exit(1)

        # Format file system
        if self.confparser.get('system', 'formatfs').lower() == "yes":
            self.remakeExt4()
        else:
            print "skipped formating fs"

        # Making fragments
        if self.confparser.get('fragment', 'createfragment').lower() == 'yes':
            print "making fragments....."
            self.makeFragmentsOnFS()


    def wrapper(self):
        """
        SetupEnv()
        RecordStatus()
        workload.Run()
        RecordStatus()
        """
        if self.jobcomment == 'test001':
            self.wrapper_test001()
        elif self.jobcomment == 'test002':
            self.wrapper_test002()

    def wrapper_test001(self):
        self.RecordWalkmanConfig()
 
        nwrites_per_file = range(60,70)
        for year in range(len(nwrites_per_file)):
            self.SetupEnv()
            self.RecordStatus(year=year,season=0)
            
            # Run workload
            self.play_test001(nwrites_per_file=nwrites_per_file[year])

            self.RecordStatus(year=year,season=1)

    def play_test001(self, nwrites_per_file):
        wl_producer = pyWorkload.producer.Producer()
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        wl_producer.produce(np=1,
            startOff=0,
            nwrites_per_file = nwrites_per_file,
            nfile_per_dir=1,
            ndir_per_pid=1,
            wsize=1024,
            wstride=1024,
            rootdir=os.path.join(self.confparser.get('system','mountpoint')),
            tofile=self.confparser.get('system','workloadbufpath'),
            fsync_per_write=True)

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test002(self):
        self.RecordWalkmanConfig()
 
        fsync_per_write = [False, True]
        for year in range(len(nwrites_per_file)):
            self.SetupEnv()
            self.RecordStatus(year=year,season=0)
            
            # Run workload
            self.play_test001(nwrites_per_file=nwrites_per_file[year])

            self.RecordStatus(year=year,season=1)

    def play_test002(self, nwrites_per_file):
        wl_producer = pyWorkload.producer.Producer()
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        wl_producer.produce(np=1,
            startOff=0,
            nwrites_per_file = nwrites_per_file,
            nfile_per_dir=1,
            ndir_per_pid=1,
            wsize=1024,
            wstride=1024,
            rootdir=os.path.join(self.confparser.get('system','mountpoint')),
            tofile=self.confparser.get('system','workloadbufpath'),
            fsync_per_write=True)

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()



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
    
    walkman = Walkman(confparser, 'test001')
    walkman.wrapper()

if __name__ == "__main__":
    main(sys.argv)


