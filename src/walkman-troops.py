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
        _SetupEnv()
        _RecordStatus()
        workload.Run()
        _RecordStatus()

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
        resultdir_prefix = self.confparser.get('system', 'resultdir_prefix')
        resultdir = "results." + self.confparser.get('system','hostname') 
        self.confparser.set('system', 'resultdir', 
                os.path.join(resultdir_prefix, resultdir) )
        if not os.path.exists(self.confparser.get('system','resultdir')):
            os.makedirs(self.confparser.get('system','resultdir'))

        # set workload buf, where we put the tmp workload file.
        # You'd better put the workload buf to memory file systems, 
        # We need it fast.
        # We need hostname to make it unique.
        self.confparser.set('system','workloadbufpath', 
               os.path.join(self.confparser.get('system', 'workloaddir'),
                 "_workload.buf." + self.confparser.get('system', 'hostname')))

        ############################
        # Setup Monitor

        # monitor
        self.monitor = MWpyFS.Monitor.FSMonitor(
                 self.confparser.get('system','partition'), 
                 self.confparser.get('system','mountpoint'),
                 ld = self.confparser.get('system','resultdir')) # logdir



    def _remakeExt4(self):
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

    def _makeFragmentsOnFS(self):
        MWpyFS.mkfrag.makeFragmentsOnFS(
                partition=self.confparser.get('system', 'partition'),
                mountpoint=self.confparser.get('system', 'mountpoint'),
                alpha=self.confparser.getfloat('fragment', 'alpha'),
                beta=self.confparser.getfloat('fragment', 'beta'),
                sumlimit=self.confparser.getint('fragment', 'sum_limit'),
                seed=self.confparser.getint('fragment', 'seed'),
                tolerance=self.confparser.getfloat('fragment', 'tolerance'))

    def _getYearSeasonStr(self, year, season):
        return "year"+str(year).zfill(5)+\
                    ".season"+str(season).zfill(5)

    def _getLogFilenameBySeasonYear(self, season, year):
        return "walkmanJOB-"+self.confparser.get('system','jobid')+\
                ".result.log." + self._getYearSeasonStr(year, season)

    def _RecordWalkmanConfig(self):
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

    def _RecordStatus(self, year, season):
        self.monitor.display(savedata=True, 
                    logfile=self._getLogFilenameBySeasonYear(season,year),
                    monitorid=self._getYearSeasonStr(year=year, season=season),
                    jobid=self.confparser.get('system','jobid')
                    )
    def _RecordFSSummary(self):
        # save the fs summary so I can traceback if needed
        fssumpath = os.path.join(self.confparser.get('system', 'resultdir'),
                        "walkmanJOB-"+self.confparser.get('system','jobid')+".FS-summary")
        with open(fssumpath, 'w') as f:
            f.write( self.monitor.dumpfsSummary())

    def _SetupEnv(self):
        # Make loop device
        if self.confparser.get('system', 'makeloopdevice') == 'yes'\
                and self.confparser.get('system', 'formatfs') != 'yes':
            exit(1)

        # Format file system
        if self.confparser.get('system', 'formatfs').lower() == "yes":
            self._remakeExt4()
        else:
            print "skipped formating fs"

        # Making fragments
        if self.confparser.get('fragment', 'createfragment').lower() == 'yes':
            print "making fragments....."
            self._makeFragmentsOnFS()

    def walk(self):
        self._wrapper()
    
    def _wrapper(self):
        """
        _SetupEnv()
        workload.Run()
        _RecordStatus()
        """
        self._RecordWalkmanConfig()

        nyear = self.confparser.getint('workload', 'nyears')
        nseasons_per_year = self.confparser.getint('workload', 'nseasons_per_year')
        for year in range(nyear):
            for season in range(nseasons_per_year):
                self._SetupEnv()
                
                # Run workload
                self._play_test()

                self._RecordStatus(year=year,season=season)

    def _play_test(self):
        """
        Generate the workload based on the config file, and then
        play it by our external player
        """
        wl_producer = pyWorkload.producer.Producer()

        wl_producer.produce(
            np              = self.confparser.getint('workload', 'np'),
            startOff        = self.confparser.getint('workload', 'startOff'),
            nwrites_per_file= self.confparser.getint('workload', 'nwrites_per_file'),
            nfile_per_dir   = self.confparser.getint('workload', 'nfile_per_dir'),
            ndir_per_pid    = self.confparser.getint('workload', 'ndir_per_pid'),
            wsize           = self.confparser.getint('workload', 'wsize'),
            wstride         = self.confparser.getint('workload', 'wstride'),
            rootdir         = os.path.join(self.confparser.get('system','mountpoint')),
            tofile          = self.confparser.get('system','workloadbufpath'),
            fsync_per_write = self.confparser.get('workload', 'fsync_per_write')
            )

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

class Troops:
    def __init__(self, confparser):
        """
        Note that the config parser in Troops
        is mostly for system config, the workload config
        is very likely to be changed in Troops (and
        that's what Troops is designed for.
        """
        self.confparser = confparser 

    def _walkman_walk(self, cf):
        walkman = Walkman(cf, 'fromTroops')
        walkman.walk()

    def march(self):
        "change self.confparser here"
        cparser = self.confparser
        for nwrites_per_file in range (1, 3):
            cparser.set('nwrites_per_file', nwrites_per_file)
            _walkman_walk(cparser)
            
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
    
    walkman = Walkman(confparser, 'trial')
    walkman.walk()

if __name__ == "__main__":
    main(sys.argv)


