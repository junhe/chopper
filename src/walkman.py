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

class Config:
    def __init__(self):
        self.dic = {}

    def display(self, style="columns", colwidth=15, save2file=""):
        contents = ""
        if style == "columns":
            header = self.dic.keys()
            header = [ str(x).ljust(colwidth) for x in header]
            header = " ".join(header) + '\n'

            vals = self.dic.values()
            vals = [ str(x).ljust(colwidth) for x in vals]
            vals = " ".join(vals) + '\n'

            contents = header + vals
        else:
            tablestr = ""
            for keyname in self.dic:
                k = str(keyname).ljust(colwidth)
                v = str(self.dic[keyname]).ljust(colwidth)
                entry = " ".join([k, v]) 
                tablestr += entry + '\n'

            contents = tablestr

        if save2file != "":
            with open(save2file, 'w') as f:
                f.write(contents)
                f.flush()
        return contents

class Walkman:
    def __init__(self, confpath):
        self.confparser = SafeConfigParser()
        try:
            self.confparser.readfp(open(confpath, 'r'))
        except:
            print "unable to read config file:", confpath
        

        self.conf = Config()

        self.confparser.set('system','hostname', socket.gethostname())
        self.confparser.set('system','jobid', 
            self.confparser.get('system','hostname') + "-" +
            time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))

        self.confparser.set('system','workloadbufpath', 
                   os.path.join(self.confparser.get('system', 'workloaddir')\
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
        conflogpath = self.confparser.get('system','resultdir') + \
                    "walkmanJOB-"+self.confparser.get('system','jobid')+".conf.rows"

        for section_name in self.confparser.sections():
            print '[',section_name,']'
            for name, value in self.confparser.items(section_name):
                print '  %s = %s' % (name.ljust(colwidth), value.ljust(colwidth))
            print

    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.confparser.get('system','devname'),
                self.confparser.get('system','mountpoint'), 
                self.confparser.get('system','diskconf'), 
                self.confparser.get('system','username'))

    def remakeExt4(self):
        MWpyFS.FormatFS.remakeExt4(partition  =self.confparser.get('system','partition'),
                                   mountpoint =self.confparser.get('system','mountpoint'),
                                   username   =self.confparser.get('system','username'),
                                   blockscount=self.confparser.get('system','blockscount'))


    #def produceWorkload_rmdir(self, rootdir):
        #self.wl_producer.produce_rmdir(np=self.confparser.get('system','np'),
                                       #ndir_per_pid=self.ndir_per_pid,
                                       #rootdir=self.mountpoint+rootdir,
                                       #tofile=self.workloadbufpath)

    def produceWorkload(self, rootdir):
        self.wl_producer.produce(np=self.confparser.get('workload','np'), 
                                startOff=self.confparser.get('workload','startOff'),
                                nwrites_per_file = self.confparser.get('workload','nwrites_per_file'), 
                                nfile_per_dir=self.confparser.get('workload','nfile_per_dir'), 
                                ndir_per_pid=self.confparser.get('workload','ndir_per_pid'),
                                wsize=self.confparser.get('workload','wsize'), 
                                wstride=self.confparser.get('workload','wstride'), 
                                rootdir=self.confparser.get('system','mountpoint')+rootdir,
                                tofile=self.confparser.get('system','workloadbufpath'))
    def play(self):
        cmd = [self.confparser.get('system','mpirunpath'), "-np", 
                self.confparser.get('system','np'), 
                self.confparser.get('system','playerpath'), 
                self.confparser.get('system','workloadbufpath')]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def getrootdirByIterIndex(self, i):
        rootdir = "season"+str(i).zfill(3)+"/"   #TODO: fix the "/" must thing
        return rootdir

    def getLogFilenameBySeasonYear(self, season, year):
        return "walkmanJOB-"+self.confparser.get('system','jobid')+\
                ".result.log.year-"+str(year).zfill(5)+\
                ".season-"+str(season).zfill(5)

    def displayFreeFrag():
        e2ff = self.monitor.e2freefrag()
        print e2ff[0]
        print e2ff[1]
        return 

def main(args):
    if len(args) != 2:
        print "usage:", args[0], "config-file"
        exit(1)

    confpath = args[1]
    walkman = Walkman(confpath)
    walkman.displayandsaveConfig()
    return

    #print walkman.monitor.dumpfsSTR(),
    #return


    #walkman.rebuildFS()
    walkman.remakeExt4()
    #print 'sleeping 5 sec after building fs....'
    time.sleep(5)
    #return 

    print "starting......"
    time.sleep(3)

    nyears=1000
    nseasons_per_year = 10
    
    print "start looping..."
    for y in range(nyears):
        for s in range(nseasons_per_year):
            rootdir = walkman.getrootdirByIterIndex(s)
            walkman.produceWorkload(rootdir=rootdir)

            walkman.play()
            
 
            # now, delete the previous dir if it exists
            pre_s = (s - (nseasons_per_year-1))%nseasons_per_year
            pre_s_rootdir = walkman.getrootdirByIterIndex(pre_s)
            fullpath = os.path.join(walkman.conf.dic['mountpoint'],pre_s_rootdir)
            try:
                print "removing ", fullpath
                shutil.rmtree(fullpath)
            except:
                print "failed to rmtree (but should be OK):", fullpath


            # Monitor at the end of each year
            time.sleep(3)
            walkman.monitor.display(savedata=True, 
                                    logfile=walkman.getLogFilenameBySeasonYear(s,y))
            print "------ End of this year, sleep 2 sec ----------"
            time.sleep(2)
           

if __name__ == "__main__":
    main(sys.argv)

