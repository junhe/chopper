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
    def __init__(self, confparser):
        "confparser must be ready to use get()"
        self.confparser = confparser
       
        ############################
        # Setup Env of Walkman

        # Set jobid
        self.confparser.set('system','hostname', socket.gethostname())
        self.confparser.set('system','jobid', 
            self.confparser.get('system','hostname') + "-" +
            time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))

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
        print "making fragments....."
        if self.confparser.get('fragment', 'createfragment').lower() == 'yes':
            self.makeFragmentsOnFS()


    def wrapper(self):
        """
        SetupEnv()
        RecordStatus()
        workload.Run()
        RecordStatus()
        """
        self.RecordWalkmanConfig()

        self.SetupEnv()
        self.RecordStatus()
        
        # Run workload

        self.RecordStatus()


def test0001_parameters():
    settingtable = [] # each row is a dictionary
    dict = {"nyears":1
            "nseasons_per_year":1,
            "np":1,
            "ndir_per_pid":1,
            "nfile_per_dir":1,
            "nwrites_per_file":1024,
            "wsize":1024,
            "wstride":1024,
            "fsync_per_write":True}
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
    
    #settingtable = getWorkloadParameters()
    settingtable = test0001_parameters()
    betadist_parameters = [
            [-1,-1]
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


