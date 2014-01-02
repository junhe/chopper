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
import random
from ast import literal_eval

walkmanlog = None
feedback_dic = {}

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

    NEW!
    Now it should get feedback from the file system. It is
    good that we already can record the status of the file
    system. What we need to do is just calculate the metric
    by Python instead of delaying it to R :(

    Then we need to figure out how to use this metics to adjust
    our parameters. 

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
                    sizeMB=loodevsizeBytes/(1024*1024))

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

    def _RecordStatus(self, year, season, savedata=True):
        subprocess.call(['sync'])
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

        ret = self.monitor.display(savedata=savedata, 
                    logfile=self._getLogFilenameBySeasonYear(season,year),
                    monitorid=self._getYearSeasonStr(year=year, season=season),
                    jobid=self.confparser.get('system','jobid')
                    )
        return ret

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

        # At least put some files there
        if self.confparser.get('system', 'copybootfiles').lower() == 'yes':
            print "copying some boot files to the mount point"
            pyWorkload.misc.copy_boot(
                    self.confparser.get('system', 'mountpoint') )


    def walk(self):
        self._wrapper()
    
    def _wrapper(self):
        """
        _SetupEnv()
        workload.Run()
        _RecordStatus()
        """

        nyear = self.confparser.getint('workload', 'nyears')
        nseasons_per_year = self.confparser.getint('workload', 'nseasons_per_year')

        self._SetupEnv()
        #self._RecordStatus(year=0, season=0) # always record the inital status

        for year in range(nyear):
            for season in range(nseasons_per_year):
                # Run workload
                ret = self._play_workload_wrapper(year=year, season=season)

                # do not record faulty status of the file system
                # however, sometimes it is useful to record faulty ones
                print 'Return of _play_workload_wrapper() =', ret
                if ret == 0:
                    ret_record = self._RecordStatus(year=year,season=season+1, 
                                                    savedata=False)
                    print 'ret_record', ret_record
                    self._post_run_processing(ret_record, year, season+1)
                else:
                    walkmanlog.write('>>>>>>>> One Failed walkman <<<<<<<<<<<<')
                    confparser.write( walkmanlog )

    def _post_run_processing(self, ret_record, year, season):
        self._record_config(ret_record, year, season)
        self._record_details(ret_record, year, season)
    
    def _record_config(self, ret_record, year, season):
        if ret_record.has_key('d_span'):
            # The returned d_span is good.
            d_span = ret_record['d_span']
            if d_span != 'NA':
                d_span = int(ret_record['d_span'])
            self.confparser.set(
                                self.confparser.get('workload', 'name'),
                                'd_span',
                                str(d_span))

        if ret_record.has_key('physical_layout_hash'): 
            # has this key in ret_record 
            self.confparser.set(
                                self.confparser.get('workload', 'name'),
                                #'workload_many_file_traverse',
                                'physical_layout_hash', str(ret_record['physical_layout_hash']) )
 
        # save wrappers sequence ((()))
        if self.confparser.get('workload', 'name') == 'singlefiletraverse':
            wps = self.confparser.get(
                                'singlefiletraverse',
                                'wrappers')
            wps = literal_eval(wps)
            self.confparser.set(
                                'singlefiletraverse',
                                'pattern_symbols',
                            pyWorkload.pattern_iter.wrappers_to_symbols(wps))

        self.confparser.remove_option('singlefiletraverse', 'chunks')
        self.confparser.remove_option('singlefiletraverse', 'wrappers')

        self._RecordWalkmanConfig()
        
    def _record_details(self, ret_record, year, season):
        global feedback_dic

        # initialize feedback_dic as needed
        for k in ret_record.keys():
            if not feedback_dic.has_key(k):
                feedback_dic[k] = []
        
        #print ['*'] * 100
        print ret_record
        print feedback_dic
        #feedback_inuse = 'd_span'
        feedback_inuse = 'physical_layout_hash'
        #print feedback_inuse


        print 'd_span', ret_record['d_span']
        print 'filesize', self.confparser.getint(self.confparser.get('workload','name'), 'filesize')

        if ret_record['d_span'] <  \
                2 * self.confparser.getint(self.confparser.get('workload','name'), 'filesize'):
            return


        if ret_record[feedback_inuse] in feedback_dic[feedback_inuse]:
            # already has it, skip recording
            print 'skip'
            return

        feedback_dic[feedback_inuse].append( ret_record[feedback_inuse] )

        self._RecordStatus(year=year,season=season, 
                                        savedata=True)

    def _play_workload_wrapper(self, year, season):
        """
        decide which workload to play here. 
        They use different generators
        """
        if self.confparser.get('workload', 'name') == 'ibench':
            return self._play_ibench(year, season)
        elif self.confparser.get('workload', 'name') == 'singlefiletraverse':
            return self._play_single_file_traverse()
        elif self.confparser.get('workload', 'name') == 'manyfiletraverse':
            return self._play_many_file_traverse()
        elif self.confparser.get('workload', 'name') == 'fbworkload':
            # fbworkload is the one with segment, write size,
            # write direction...
            return self._play_fb_workload()
        elif self.confparser.get('workload', 'name') == 'traditional':
            # This is the one where many pid write to many dir with
            # many files of many writes
            # and have write frequency.
            return self._play_test()
        else:
            print "BAD BAD, you are using a workload name that does not exist"
            exit(1)

    def _play_many_file_traverse(self):
        chunks_and_ops = self.confparser.get(self.confparser.get('workload','name'),
                                             'chunks_and_ops')
        chunks_and_ops = literal_eval(chunks_and_ops)

        #print "------------------------------------------"
        #pprint.pprint( chunks_and_ops )

        pyWorkload.pattern_iter.GenWorkloadFromChunksOfFiles(
                chunks_and_ops,
                rootdir  = self.confparser.get('system', 'mountpoint'),
                tofile   = self.confparser.get('system', 'workloadbufpath'))
       
        # find out how many proc we need
        max_rank = 0
        with open( self.confparser.get('system', 'workloadbufpath') ) as f:
            for line in f:
                items = line.split(";")
                rank  = int(items[0])
                if rank > max_rank:
                    max_rank = rank


        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                #self.confparser.get('workload','np'), 
                max_rank+1,
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]

        proc = subprocess.Popen(cmd) 
        proc.wait()
        return proc.returncode

    def _play_single_file_traverse(self):
        chunks = self.confparser.get(self.confparser.get('workload','name'),
                                        'chunks')
        chunks = literal_eval(chunks)
        wrappers = self.confparser.get(self.confparser.get('workload','name'),
                                        'wrappers')
        wrappers = literal_eval(wrappers)

        print chunks
        print wrappers

        pyWorkload.pattern_iter.GenWorkloadFromChunks(
                chunks, wrappers,
                rootdir  = self.confparser.get('system', 'mountpoint'),
                tofile   = self.confparser.get('system', 'workloadbufpath'))

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]

        proc = subprocess.Popen(cmd) 
        proc.wait()
        return proc.returncode

    def _play_fb_workload(self):
        wpd = {
                'segment_size': 100,
                'write_size'  : 50,
                'file_size'   : 200,
                #'direction'   : 'INCREASE'
                'direction'   : 'DECREASE'
              }
        pyWorkload.producer.GenFBWorkload(
                                  write_pattern_dic= wpd,
                                  writes_per_flush = 2,
                                  rootdir          = self.confparser.get('system', 'mountpoint'),
                                  tofile           = self.confparser.get('system','workloadbufpath'))

        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('workload','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]

        proc = subprocess.Popen(cmd) 
        proc.wait()
        return proc.returncode

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

    def _test018(self):
        paradict = {
                'nwrites_per_file': [2],
                'w_hole'          : [1024*1024 - 2*4096],
                'wsize'           : [4096],
                'nfile_per_dir'   : [1],
                # 0: only fsync() before closing
                # 1: fsync() after each write
                # 2: no fynsc() during open-close
                'fsync' : [2],
                'name'  : ['fbworkload']
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
        "It returns paralist, which will be put into confparser"
        return self._test018()

    def march_wrapper(self):
        #self._march_many()
        self._march_single()

    def _march_traditional(self):
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
            # put the paremters in para into cparser
            for k,v in para.items():
                cparser.set( 'workload', str(k), str(v) )
            # Do a run with cparser
            self._walkman_walk(cparser)

    def _march_single(self):
        
        filesystems = ['btrfs', 'xfs', 'ext4']

        self.confparser.set('workload', 'name', 'singlefiletraverse')
        self.confparser.add_section( self.confparser.get('workload','name') )

        for fs in filesystems:
            self.confparser.set('system', 'filesystem', fs)

            exps = [2**x for x in range(15)]
            filesizes1 = [4*1024*3*x for x in exps] 
            filesizes2 = [4*1024*3*x for x in range(1,20)] 

            for fsizemode in ['incr', 'exp']:
                self.confparser.set('singlefiletraverse', 'fsizemode', fsizemode)
                if fsizemode == 'incr':
                    filesizes = filesizes2
                else:
                    filesizes = filesizes1

                #for chunk_size in chunksizes:
                for filesize in filesizes:
                    chunk_size = 4096
                    #filesize = chunk_size * 3
                    #print ['input filesize']*100,filesize
                    #continue

                    self.confparser.set(self.confparser.get('workload','name'), 
                                        'filesize', str(filesize))
                    self.confparser.set(self.confparser.get('workload','name'),
                                        'chunk_size', str(chunk_size))
                    
                    print "Before iterate..."
                    for entry in pyWorkload.pattern_iter.pattern_iter(nfiles     =1, 
                                              filesize   =filesize, 
                                              chunksize  =chunk_size,
                                              num_of_chunks = 3):
                        print '----------------------------------------------------------'
                        print '----------------------------------------------------------'
                        print '----------------------------------------------------------'
                        print '----------------------------------------------------------'
                        print '----------------------------------------------------------'
                        print entry
                        chunks = str(entry['chunks'])
                        wrappers = str(entry['wrappers'])
                        self.confparser.set(self.confparser.get('workload','name'),
                                            'chunks',
                                            chunks)
                        self.confparser.set(self.confparser.get('workload','name'),
                                            'wrappers',
                                            wrappers)
                        wrappers01 = "".join( [str(int(x)) for x in entry['wrappers']] )
                        self.confparser.set(self.confparser.get('workload','name'),
                                            'wrappers01',
                                            wrappers01)
                        patternstring = pyWorkload.pattern_iter.pattern_string( entry['chunks'], entry['wrappers'] )
                        self.confparser.set(self.confparser.get('workload','name'),
                                            'patternstring', patternstring)
                        print patternstring
                             
                        self._walkman_walk(self.confparser)
                        #print 'my end'
                        #exit(1)
                        #break

                    #time.sleep(1)
                    #break

    def _march_many(self):

        self.confparser.set('workload', 'name', 'manyfiletraverse')

        filesize = 8*1024*1024
        chunk_size = 1024*1024

    
        
        for entry in pyWorkload.pattern_iter.pattern_iter_nfiles(
                                  nfiles     =2,
                                  filesize   =filesize, 
                                  chunksize  =chunk_size):
            #pprint.pprint( entry )
            chunks_and_ops = str(entry)
            #print "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk"
            #print chunks_and_ops
            self.confparser.set(self.confparser.get('workload','name'),
                                'chunks_and_ops',
                                chunks_and_ops)

            self._walkman_walk(self.confparser)
            #time.sleep(1)

def main(args):
    if len(args) != 2:
        print 'usage:', args[0], 'config-file'
        exit(1)
    global walkmanlog
    walkmanlog = open('/tmp/walkman.log', 'a')
    
    confpath = args[1]
    confparser = SafeConfigParser()
    try:
        confparser.readfp(open(confpath, 'r'))
    except:
        print "unable to read config file:", confpath
        exit(1)
   
    troops = Troops(confparser)
    troops.march_wrapper()

    #walkman = Walkman(confparser, 'recorder')
    #walkman._RecordStatus(0, 0)
    walkmanlog.close()
    exit(0)

if __name__ == "__main__":
    main(sys.argv)


