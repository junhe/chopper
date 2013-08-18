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
        pass
    
    def rebuildFS(self):
        pass

print "hello"

fsmon = MWpyFS.Monitor.FSMonitor("/dev/sdb1", "/mnt/scratch")
fsmon.display(savedata=False)
