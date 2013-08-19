# walkman is the driver/integrator of the MetaWalker.
# the workflow is like:
#   0. format the whole system
#   1. genearate workloads by Producer
#   2. For each workload:
#       2. play workload by player
#       3. monitor the FS status
import subprocess
import MWpyFS
import pyWorkload


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
        self.np = 4 # put it here guide mpirun and wl producer
    
    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.devname,
                self.mountpoint, self.diskconf, "junhe")
    def produceWorkload(self, rootdir):
        self.wl_producer.produce(np=self.np, 
                                startOff=0,
                                nwrites_per_file = 10000, 
                                nfile_per_dir=3, 
                                ndir_per_pid=2,
                                wsize=1, 
                                wstride=2, 
                                rootdir=self.mountpoint+rootdir,
                                tofile=self.workloadpath)
    def play(self):
        cmd = [self.mpirunpath, "-np", self.np, self.playerpath, self.workloadpath]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()


def main():
    walkman = Walkman()
    #walkman.rebuildFS()

    n = 3 # play this workload for n time, monitor the FS status
          # after each time
    for i in range(2,n):
        rootdir = "round"+str(i)+"/"   #TODO: fix the "/" must thing
        walkman.produceWorkload(rootdir=rootdir)
        walkman.play()
        walkman.monitor.display(savedata=True)

if __name__ == "__main__":
    main()
