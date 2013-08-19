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
#       filepath create_time n_metablock n_datablock metadata_ratio filebytes
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
import shlex
import os
import pprint

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

class FSMonitor:
    """
    This monitor probes the ext4 file system and return information I 
    want in a nice format.
    """
    def __init__(self, dn, mp, ld="/tmp", cw=20):
        self.devname = dn 
        self.mountpoint = mp # please only provide path without mountpoint
                             # when using this class.
        self.col_width = cw
        self.logdir = ld
        self.resetMonitorTime()
    
    def resetMonitorTime(self):
        self.monitor_time = strftime("%Y-%m-%d-%H-%M-%S", gmtime())


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
                    hist_table = "Extent_start Extent_end  Free_extents   Free_Blocks  Percent monitor_time HEADERMARKER_freefrag_hist\n"
                    continue
                fline = re.sub(r'[\-:\n]', "", line)
                fline = re.sub(r'\.{3}', "", fline)
                hist_table += fline + " " + self.widen(str(self.monitor_time)) \
                              + " DATAMARKER_freefrag_hist\n"
                 
        return (self.dict2table(sums_dict), hist_table)

        
    def dump_extents(self, filepath):
        cmd = "debugfs /dev/sdb1 -R 'dump_extents " + filepath + "'"
        cmd = shlex.split(cmd)
        #print cmd
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
        proc.wait()

        ext_list = [] # Use list here in case I want to extract data in Python
        header = []
        n_entries = [0] * 3 # n_entries[k] is the number of entries at level k
                            # it can be used to calculate number of 
                            # internal/leaf nodes
        max_level = 0
        for line in proc.stdout:
            #print "LLL:", line,
            if "Level" in line:
                header = ["Level_index", "Max_level", 
                         "Entry_index", "N_Entry",
                         "Logical_start", "Logical_end",
                         "Physical_start", "Physical_end",
                         "Length", "Flag"]
            else:
                savedline = line
                line = re.sub(r'[/\-]', " ", line)
                tokens = line.split()
                d = {}
                for i in range(9):
                    try:
                        d[ header[i] ] = tokens[i]
                    except:
                        print savedline
                        print "token:", tokens
                        print "header:", header # having a try-except can grant you
                                            # the opportunity to do something 
                                            # after bad thing happen
                
                if len(tokens) == 10:
                    d["Flag"] = tokens[10]
                else:
                    d["Flag"] = "NA"

                n_entries[ int(d["Level_index"]) ] = int( d["N_Entry"] )
                max_level = int( d["Max_level"] )
                
        # calculate number of meatadata blocks
        # only 1st and 2nd levels takes space. 
        # How to calculate:
        #   if there is only 1 level (root and level 1).
        #   the number of entires in level 0 indicates the
        #   number of nodes in level 1.
        #   Basically, the number of entries in level i
        #   equals the number of ETB of the next level
        n_metablock = 0
        if max_level == 0:
            # the tree has no extent tree block outside of the inode
            n_metablock = 0
        else:
            for n in n_entries[0:max_level]:
                n_metablock += n
        
        dumpdict = {}
        dumpdict["filepath"] = filepath
        dumpdict["n_metablock"] = n_metablock
        others = self.filefrag(filepath)
        dumpdict["n_datablock"] = others["nblocks"]
        dumpdict["filebytes"] = others["nbytes"]
    
        return dumpdict

    def filefrag(self, filepath):
        fullpath = os.path.join(self.mountpoint, filepath)  
        cmd = ["filefrag", "-sv", fullpath]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        proc.wait()

        mydict = {}
        for line in proc.stdout:
            if line.startswith("File size of"):
                #print line
                line = line.split(" is ")[1]
                #print line
                nums = re.findall(r'\d+', line)
                if len(nums) != 3:
                    print "filefrag something wrong"
                    exit(1)
                mydict["nbytes"] = nums[0]
                mydict["nblocks"] = nums[1]
                mydict["blocksize"] = nums[2]
        return mydict

    def getAllInodePaths(self, rootdir="."):
        "it returns paths of all files and diretories"
        rootpath = os.path.join(self.mountpoint, rootdir)

        paths = []
        with cd(rootpath):
            cmd = ['find', rootdir]
            proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
            proc.wait()

            for line in proc.stdout:
                paths.append(line.replace("\n", ""))
            
        return paths

    def getAllExtentStats(self, rootdir="."):
        files = self.getAllInodePaths(rootdir)
        stats = []
        for f in files:
            stats.append( self.dump_extents(f) )
        return stats
        
    def getAllExtentStatsSTR(self, rootdir="."):
        stats = self.getAllExtentStats(rootdir)

        if len(stats) == 0:
            return ""
            
        header = ""
        for keyname in stats[0]:
            header += self.widen(keyname) + " "
        header += self.widen("monitor_time") + " HEADERMARKER_extstats\n"

        vals = ""
        for entry in stats:
            for keyname in entry:
                vals += self.widen(str(entry[keyname])) + " "
            vals += self.widen(str(self.monitor_time)) + " DATAMARKER_extstats\n"
        
        return header + vals
        
    def widen(self, s):
        return s.rjust(self.col_width)

    def dict2table(self, mydict):
        mytable = ""

        header = ""
        for keyname in mydict:
            header += self.widen(keyname) + " "
        header += self.widen("monitor_time") + " HEADERMARKER_freefrag_sum\n"

        vals = ""    
        for keyname in mydict:
            vals += self.widen(mydict[keyname]) + " "
        vals += self.widen(str(self.monitor_time)) + " DATAMARKER_freefrag_sum\n"

        return header + vals

    def display(self, savedata=False, logfile=""):
        self.resetMonitorTime()
        "resultpath should be in another file system so they don't intervene"
        extstats = self.getAllExtentStatsSTR()
        frag = self.e2freefrag()
        
        # display
        extstats_header = "-----------  Extent statistics  -------------\n"
        frag0_header  = "-----------  Extent summary  -------------\n"
        frag1_header = "----------- Extent Histogram   -------------\n"

        print extstats_header, extstats,
        print frag0_header, frag[0]
        print frag1_header, frag[1]

        if savedata: 
            if logfile == "":
                filename = self.monitor_time + ".result"
            else:
                filename = logfile
            fullpath = os.path.join(self.logdir, filename)
            f = open(fullpath, 'w')
            f.write(extstats_header + extstats)
            f.write(frag0_header + frag[0])
            f.write(frag1_header + frag[1])
            f.close()
        
        return

        

#fsmon = FSMonitor("/dev/sdb1", "/mnt/scratch")
#fsmon.display(savedata=True)

