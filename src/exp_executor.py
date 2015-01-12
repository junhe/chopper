# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import chpConfig
import subprocess
import MWpyFS
import argparse
import pyWorkload
import time
import optparse
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
import platform
import multiprocessing
#import cluster
from ast import literal_eval
from time import strftime, localtime, sleep
import make_disk_images


walkmanlog = open('/tmp/walkman.log', 'a')

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

    It is called Walkman because it walks in the input space
    and collect response.
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
        # This was for a legacy feature.
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

        # monitor
        self.monitor = MWpyFS.Monitor.FSMonitor(
                 self.confparser.get('system','partition'), 
                 self.confparser.get('system','mountpoint'),
                 ld = self.confparser.get('system','resultdir'),
                 filesystem = self.confparser.get('setup', 'filesystem')) # logdir

    def _remake_fs(self):
        fs = self.confparser.get('system', 'filesystem')

        disk_used = self.confparser.getfloat('system', 'disk_used')
        assert disk_used >= 0 and disk_used <= 1, "now it is a ratio"
        disksize = self.confparser.getint('system', 'disksize')
        used_ratio = disk_used 
        layoutnumber = self.confparser.getint('system',
                                              'layoutnumber')
        mopts = self.confparser.get('system', 'mountopts')

        make_disk_images.use_one_image(fstype=fs,
                               disksize=disksize,
                               used_ratio=used_ratio,
                               layoutnumber=layoutnumber,
                               mountopts=mopts
                               )
        return

    def _getYearSeasonStr(self, year, season):
        "Legacy function"
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
            print 'freezing...'
            MWpyFS.FormatFS.xfs_freeze(self.confparser.get('system', 'mountpoint'))
            print 'unfreezing...'
            MWpyFS.FormatFS.xfs_unfreeze(self.confparser.get('system', 'mountpoint'))

            print 'remounting...'
            MWpyFS.FormatFS.remountFS(devname=self.confparser.get('system', 'partition'),
                                      mountpoint=self.confparser.get('system', 'mountpoint'))
            MWpyFS.FormatFS.umountFS(self.confparser.get('system', 'partition'))
            MWpyFS.FormatFS.mountXFS(self.confparser.get('system', 'partition'),
                                     self.confparser.get('system', 'mountpoint'))
            print 'waiting for log to apply'
            time.sleep(1) # TODO: find a better way to make sure all logs
                          # are replayed.
        elif self.confparser.get('system', 'filesystem') == 'btrfs':
            MWpyFS.FormatFS.remountFS(devname=self.confparser.get('system', 'partition'),
                                      mountpoint=self.confparser.get('system', 'mountpoint'))
            print 'waiting for log to apply'
            time.sleep(1)

        print 'BEFORE DISLAY .............................'
        ret = self.monitor.display(savedata=savedata, 
                    logfile=self._getLogFilenameBySeasonYear(season,year),
                    monitorid=self._getYearSeasonStr(year=year, season=season),
                    jobid=self.confparser.get('system','jobid')
                    )
        return ret


    def _set_cpu(self):
        # assuming the available cpus have consecutive ids
        navail  = len(MWpyFS.Monitor.get_available_cpu_dirs())
        avails = range(navail)

        onlinecpus = MWpyFS.Monitor.get_online_cpuids() 
        offcpus = [id for id in avails if not id in onlinecpus]
        ncurrent = len( onlinecpus )
        
        ngoal = self.confparser.getint('system', 'core.count')

        if ngoal > navail:
            print 'You want {goal} cpus, but you only have {navail}.'.\
                    format(goal=ngoal, navail=navail)
            exit(1)

        while ncurrent > ngoal:
            # disable the last online cpu
            lastcpu = onlinecpus[-1]
            MWpyFS.Monitor.switch_cpu(lastcpu, mode='OFF')
        
            onlinecpus = MWpyFS.Monitor.get_online_cpuids() 
            offcpus = [id for id in avails if not id in onlinecpus]
            ncurrent = len( onlinecpus )
 
        while ncurrent < ngoal:
            # enable the first offline cpu
            firstcpu = offcpus[-1]
            MWpyFS.Monitor.switch_cpu(firstcpu, mode='ON')
        
            onlinecpus = MWpyFS.Monitor.get_online_cpuids() 
            offcpus = [id for id in avails if not id in onlinecpus]
            ncurrent = len( onlinecpus )

    def _SetupEnv(self):
        # set cpu count
        self._set_cpu()

        # Format file system
        self._remake_fs()

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

        Legacy code, not I removed all the other generators. 
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
    def __init__(self):
        # get a new instance, otherwise the global one is messy
        self.confparser = chpConfig.get_configparser() 

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

        ret = self._walkman_walk(conf)
        return ret

    def run_experiment(self, designfile, mode='batch'):
        #for treatment in pyWorkload.exp_design.dir_distance_iter():
        #for treatment in pyWorkload.exp_design.onefile_iter():
        if mode == 'batch':
            for treatment in pyWorkload.\
                   exp_design.fourbyfour_iter(designfile):
                self.run_and_get_df( treatment, savedf=True)
        elif mode == 'reproduce':
            for treatment in pyWorkload.\
                   exp_design.reproducer_iter(designfile):
                self.run_and_get_df( treatment, savedf=True)
        else:
            print 'experiment mode is not supported'
            exit(1)

    def run_and_get_df(self, treatment, savedf=False):
        """
        This function will run the experiment for this treatment,
        and append the resulting dataframe to the result file
        """
        # put treatment info to a dataframe which will be written to result file
        df = pyWorkload.pat_data_struct.treatment_to_df_morefactors(treatment)

        # put response to df
        ret = self.get_response(treatment)

        # calculate the ideal distance_sum
        ideal_sum = MWpyFS.Monitor.\
            extent_distant_sum({'off':None, 
                                'len':treatment['unique.bytes']})

        
        df.addColumn(key = 'dspan', value=ret['d_span'])
        assert ret['distance_sum'] >= ideal_sum, \
                "{} {} {}".format(ret['distance_sum'], ideal_sum, treatment['unique.bytes'])
        df.addColumn(key = 'layout_index', 
                     value = ret['distance_sum']/float(ideal_sum))
        df.addColumn(key = 'treatment_id', 
                     value = datetime.datetime.now().strftime("%m-%d-%H-%M-%S.%f"))
        df.addColumn(key = 'node_id',
                value = '.'.join(socket.gethostname().split('.')[0:2]))
        df.addColumn(key = 'kernel.release',
                value = platform.release())
        df.addColumn(key = 'datafiles',
                value = ret['datafiles'])
        df.addColumn(key = 'datafiles_dspan',
                value = ret['datafiles_dspan'])
        df.addColumn(key = 'num_extents',
                value = ret['num_extents'])

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
                  'n_virtual_cores', 
                  'disksize', 'disk_used',
                  'dspan', 'fullness',
                  'jobid', 'filesystem',
                  'dir.span', 'num.files',
                  'layout_index',
                  'layoutnumber',
                  'kernel.release',
                  'datafiles',
                  'datafiles_dspan',
                  'num_extents'
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
                self.fileout = open(
                        chpConfig.parser.get('system', 'resulttablepath'), 'w')
                self.fileout.write(df.toStr(header=True, table=True)) 
            else:
                self.fileout.write(df.toStr(header=False, table=True)) 
        return df

exp_exe = Executor()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="This script runs experiments sequentially. " \
            'Example: python exp_executor.py ' \
            '--mode=batch --resultpath=myresult.txt' 
            )
    parser.add_argument('--mode', choices=('batch', 'reproduce'),
            help='if mode=batch, design.path in h0.conf will be used as the '
            'design file to run the experiments. if mode=reproduce, '
            'reproducer.path in h0.conf will be used to run the experiments.')
    parser.add_argument('--resultpath', action='store') 
    args = parser.parse_args()

    if None in list(vars(args).values()):
        parser.print_help()
        exit(1)

    chpConfig.parser.set('system', 'resulttablepath', args.resultpath)

    if args.mode == 'batch':
        path = chpConfig.parser.get('setup', 'design.path')
    elif args.mode == 'reproduce':
        path = chpConfig.parser.get('setup', 'reproducer.path')
    
    exp_exe.run_experiment(designfile = path,
                           mode = args.mode)


