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
import itertools

def ParameterCominations(parameter_dict):
    """
    Get all the cominbation of the values from each key
    http://tinyurl.com/nnglcs9

    Input: parameter_dict={
                    p0:[x, y, z, ..],
                    p1:[a, b, c, ..],
                    ...}
    Output: [
             {p0:x, p1:a, ..},
             {..},
             ...
            ]
    """
    d = parameter_dict
    return [dict(zip(d, v)) for v in itertools.product(*d.values())]


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
                 ld = self.confparser.get('system','resultdir'),
                 filesystem = self.confparser.get('system', 'filesystem')) # logdir

    def _remake_fs(self):
        fs = self.confparser.get('system', 'filesystem')
        if fs == 'ext4':
            self._remakeExt4()
        elif fs == 'xfs':
            self._remakeXFS()
        elif fs == 'btrfs':
            self._remakeBtrfs()

    def _remakeBtrfs(self):
        blockscount = self.confparser.getint('system', 'blockscount')
        blocksize = self.confparser.getint('system', 'blocksize')
            
        loodevsizeBytes = blockscount*blocksize
        if self.confparser.get('system', 'makeloopdevice') == 'yes':
            MWpyFS.FormatFS.makeLoopDevice(
                    devname=self.confparser.get('system', 'partition'),
                    tmpfs_mountpoint=self.confparser.get('system', 'tmpfs_mountpoint'),
                    sizeMB=loodevsizeBytes)

        if not os.path.exists(self.confparser.get('system','mountpoint')):
            os.makedirs(self.confparser.get('system','mountpoint'))

        MWpyFS.FormatFS.btrfs_remake(partition  =self.confparser.get('system','partition'),
                                   mountpoint   =self.confparser.get('system','mountpoint'),
                                   username     =self.confparser.get('system','username'),
                                   groupname    =self.confparser.get('system','groupname'),
                                   nbytes       =loodevsizeBytes)

    def _remakeXFS(self):
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

        MWpyFS.FormatFS.remakeXFS(partition  =self.confparser.get('system','partition'),
                                   mountpoint =self.confparser.get('system','mountpoint'),
                                   username   =self.confparser.get('system','username'),
                                   groupname   =self.confparser.get('system','groupname'),
                                   blocksize=blocksize)

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
        assert self.confparser.get('system', 'filesystem') == 'ext4'
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
        #subprocess.call(['sync'])
        if self.confparser.get('system', 'filesystem') == 'xfs':
            MWpyFS.FormatFS.remountFS(devname=self.confparser.get('system', 'partition'),
                                      mountpoint=self.confparser.get('system', 'mountpoint'))
            MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'partition'))
            MWpyFS.FormatFS.mountXFS(self.confparser.get('system', 'partition'),
                                     self.confparser.get('system', 'mountpoint'))

            time.sleep(1) # TODO: find a better way to make sure all logs
                          # are replayed.
        elif self.confparser.get('system', 'filesystem') == 'btrfs':
            MWpyFS.FormatFS.remountFS(devname=self.confparser.get('system', 'partition'),
                                      mountpoint=self.confparser.get('system', 'mountpoint'))
            time.sleep(1)

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
            f.write( str(self.monitor.dumpfsSummary() ))

    def _SetupEnv(self):
        # Make loop device
        if self.confparser.get('system', 'makeloopdevice') == 'yes'\
                and self.confparser.get('system', 'formatfs') != 'yes':
            exit(1)

        # Format file system
        if self.confparser.get('system', 'formatfs').lower() == "yes":
            self._remake_fs()
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

        self._SetupEnv()
        self._RecordStatus(year=0, season=0) # always record the inital status

        for year in range(nyear):
            for season in range(nseasons_per_year):
                # Run workload
                ret = self._play_test(ext4debug=False)
                #ret = self._play_ibench(year=year, season=season)

                #do not record faulty status of the file system
                #however, sometimes it is useful to record faulty ones
                if ret == 0:
                    self._RecordStatus(year=year,season=season+1)

    def _play_ibench(self, year, season):
        ret = pyWorkload.tools.run_ibench(1, 
                                    "{year}.{season}".format(year=year, season=season), 
                                    self.confparser.get("system", "mountpoint"))
        return ret

    def _play_test(self, ext4debug=False):
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
            fsync_per_write = self.confparser.getint('workload', 'fsync_per_write'),
            fsync_before_close
                            = self.confparser.getint('workload', 'fsync_before_close')
            )

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]

        # turn on ext4 debug if necessary
        if self.confparser.get('system', 'filesystem') == 'ext4' \
           and ext4debug == True:
            MWpyFS.FormatFS.enable_ext4_mballoc_debug(True)
            MWpyFS.FormatFS.send_dmesg("Turned on mballoc debug. MARKER_MBALLOC_ON")

        proc = subprocess.Popen(cmd) 
        proc.wait()

        # turn on ext4 debug if necessary
        if self.confparser.get('system', 'filesystem') == 'ext4'  \
            and ext4debug == True:
            MWpyFS.FormatFS.enable_ext4_mballoc_debug(True)
            MWpyFS.FormatFS.send_dmesg("Turned off mballoc debug. MARKER_MBALLOC_OFF")

        return proc.returncode

