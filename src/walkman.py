# walkman is the driver/integrator of the MetaWalker.
# the workflow is like:
#   0. format the whole system
#   1. genearate workloads by Producer
#   2. For each workload:
#       2. play workload by player
#       3. monitor the FS status

import MWpyFS

class Walkman:
    def __init__(self):
        self.devname = '/dev/sdb'
        self.partition = '/dev/sdb1'
        self.diskconf = '../conf/sfdisk.conf'
        self.mountpoint = '/mnt/scratch/'
        self.moniotor = MWpyFS.Monitor.FSMonitor(self.partition, 
                                                 self.mountpoint)
    
    def rebuildFS(self):
        MWpyFS.FormatFS.buildNewExt4(self.devname,
                self.mountpoint, self.diskconf)



def main():
    walkman = Walkman()
    walkman.rebuildFS()


if __name_ == "__main__":
    main()
