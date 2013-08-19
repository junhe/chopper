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
        self.moniotor = MWpyFS.Monitor.FSMonitor(self.partition, 
                                                 self.mountpoint)
        self.workloadpath = "./pyWorkload/workload.buf"
        self.wl_producer = pyWorkload.producer.Producer()
        self.playerpath = "../build/src/player"
        self.np = 4 # put it here guide mpirun and wl producer
    
    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.devname,
                self.mountpoint, self.diskconf)
    def produceWorkload(self):
        self.wl_producer.produce(np=self.np, 
                                startOff=10000, 
                                nwrites_per_file = 10, 
                                nfile_per_dir=3, 
                                ndir_per_pid=2,
                                wsize=3331, 
                                wstride=3331, 
                                mountpoint="/mnt/scratch/", 
                                tofile=self.workloadpath)
    def play(self):
        cmd = ["mpirun", "-np", self.np, self.playerpath, self.workloadpath]
        cmd = [str(x) for x in cmd]
        proc = subprocess.Popen(cmd) 
        proc.wait()


def main():
    walkman = Walkman()
    #walkman.rebuildFS()
    walkman.produceWorkload()

    n = 1 # play this workload for n time, monitor the FS status
          # after each time
    for i in range(n):
        walkman.play()

if __name__ == "__main__":
    main()
