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
    def RecordFSSummary(self):
        # save the fs summary so I can traceback if needed
        fssumpath = os.path.join(self.confparser.get('system', 'resultdir'),
                        "walkmanJOB-"+self.confparser.get('system','jobid')+".FS-summary")
        with open(fssumpath, 'w') as f:
            f.write( self.monitor.dumpfsSummary())

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
        elif self.jobcomment == 'test003':
            self.wrapper_test003()
        elif self.jobcomment == 'test004':
            self.wrapper_test004()
        elif self.jobcomment == 'test004a':
            self.wrapper_test004a()
        elif self.jobcomment == 'test004b':
            self.wrapper_test004b()
        elif self.jobcomment == 'test005':
            self.wrapper_test005()
        elif self.jobcomment == 'test006':
            self.wrapper_test006()
        elif self.jobcomment == 'test006a':
            self.wrapper_test006a()
        elif self.jobcomment == 'test006b':
            self.wrapper_test006b()
        elif self.jobcomment == 'test007':
            self.wrapper_test007()
        elif self.jobcomment == 'test007a':
            self.wrapper_test007a()
        elif self.jobcomment == 'test007b':
            self.wrapper_test007b()
        elif self.jobcomment == 'test007c':
            self.wrapper_test007c()
        elif self.jobcomment == 'test010':
            self.wrapper_test010()
        elif self.jobcomment == 'test011':
            self.wrapper_test011()
        elif self.jobcomment == 'test011a':
            self.wrapper_test011a()
        elif self.jobcomment == 'test012':
            self.wrapper_test012()
        elif self.jobcomment == 'test013':
            self.wrapper_test013()

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
        self.RecordFSSummary()
 
        fsync_per_write = [False, True]
        for year in range(len(fsync_per_write)):
            self.SetupEnv()
            self.RecordStatus(year=year,season=0)
            
            # Run workload
            self.play_test002(fsync_per_write = fsync_per_write[year])

            self.RecordStatus(year=year,season=1)

    def play_test002(self, fsync_per_write):
        wl_producer = pyWorkload.producer.Producer()
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        wl_producer.produce(np=1,
            startOff=0,
            nwrites_per_file = 5*1024*1024,
            nfile_per_dir=1,
            ndir_per_pid=1,
            wsize=1,
            wstride=1,
            rootdir=os.path.join(self.confparser.get('system','mountpoint')),
            tofile=self.confparser.get('system','workloadbufpath'),
            fsync_per_write=fsync_per_write)

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test002b(self, do_fsync):
        nops_per_file = 512*1024
        for op in range(nops_per_file):
            run_fsbench(ndir=1,nfiles_per_dir=1,nops_per_file=1,
                        size_per_op=1, do_fsync=do_fsync, do_write=1, do_read=0, 
                        topdir=self.confparser.get("system", "mountpoint"),
                        do_append=1)

    def run_fsbench(self, ndir, nfile_per_dir, nops_per_file, 
                  size_per_op, do_fsync, do_write, do_read, topdir, do_append, cpu=""):

        taskset_wrapper = ["taskset", "0x0000000"+str(cpu)]
        cmd = ["../../extreme-benchmark/filesystem/fsbench", 
                ndir, nfile_per_dir, nops_per_file, 
                size_per_op, do_fsync, do_write, do_read, topdir, do_append]
        cmd = [str(x) for x in cmd]
        if cpu == "":
            finalcmd = cmd
        else:
            finalcmd = taskset_wrapper+cmd
        print finalcmd
        p = subprocess.Popen(finalcmd)
        p.wait()

    def wrapper_test003(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        revs = [False, True]
        for yr in range(len(revs)):
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test003(revs[yr])

            self.RecordStatus(year=yr,season=1)

    def play_test003(self, rev):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        off = 0
        sizes = [2**x for x in range(29)]
        sizes = sorted(sizes, reverse=rev)
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        for s in sizes:
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=s)
            off += s
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test004(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload

        switchcpus = [False, True]
        doflushs = [0,1]
        
        parameters = [switchcpus, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            subprocess.Popen("echo 65536 > /sys/fs/ext4/loop0/mb_stream_req", 
                    shell=True)
            time.sleep(3)

            self.RecordStatus(year=yr,season=0)
            self.play_test004(para[0], para[1])
            self.RecordStatus(year=yr,season=1)
        print paralist
    
    def play_test004(self, switchcpu, doflush):
        for i in range(2048):
            if switchcpu:
                cur_cpu = ((i%2)+1)
            else:
                cur_cpu = ""
            self.run_fsbench(ndir=1,nfile_per_dir=1,nops_per_file=1,
                        size_per_op=4096, do_fsync=doflush, do_write=1, do_read=0, 
                        topdir=self.confparser.get("system", "mountpoint"),
                        do_append=1, cpu=cur_cpu)

    def wrapper_test004a(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload

        switchcpus = ["no", "yes", "fixed"]
        doflushs = [0,1]
        
        parameters = [switchcpus, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            subprocess.Popen("echo 65536 > /sys/fs/ext4/loop0/mb_stream_req", 
                    shell=True)
            time.sleep(3)

            self.RecordStatus(year=yr,season=0)
            self.play_test004a(para[0], para[1])
            self.RecordStatus(year=yr,season=1)
        print paralist
    
    def play_test004a(self, switchcpu, doflush):
        for i in range(32):
            if switchcpu == "yes":
                cur_cpu = ((i%2)+1)
            elif switchcpu == "no":
                cur_cpu = ""
            elif switchcpu == "fixed":
                cur_cpu = "1"
            self.run_fsbench(ndir=1,nfile_per_dir=1,nops_per_file=1,
                        size_per_op=4096, do_fsync=doflush, do_write=1, do_read=0, 
                        topdir=self.confparser.get("system", "mountpoint"),
                        do_append=1, cpu=cur_cpu)

    def wrapper_test004b(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload

        switchcpus = ["no", "yes", "fixed"]
        doflushs = [0,1]
        
        parameters = [switchcpus, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            subprocess.Popen("echo 65536 > /sys/fs/ext4/loop0/mb_stream_req", 
                    shell=True)
            time.sleep(3)

            self.RecordStatus(year=yr,season=0)
            self.play_test004b(para[0], para[1])
            self.RecordStatus(year=yr,season=1)
        print paralist
    
    def play_test004b(self, switchcpu, doflush):
        for i in range(2048):
            if switchcpu == "yes":
                cur_cpu = ((i%2)+1)
            elif switchcpu == "no":
                cur_cpu = ""
            elif switchcpu == "fixed":
                cur_cpu = "1"
            self.run_fsbench(ndir=1,nfile_per_dir=1,nops_per_file=1,
                        size_per_op=4096, do_fsync=doflush, do_write=1, do_read=0, 
                        topdir=self.confparser.get("system", "mountpoint"),
                        do_append=1, cpu=cur_cpu)



    def wrapper_test005(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        strides = [4096, 2*4096]
        doflushs = [0, 1]
        parameters = [strides, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test005(para[0], para[1] )

            self.RecordStatus(year=yr,season=1)

    def play_test005(self, stride, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        off = 0
        sizes = [4096] * 1024
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        for s in sizes:
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=s)
            off += stride
            if doflush == 1:
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test006(self):
        "write backwards"
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        strides = [4096*(-1), 4096*(-2)]
        doflushs = [0, 1]
        parameters = [strides, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test006(para[0], para[1] )

            self.RecordStatus(year=yr,season=1)

    def play_test006(self, stride, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        off = 4096*31 
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        while off >= 0:
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            off += stride
            if doflush == 1:
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test006a(self):
        "write backwards"
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        strides = [4096, 2*4096]
        doflushs = [0, 1]
        parameters = [strides, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test006a(para[0], para[1] )

            self.RecordStatus(year=yr,season=1)

    def play_test006a(self, stride, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        off = 4096*31 
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        while off < 4096*64:
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            off += stride
            if doflush == 1:
                prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test006b(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        strides = [4096]
        doflushs = [0, 1]
        parameters = [strides, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test006b(para[0], para[1] )

            self.RecordStatus(year=yr,season=1)

    def play_test006b(self, stride, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        off = 4096*31 
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        while off < 4096*64:
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            off += stride

        if doflush == 1:
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()


    def wrapper_test007(self):
        "write backwards"
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        offsets = [4096*((2**x)-1) for x in range(11)]
        offsets = [0] + offsets
        doflushs = [1]

        parameters = [offsets, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test007(para[0], para[1])

            self.RecordStatus(year=yr,season=1)

        print paralist

    def play_test007(self, off, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))

        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        #time.sleep(2)
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test007a(self):
        "write backwards"
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        offsets = [4096*x for x in range(18)]
        doflushs = [0, 1]

        parameters = [offsets, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test007a(para[0], para[1])

            self.RecordStatus(year=yr,season=1)

        print paralist

    def play_test007a(self, off, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))

        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
        
        if doflush == 1:
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        #time.sleep(2)
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test007c(self):
        "write backwards"
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        syssyncs = [0,1]
        for yr in range(len(syssyncs)):
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)
            
            offs = range(35)
            offs = [4096*x for x in offs]
            for off in offs:
                self.play_test007c(off, syssyncs[yr])

            self.RecordStatus(year=yr,season=1)

    def play_test007c(self, off, syssync):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=off, len=4096)

        blockn = off / 4096

        if blockn % 2 == 0:
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()

        if syssync == 1:
            print "calling system sync"
            psync = subprocess.Popen(['sync'])
            psync.wait()
        else:
            print "no sync is called"

        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test010(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        strides = [4096*(2**x) for x in range(16)]
        doflushs = [0, 1]
        parameters = [strides, doflushs]
        paralist = list(itertools.product(*parameters))

        for yr in range(len(paralist)):
            para = list(paralist[yr])
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test010(para[0], para[1] )

            self.RecordStatus(year=yr,season=1)

    def play_test010(self, stride, doflush):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        off = 0 
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=off, len=4096)
        off += stride

        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=off, len=4096)
        off += stride

        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=off, len=4096)

        if doflush == 1:
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test011(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        nwrites = [64, 1]
        for yr in range(len(nwrites)):
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test011(nwrites[yr])

            self.RecordStatus(year=yr,season=1)

    def play_test011(self, n):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        off = 0 
        for i in range(n):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024*1024 # 8MB stride

        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        # Tail effect
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        off = 0 
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=1, off=off, len=4096)

        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        proc = subprocess.Popen(['sync'])
        proc.wait()

    def wrapper_test011a(self):
        """
        The only difference is that we don't flush the big file util 
        before close(). So that we don't use group preallocation
        """
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        nwrites = [64, 2]
        for yr in range(len(nwrites)):
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            self.play_test011a(nwrites[yr])

            self.RecordStatus(year=yr,season=1)

    def play_test011a(self, n):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        off = 0 
        for i in range(n):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024*1024 # 8MB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        # Another big file.
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        off = 0 
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=1, off=off, len=4096)
        off += 64*1024
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=1, off=off, len=4096)

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        proc = subprocess.Popen(['sync'])
        proc.wait()


    def wrapper_test012(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        for yr in range(8):
            self.SetupEnv()
            self.RecordStatus(year=yr,season=0)

            if yr == 0:
                self.play_test012_0_onlyholes()
            elif yr == 1:
                self.play_test012_1_sameopen()
            elif yr == 2:
                self.play_test012_2_openagain()
            elif yr == 3:
                self.play_test012_3_remount()
            elif yr == 4:
                self.play_test012_4_remount_onemorefile()
            elif yr == 5:
                self.play_test012_5_remount_onemorefile_onefsync()
            elif yr == 6:
                self.play_test012_6_noremount_onemorefile()
            elif yr == 7:
                self.play_test012_7_noremount_twomorefile()

            self.RecordStatus(year=yr,season=1)

    def play_test012_0_onlyholes(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_1_sameopen(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        # filling holes
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_2_openagain(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()


        # open the file again 
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_3_remount(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'mountpoint'))
        MWpyFS.FormatFS.mountExt4(self.confparser.get('system', 'partition'), 
                        self.confparser.get('system', 'mountpoint'))

        # open the file again 
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_4_remount_onemorefile(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'mountpoint'))
        MWpyFS.FormatFS.mountExt4(self.confparser.get('system', 'partition'), 
                        self.confparser.get('system', 'mountpoint'))

        # open the file again 
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        # new file
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=1, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes 
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)



        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_5_remount_onemorefile_onefsync(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'mountpoint'))
        MWpyFS.FormatFS.mountExt4(self.confparser.get('system', 'partition'), 
                        self.confparser.get('system', 'mountpoint'))

        # open the file again 
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        # new file
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=1, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        #prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes 
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_6_noremount_onemorefile(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        #MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'mountpoint'))
        #MWpyFS.FormatFS.mountExt4(self.confparser.get('system', 'partition'), 
                        #self.confparser.get('system', 'mountpoint'))

        # open a new file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        # new file
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=1, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes 
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)



        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def play_test012_7_noremount_twomorefile(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        ##################################
        # new file 1
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        # new file 1
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=1, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        ##################################
        # new file 2 
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/loopmount/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=2)

        # new file 2 
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=2, off=off, len=4096)
            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=2)
        prd.addUniOp('close', pid=0, dirid=0, fileid=2)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def wrapper_test013(self):
        self.RecordWalkmanConfig()
        self.RecordFSSummary()
 
        # Run workload
        self.SetupEnv()
        #self.RecordStatus(year=0,season=0)
        subprocess.call("sh ./switch-mb-debug.sh 1".split())

        self.play_test013()
        subprocess.call("sh ./switch-mb-debug.sh 0".split())

        #self.RecordStatus(year=0,season=1)

    def play_test013(self):
        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')
                                + "_workload.buf." 
                                + self.confparser.get('system', 'hostname')))

        # Big file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/scratch/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addDirOp('mkdir', pid=0, dirid=0)
        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # write with holes
        off = 0 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        prd.display()
        prd.saveWorkloadToFile()

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

        #MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'mountpoint'))
        #MWpyFS.FormatFS.mountExt4(self.confparser.get('system', 'partition'), 
                        #self.confparser.get('system', 'mountpoint'))

        # open a new file
        prd = pyWorkload.producer.Producer(
                rootdir="/mnt/scratch/",
                tofile=self.confparser.get('system',
                    "workloadbufpath"))
        prd.addUniOp('open', pid=0, dirid=0, fileid=1)

        # new file
        off = 0
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=1, off=off, len=4096)
            #prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

            off += 8*1024 # 8KB stride
           

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=1)
        prd.addUniOp('close', pid=0, dirid=0, fileid=1)

        prd.addUniOp('open', pid=0, dirid=0, fileid=0)

        # filling holes 
        off = 4096 
        for i in range(17):
            prd.addReadOrWrite('write', pid=0, dirid=0,
                   fileid=0, off=off, len=4096)

            off += 8*1024 # 8KB stride

        prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)
        prd.addUniOp('close', pid=0, dirid=0, fileid=0)



        prd.display()
        prd.saveWorkloadToFile()

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
    
    walkman = Walkman(confparser, 'test013')
    walkman.wrapper()

if __name__ == "__main__":
    main(sys.argv)


