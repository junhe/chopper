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

class Walkman:
    def __init__(self):
        self.devname = '/dev/sdb'
        self.partition = '/dev/sdb1'
        self.diskconf = '../conf/sfdisk.conf'
        self.mountpoint = '/mnt/scratch/'
        self.monitor = MWpyFS.Monitor.FSMonitor(self.partition, 
                                                 self.mountpoint,
                                                 ld = "./") # logdir
        self.workloadpath = "./pyWorkload/workload.buf"
        self.wl_producer = pyWorkload.producer.Producer()
        self.playerpath = "../build/src/player"
        self.mpirunpath = "/home/junhe/installs/openmpi-1.4.3/bin/mpirun"
        self.np = 2 # put it here guide mpirun and wl producer
        self.ndir_per_pid = 2
    
    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.devname,
                self.mountpoint, self.diskconf, "junhe")

    #def produceWorkload_rmdir(self, rootdir):
        #self.wl_producer.produce_rmdir(np=self.np,
                                       #ndir_per_pid=self.ndir_per_pid,
                                       #rootdir=self.mountpoint+rootdir,
                                       #tofile=self.workloadpath)

    def produceWorkload(self, rootdir):
        self.wl_producer.produce(np=self.np, 
                                startOff=0,
                                nwrites_per_file = 50, 
                                nfile_per_dir=3, 
                                ndir_per_pid=self.ndir_per_pid,
                                wsize=4097, 
                                wstride=4098*2, 
                                rootdir=self.mountpoint+rootdir,
                                tofile=self.workloadpath)
    def play(self):
        cmd = [self.mpirunpath, "-np", self.np, self.playerpath, self.workloadpath]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()

    def getrootdirByIterIndex(self, i):
        rootdir = "round"+str(i)+"/"   #TODO: fix the "/" must thing
        return rootdir

    def getLogFilenameBySeasonYear(self, season, year):
        return "result.log.season-"+str(season)+".year-"+str(year)

    def displayFreeFrag():
        e2ff = self.monitor.e2freefrag()
        print e2ff[0]
        print e2ff[1]
        return 

def main():
    walkman = Walkman()

    #walkman.rebuildFS()
    #return


    nyears=3
    nseasons_per_year = 4
    
    for y in range(nyears):
        for s in range(nseasons_per_year):
            rootdir = walkman.getrootdirByIterIndex(s)
            walkman.produceWorkload(rootdir=rootdir)

            walkman.play()

            time.sleep(3)
            walkman.monitor.display(savedata=True, 
                                    logfile=walkman.getLogFilenameBySeasonYear(s,y))

            # now, delete the previous dir if it exists
            pre_s = (s - (nseasons_per_year-1))%nseasons_per_year
            pre_s_rootdir = walkman.getrootdirByIterIndex(pre_s)
            fullpath = os.path.join(walkman.mountpoint,pre_s_rootdir)
            try:
                print "removing ", fullpath
                shutil.rmtree(fullpath)
            except:
                print "failed to rmtree (but should be OK):", fullpath

            

if __name__ == "__main__":
    main()

