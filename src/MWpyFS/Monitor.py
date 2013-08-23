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
from time import strftime, localtime
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
        self.devname = dn   # this should be the device name of the partition 
        self.mountpoint = mp # please only provide path without mountpoint
                             # when using this class.
        self.col_width = cw
        self.logdir = ld
        self.resetMonitorTime()
    
    def resetMonitorTime(self, monitorid=""):
        "monitor_time is used to identify each data retrieval"
        if monitorid == "":
            self.monitor_time = strftime("%Y-%m-%d-%H-%M-%S", localtime())
        else:
            self.monitor_time = monitorid

    def _spliter_dumpfs(self, line):
        line = line.replace(",", " ")
        elems = line.split(":")[1]
        elems = elems.split()

        new_elems = [] # [[a0,a1],[b0,b1]...]
        for elem in elems:
            e = elem.split("-")
            elen = len(e)
            if elen == 2:
                new_elems.append(e)
            elif elen == 1:
                e = e*2
                new_elems.append(e)
            else:
                print "wrong split", elem
                exit(1)
        return new_elems

    def dumpfsSummary(self):
        print "dumpfs..."
        cmd = ["dumpe2fs", "-h", self.devname]
        proc = subprocess.Popen(cmd, 
                                stdout=subprocess.PIPE)

        print "dumpfs finished. Parsing results..."
        proc.wait()
        return proc.communicate()[0]

    def dumpfs(self):
        print "dumpfs..."
        cmd = ["dumpe2fs", self.devname]
        proc = subprocess.Popen(cmd, 
                                stdout=subprocess.PIPE)

        print "dumpfs finished. Parsing results..."
        freeblocks = []
        freeinodes = []
        for line in proc.stdout:
            if line.startswith("  Free blocks:"):
                freeblocks += self._spliter_dumpfs(line)
            elif line.startswith("  Free inodes:"):
                freeinodes += self._spliter_dumpfs(line)
            else:
                pass
        proc.wait()
        return {"blocks":freeblocks, "inodes":freeinodes}

    def dumpfsSTR(self):
        print "dumpfsSTR...."
        ranges = self.dumpfs()
        print "after dumpfs()..."

        freeblocks = "start end monitor_time HEADERMARKER_freeblocks".split()
        freeblocks = [ self.widen(x) for x in freeblocks ]
        freeblocks = " ".join(freeblocks) + '\n'
        for row in ranges['blocks']:
            entry = row + [self.monitor_time,  "DATAMARKER_freeblocks"]
            entry = [ self.widen(str(x)) for x in entry ]
            entry = " ".join(entry)
            freeblocks += entry + "\n"

        freeinodes = "start end monitor_time HEADERMARKER_freeinodes".split()
        freeinodes = [ self.widen(x) for x in freeinodes ]
        freeinodes = " ".join(freeinodes) + '\n'
        for row in ranges['inodes']:
            entry = row + [self.monitor_time,  "DATAMARKER_freeinodes"]
            entry = [ self.widen(str(x)) for x in entry ]
            entry = " ".join(entry)
            freeinodes += entry + "\n"
        
        return {'freeblocks':freeblocks, 
                'freeinodes':freeinodes}

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
                line = line.strip()
                if "Extent Size" in line:
                    hist_table = "Extent_start Extent_end  Free_extents   Free_Blocks  Percent monitor_time HEADERMARKER_freefrag_hist\n"
                    continue
                fline = re.sub(r'[\-:\n]', "", line)
                fline = re.sub(r'\.{3}', "", fline)
                hist_table += fline + " " + self.widen(str(self.monitor_time)) \
                              + " DATAMARKER_freefrag_hist\n"
                 
        return (self.dict2table(sums_dict), hist_table)

        
    def dump_extents(self, filepath):
        cmd = "debugfs " + self.devname + " -R 'dump_extents " + filepath + "'"
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
                if len(tokens) == 8:
                    # there is no physical end
                    tokens.insert(7, "NA") #TODO: this is dangerous

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
        
    def getAllExtentStatsSTRSTR(self, rootdir="."):
        ret = self.getAllExtentStatsSTR(rootdir=rootdir)
        extstats_str = ret['extstats_str']
        fs_nmetablocks = ret['fs_nmetablocks']
        fs_ndatablocks = ret['fs_ndatablocks']

        fssum = "fs_nmetablocks fs_ndatablocks monitor_time HEADERMARKER_extstatssum\n"
        items = [fs_nmetablocks, fs_ndatablocks, self.monitor_time, 'DATAMARKER_extstatssum']
        items = [self.widen(str(x)) for x in items]
        fssum += " ".join(items) + '\n'
        
        return {'extstats_str':extstats_str, 'fssum':fssum}


    def getAllExtentStatsSTR(self, rootdir="."):
        stats = self.getAllExtentStats(rootdir)

        if len(stats) == 0:
            return ""
            
        header = ""
        for keyname in stats[0]:
            header += self.widen(keyname) + " "
        header += self.widen("monitor_time") + " HEADERMARKER_extstats\n"

        vals = ""
        fs_nmetablocks = 0
        fs_ndatablocks = 0
        for entry in stats:
            for keyname in entry:
                vals += self.widen(str(entry[keyname])) + " "
                if keyname == 'n_metablock':
                    fs_nmetablocks += int( entry[keyname] )
                elif keyname == 'n_datablock':
                    fs_ndatablocks += int( entry[keyname] )
                else:
                    pass
            vals += self.widen(str(self.monitor_time)) + " DATAMARKER_extstats\n"
        
        extstats_str = header + vals

        retdic = {'extstats_str':extstats_str,
                  'fs_nmetablocks': fs_nmetablocks,
                  'fs_ndatablocks': fs_ndatablocks}
        return retdic
        
    def widen(self, s):
        return s.ljust(self.col_width)

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

    def display(self, savedata=False, logfile="", monitorid="", jobid="myjobid"):
        self.resetMonitorTime(monitorid=monitorid)

        ext_ret = self.getAllExtentStatsSTRSTR()
        extstats = self.addCol( ext_ret['extstats_str'],
                                "jobid", jobid )
        extstatssum = self.addCol( ext_ret['fssum'],
                                "jobid", jobid)

        frag = self.e2freefrag()
        freespaces = self.dumpfsSTR()
        
        extstats_header = "-----------  Extent statistics  -------------\n"
        frag0_header    = "-----------  Extent summary  -------------\n"
        frag1_header    = "----------- Extent Histogram   -------------\n"
        dumpfs_header   = "----------- Dumpfs Header ------------\n"
        print "........working on monitor............"
        #print extstats_header, ext_ret['fssum']
        #print extstats_header, extstats,
        #print frag0_header, frag[0]
        #print frag1_header, frag[1]
        #print dumpfs_header, freespaces
        

        if savedata: 
            if logfile == "":
                filename = self.monitor_time + ".result"
            else:
                filename = logfile
            fullpath = os.path.join(self.logdir, filename)
            f = open(fullpath, 'w')
            f.write(extstats_header + extstats)
            f.write(extstatssum)
            f.write(frag0_header + self.addCol(frag[0], 'jobid', jobid))
            f.write(frag1_header + self.addCol(frag[1], 'jobid', jobid))
            f.write(dumpfs_header + self.addCol(freespaces['freeblocks'], 'jobid', jobid))
            f.write(dumpfs_header + self.addCol(freespaces['freeinodes'], 'jobid', jobid))
            f.flush()
            f.close()
        return

    def addCol(self, table, colname, val):
        "add a col to table with same val"
        lines = table.splitlines()
        for i, line in enumerate(lines):
            if i == 0:
                lines[i] += " " + self.widen(colname)
            else:
                lines[i] += " " + self.widen(str(val))
        return '\n'.join(lines)+'\n'

#fsmon = FSMonitor("/dev/sdb1", "/mnt/scratch")
#fsmon.display(savedata=True)

