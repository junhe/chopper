# The monitor is used to monitor the FS fragmentation status.
# What I want to see is, generally, how's the metadata. This may include:
#
#  SIZE of inode and extent tree. (number of inode block and extent tree
#  block). This can be find by debugfs "dump_extents [-n] [-l] filespec".
#  But you have to do it for ALL files in the file system, which might be
#  slow. I haven't got a better approach. A good indicator of metadata
#  problem is #_metadata_block/#_data_block. This should be very informative
#  about the aging of a file system which causes metadata disaster.
#       I expect the following from the output of this per file:
#       
#       filepath create_time meta_ratio n_metablock n_datablock
#
#  Extent fragmentation overview. This can be obtained by e2freefrag. This
#  should give me a good sense of how fragemented the FS is. The acceleration
#  rate of fragmentation might be a good indicator of whether a workload
#  can cause metadata problem. (Because of fragmentation, physical blocks
#  might not be able to allocated contiguously, then it needs two or more
#  extents to the logically contiguous blocks.)
#       I expect the following from the output of this per FS:
#       JUST LIKE THE ORIGINAL OUTPUT BUT FORMAT IT A LITTLE BIT

import subprocess
from time import gmtime, strftime
import re

def dict2table(mydict):
    mytable = ""
    for keyname in mydict:
        mystr = " ".join( [keyname, mydict[keyname]] )
        mytable += mystr + "\n"
    return mytable
        

class FSMonitor:
    """
    This monitor probes the ext4 file system and return information I 
    want in a nice format.
    """
    def __init__(self, dn, mp):
        self.devname = dn 
        self.mountpoint = mp
        self.monitor_id = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
    
    def e2freefrag(self):
        cmd = ["e2freefrag", self.devname]
        proc = subprocess.Popen(cmd,
                           stdout=subprocess.PIPE)
        proc.wait()

        part = 0
        sums_dict = {}
        hist_table = ""
        for line in proc.stdout:
            if part == 0:
                if "HISTOGRAM" in line:
                    part = 1
                    continue
                mo = re.search( r'(.*): (\d+)', line, re.M)
                if mo:
                    keyname = mo.group(1)
                    keyname = keyname.replace('.', '')
                    keyname = "_".join(keyname.split())
                    sums_dict[keyname] = mo.group(2)
            elif part == 1:
                # This part is the histogram.
                if "Extent Size" in line:
                    hist_table = "Extent_start Extent_end  Free_extents   Free_Blocks  Percent\n"
                    continue
                fline = re.sub(r'[\-:\n]', "", line)
                fline = re.sub(r'\.{3}', "", fline)
                hist_table += fline + "\n"
                 
        return (dict2table(sums_dict), hist_table)

fsmon = FSMonitor("/dev/sdb1", "/mnt/scratch")
frag = fsmon.e2freefrag()

for e in frag: print e