class Troops:
    """
    Troops is just to make this testing framework more *layered*.
    Now we can do:
        Troops
            ...
            loop:
                modify workload
                play workload by passing confparser to walkman
                    for year:
                        for season:
                            walkman.play(year, season)
            ...

    The nice thing about Troop is that the confparser contents
    will be saved to resultdir, and later be merged with other
    results in R. So you can see the configure of each result 
    entry. 

    The bad thing about Troops is that I has to use workload Producer
    to generate the workload, so that it can only be used for workload
    that can be generated by Producer. Two ways to solve this:
        1. make the producer more powerful and make confparser more
            expressive
        2. Make workload file a parameter of Walkman, add one or more
            options to confparser to describe each workload.
    """
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

    def _test006(self):
        paradict = {
                'nwrites_per_file': [1, 3, 1024],
                'w_hole'          : [0, 1, 4096, 1024*1024 ],
                'wsize'           : [1, 1024, 
                                     4096-1, 4096, 4096+1
                                    ],
                'fsync_per_write' : [0, 1]
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            para['fsync_before_close'] = 1 # to maintain compatibility
        #pprint.pprint( paralist )

        return paralist

    def _test007(self):
        # 4KB, 8KB, 16KB, ...16MB 
        exps = range(0, 15)
        sizes = [4096*(2**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 256, 512, 1024],
                'w_hole'          : [0, 1] + sizes,
                'wsize'           : [1, 1024, 
                                     4096-1, 4096, 4096+1, 8*1024
                                    ],
                'fsync_per_write' : [0, 1]
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            para['fsync_before_close'] = 1 # to maintain compatibility

        pprint.pprint( paralist )

        return paralist

    def _test008(self):
        # 4KB, 8KB, 16KB, ...16MB 
        exps = range(0, 15)
        sizes = [4096*(2**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 64, 256, 1024],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : [1, 256, 1024, 
                                     4096-1, 4096, 4096+1, 8*1024
                                    ],
                'fsync_per_write' : [0, 1]
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            para['fsync_before_close'] = 1 # to maintain compatibility

        pprint.pprint( paralist )

        return paralist

    def _test009(self):
        # 4KB, 8KB, 16KB, ...16MB 
        exps = range(0, 15)
        sizes = [4096*(2**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 64, 1024],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : [1, 256, 1024, 4096],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [0, 1, 2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test010(self):
        "Test larger write sizes"
        exps = range(0, 15)
        sizes = [4096*(4**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 64, 1024],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : sizes,
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [0, 1, 2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test010sanity(self):
        "Test larger write sizes"
        exps = range(0, 5)
        sizes = [4096*(4**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 64, 1024],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : [1024] + sizes,
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [0, 1, 2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist



    def _test012(self):
        "test the weird group 0 write"
        paradict = {
                'nwrites_per_file': [3],
                'w_hole'          : [1*1024*1024],
                'wsize'           : [1],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [1] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test013(self):
        exps = range(0, 15)
        sizes = [4096*(4**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3, 64, 1024],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : sizes,
                'nfile_per_dir'   : [2],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [0, 1, 2] 
                }

        #paradict = {
                #'nwrites_per_file': [3],
                #'w_hole'          : [1024],
                #'wsize'           : [4096],
                #'nfile_per_dir'   : [2],
                ## 0: only fsync() before closing
                ## 1: fsync() after each write
                ## 2: no fynsc() during open-close
                #'fsync' : [2] 
                #}

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test014(self):

        #paradict = {
                #'nwrites_per_file': [10240],
                #'w_hole'          : [4096],
                #'wsize'           : [4096],
                #'nfile_per_dir'   : [2],
                ## 0: only fsync() before closing
                ## 1: fsync() after each write
                ## 2: no fynsc() during open-close
                #'fsync' : [1] 
                #}

        paradict = {
                'nwrites_per_file': [1, 3, 64, 1024, 4096, 1024*512],
                'w_hole'          : [1024, 4096],
                'wsize'           : [1, 4096],
                'nfile_per_dir'   : [1],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [0, 1, 2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test015(self):
        exps = range(0, 15)
        sizes = [4096*(4**x) for x in exps]

        paradict = {
                'nwrites_per_file': [1, 3],
                'w_hole'          : [0, 1, 512, 1024, 2048] + sizes,
                'wsize'           : [4096],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [1] 
                }
        #paradict = {
                #'nwrites_per_file': [1],
                #'w_hole'          : [2048],
                #'wsize'           : [4096],
                ## 0: only fsync() before closing
                ## 1: fsync() after each write
                ## 2: no fynsc() during open-close
                #'fsync' : [1] 
                #}

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test016(self):
        "temp tests"
        paradict = {
                'nwrites_per_file': [64],
                'w_hole'          : [256*1024*1024],
                'wsize'           : [4*1024],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [1] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test017(self):
        "where the directory data is?"
        paradict = {
                'nwrites_per_file': [1],
                'w_hole'          : [0],
                'wsize'           : [4096],
                'nfile_per_dir'   : [1000],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test018(self):
        paradict = {
                'nwrites_per_file': [3],
                'w_hole'          : [256*1024*1024],
                'wsize'           : [4096],
                'nfile_per_dir'   : [1],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _test018(self):
        paradict = {
                'nwrites_per_file': [2],
                'w_hole'          : [1024*1024 - 2*4096],
                'wsize'           : [4096],
                'nfile_per_dir'   : [1],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [2] 
                }

        paralist = ParameterCominations(paradict)

        # Translate to list of dictionary
        for para in paralist:
            # Calc stride
            stride = para['w_hole'] + para['wsize']
            para['wstride'] = stride

            #Calc fsync
            if para['fsync'] == 0:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 1
            elif para['fsync'] == 1:
                para['fsync_per_write'] = 1
                para['fsync_before_close'] = 0
            elif para['fsync'] == 2:
                para['fsync_per_write'] = 0
                para['fsync_before_close'] = 0
            else:
                print "invalid fsync"
                exit(0)

        pprint.pprint( paralist )

        return paralist

    def _march_parameter_table(self):
        return self._test018()

    def march(self):
        """
        change self.confparser here
        It would be a good idea to touch every option in
        confparser, even though it is not changed here.
        Otherwise, you might accidentally leave a value
        unchanged in the near future. 
        """
        cparser = self.confparser
        paralist = self._march_parameter_table()

        for para in paralist:
            for k,v in para.items():
                cparser.set( 'workload', str(k), str(v) )
            
            self._walkman_walk(cparser)
            
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
   
    troops = Troops(confparser)
    troops.march()

    #walkman = Walkman(confparser, 'recorder')
    #walkman._RecordStatus(0, 0)

if __name__ == "__main__":
    main(sys.argv)


