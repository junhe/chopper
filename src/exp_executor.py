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
import copy
import datetime
#import cluster
from ast import literal_eval
from time import strftime, localtime, sleep
import make_disk_images


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

        disk_used = self.confparser.getint('system', 'disk_used')
        disksize = self.confparser.getint('system', 'disksize')
        used_ratio=float(disk_used*2**30)/disksize
        print disk_used, disksize, used_ratio
       
        make_disk_images.use_one_image(fstype=fs,
                                       disksize=disksize,
                               used_ratio=used_ratio)

        return

        if fs == 'ext4':
            self._remakeExt4()
        elif fs == 'xfs':
            self._remakeXFS()
        elif fs == 'btrfs':
            self._remakeBtrfs()

    def _remakeBtrfs(self):
        disksize = self.confparser.getint('system', 'disksize')
            
        if self.confparser.get('system', 'makeloopdevice') == 'yes':
            MWpyFS.FormatFS.makeLoopDevice(
                    devname=self.confparser.get('system', 'partition'),
                    tmpfs_mountpoint=self.confparser.get('system', 'tmpfs_mountpoint'),
                    sizeMB=disksize/(1024*1024))

        if not os.path.exists(self.confparser.get('system','mountpoint')):
            os.makedirs(self.confparser.get('system','mountpoint'))

        MWpyFS.FormatFS.btrfs_remake(partition  =self.confparser.get('system','partition'),
                                   mountpoint   =self.confparser.get('system','mountpoint'),
                                   username     =self.confparser.get('system','username'),
                                   groupname    =self.confparser.get('system','groupname'),
                                   nbytes       =disksize)

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
        disk_used = self.confparser.getint('system', 'disk_used')
        disksize = self.confparser.getint('system', 'disksize')
        used_ratio=float(disk_used*2**30)/disksize
        print disk_used, disksize, used_ratio
        #exit(0)
       
        make_disk_images.use_one_image(fstype='ext4',
                                       disksize=disksize,
                               used_ratio=used_ratio)
        return

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
        return self._wrapper()
    
    def _wrapper(self):
        """
        _SetupEnv()
        workload.Run()
        _RecordStatus()
        """

        year=0
        season=0
    
        self._SetupEnv()
        #self._RecordStatus(year=0, season=0) # always record the inital status

        # Run workload
        ret = self._play_workload_wrapper(year=year, season=season)

        # do not record faulty status of the file system
        # (however, sometimes it is useful to record faulty ones)
        if ret == 0:
            ret_record = self._RecordStatus(year=year,season=season+1, 
                                            savedata=False)
            return ret_record
        else:
            walkmanlog.write('>>>>>>>> One Failed walkman <<<<<<<<<<<<')
            self.confparser.write( walkmanlog )
            return None

    def _play_workload_wrapper(self, year, season):
        """
        decide which workload to play here. 
        They use different generators
        """
        return self._play_chunkseq()

    def _play_chunkseq(self):
        files_chkseq = self.confparser.get('workload', 'files_chkseq')
        files_chkseq = literal_eval(files_chkseq)

        pyWorkload.pat_data_struct.ChunkSeq_to_workload2(
                files_chkseq,
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

class Executor:
    def __init__(self, confparser):
        self.confparser = confparser 
        self.fileout = None

    def _walkman_walk(self, cf):
        walkman = Walkman(cf, 'fromExecutor')
        return walkman.walk()

    def get_response(self, treatment):
        """
        This function takes a treatment and get the response.
        NOTHING MORE!
        """
        # we need some trivial settings in the conf file
        # such as the the workload file location
        conf = self.confparser 

        pyWorkload.workload_builder.build_conf(
                                    treatment = treatment,
                                    confparser = conf)

        #pprint.pprint(conf.items('system'))
        #pprint.pprint(conf.items('workload'))
        #exit(0)
        ret = self._walkman_walk(conf)
        return ret

    def run_experiment(self):
        #for treatment in pyWorkload.exp_design.dir_distance_iter():
        #for treatment in pyWorkload.exp_design.onefile_iter():
        for treatment in pyWorkload.\
               exp_design.fourbyfour_iter('./design_blhd-4by4.txt'):
               #exp_design.fourbyfour_iter('./4by4design.txt'):
            pprint.pprint(treatment)
            self.run_and_get_df( treatment, savedf=True)

    def sampleworkload(self):
        file_treatment = {
               'parent_dirid' : 2,
               'fileid'       : 8848,
               'writer_pid'   : 1,
               'chunks'       : [
                               {'offset':0, 'length':1},
                               {'offset':1, 'length':1},
                               {'offset':2, 'length':1},
                               {'offset':3, 'length':1}
                              ],
                              #chunk id is the index here
               'write_order'  : [0,1,2,3],
               # The bitmaps apply to ordered chunkseq
               'open_bitmap'  : [True, True, True, True],
               'fsync_bitmap' : [False, False, False, False],
               'close_bitmap' : [True, True, True, True],
               'sync_bitmap'  : [True, False, False, False ],
               'writer_cpu_map': [0,1,0,1] # set affinity to which cpu
               }

        #pprint.pprint(build_file_chunkseq( file_treatment ))

        treatment = {
                      'filesystem': 'ext4',
                      'disksize'  : 64*1024*1024,
                      'free_space_layout_score': 1,
                      'free_space_ratio': 0.7,
                      'dir_depth'     : 3,
                      # file id in file_treatment is the index here
                      'files': [file_treatment, copy.deepcopy(file_treatment)],
                      #'files': [file_treatment],
                      # the number of item in the following list
                      # is the number of total chunks of all files
                      'filechunk_order': [0, 1, 0, 1, 0, 1, 0, 1]
                      #'filechunk_order': [0,0,0,0]
                    }
        pyWorkload.workload_builder.correctize_fileid(treatment)
        self.run_and_get_df( treatment, savedf=True)
        self.run_and_get_df( treatment, savedf=True)

    def run_and_get_df(self, treatment, savedf=False ):
        """
        This function will run the experiment for this treatment,
        and append the resulting dataframe to the result file
        """
        #df = pyWorkload.pat_data_struct.treatment_to_df_foronefile(treatment)
        df = pyWorkload.pat_data_struct.treatment_to_df_morefactors(treatment)

        # put response to df
        ret = self.get_response(treatment)
        
        df.addColumn(key = 'dspan', value=ret['d_span'])
        df.addColumn(key = 'treatment_id', 
                     value = datetime.datetime.now().strftime("%m-%d-%H-%M-%S.%f"))
        df.addColumn(key = 'node_id',
                value = '.'.join(socket.gethostname().split('.')[0:2]))

        ##############################3
        # do some clean up
        # writer_cpu_map       fullness             
        # open_bitmap          close_bitmap         
        # nchunks              writer_pid           
        # n_virtual_cores      write_order          
        # filesize             sync_bitmap          
        # parent_dirid         chunks               
        # fileid               fsync_bitmap         
        # filechunk_order      disksize            
        # dir_depth            filesystem           
        # disk_used            dspan               
        # treatment_id         node_id
        tokeep = [
                  'write_order',  'filesize',
                  'sync_bitmap',  'fsync_bitmap',
                  'nchunks',
                  'n_virtual_cores', 'parent_dirid',
                  'disksize', 'disk_used',
                  'dspan', 'fullness',
                  'jobid', 'filesystem'
                  ]
        headers = copy.deepcopy(df.header)
        for colname in headers:
            if not colname in tokeep:
                df.delColumn(colname)
        # keep only one row
        del df.table[1:]

        translate_dic = {
                'write_order':'chunk.order',
                'filesize':'file.size',
                'sync_bitmap':'sync',
                'fsync_bitmap':'fsync',
                'nchunks':'num.chunks',
                'n_virtual_cores':'num.cores', 
                'parent_dirid':'dir.id',
                'disksize':'disk.size',
                'disk_used':'disk.used',
                'filesystem':'file.system'
              }
        for i,k in enumerate(df.header):
            if translate_dic.has_key(k):
                df.header[i] = translate_dic[k]

        if savedf:
            if self.fileout == None:
                self.fileout = open('result-table.txt', 'w')
                self.fileout.write(df.toStr(header=True, table=True)) 
            else:
                self.fileout.write(df.toStr(header=False, table=True)) 
        return df

walkmanlog = open('/tmp/walkman.log', 'a')
    
confpath = "../conf/h0.conf"
confparser = SafeConfigParser()
try:
    confparser.readfp(open(confpath, 'r'))
except:
    print "unable to read config file:", confpath
    exit(1)
   
exp_exe = Executor(confparser)

if __name__ == '__main__':
    exp_exe.run_experiment()

