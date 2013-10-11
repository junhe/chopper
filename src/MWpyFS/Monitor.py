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
from time import strftime, localtime, sleep
import re
import shlex
import os
import pprint

import dataframe

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
        self.resetJobID()
    
    def resetMonitorTime(self, monitorid=""):
        "monitor_time is used to identify each data retrieval"
        if monitorid == "":
            self.monitor_time = strftime("%Y-%m-%d-%H-%M-%S", localtime())
        else:
            self.monitor_time = monitorid

    def resetJobID(self, jobid="DefaultJOBID"):
        self.jobid = jobid

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

        # initialize
        freeblocks_df = dataframe.DataFrame(header=['start', 'end'],
                                           table=freeblocks)
        freeinodes_df = dataframe.DataFrame(header=['start', 'end'],
                                           table=freeinodes)

        # add additional columns 
        freeblocks_df.addColumn(key="monitor_time",
                                       value=self.monitor_time)
        freeblocks_df.addColumn(key="jobid",
                                       value=self.jobid)
        freeblocks_df.addColumn(key="HEADERMARKER_freeblocks",
                                       value="DATAMARKER_freeblocks")

        freeinodes_df.addColumn(key="monitor_time",
                                       value=self.monitor_time)
        freeinodes_df.addColumn(key="jobid",
                                       value=self.jobid)
        freeinodes_df.addColumn(key="HEADERMARKER_freeinodes",
                                       value="DATAMARKER_freeinodes")

        return {"freeblocks":freeblocks_df, "freeinodes":freeinodes_df}

    def e2freefrag(self):
        cmd = ["e2freefrag", self.devname]
        proc = subprocess.Popen(cmd,
                           stdout=subprocess.PIPE)
        proc.wait()

        part = 0
        sums_dict = {}
        hist_table = ""
        hist_df = dataframe.DataFrame()
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
                    hist_table = "Extent_start Extent_end  Free_extents   Free_Blocks  Percent"
                    hist_df.header = hist_table.split()
                    continue
                fline = re.sub(r'[\-:\n]', "", line)
                fline = re.sub(r'\.{3}', "", fline)
                row = fline.split()
                hist_df.addRowByList(row)

        hist_df.addColumns(keylist = ["HEADERMARKER_freefrag_hist",
                                      "monitor_time",
                                      "jobid"],
                           valuelist = ["DATAMARKER_freefrag_hist",
                                        self.monitor_time,
                                        self.jobid])

        # convert dict to data frame
        sums_df = dataframe.DataFrame(header=sums_dict.keys(),
                                      table=[sums_dict.values()])
        sums_df.addColumn(key="HEADERMARKER_freefrag_sum",
                          value="DATAMARKER_freefrag_sum")
        sums_df.addColumn(key="monitor_time",
                          value=self.monitor_time)
        sums_df.addColumn(key="jobid",
                          value=self.jobid)
                                      
                 
        return {"FragSummary":sums_df, "ExtSizeHistogram":hist_df}

   
    def imap_of_a_file(self, filepath):
        cmd = "debugfs " + self.devname + " -R 'imap " + filepath + "'"
        print cmd, '......'
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

        imapdict = {}
        for line in proc.stdout:
            #print line
            if "block group" in line:
                nums = re.findall(r'\d+', line)
                if len(nums) != 2:
                    print "Error parsing imap"
                    exit(1)
                imapdict['inode_number'] = nums[0] 
                imapdict['group_number'] = nums[1]
            elif 'located at block' in line:
                items = line.split()
                imapdict['block_number'] = items[3].rstrip(',')
                imapdict['offset_in_block'] = items[5]

        proc.wait()
        #print imapdict
        return imapdict


    def dump_extents_of_a_file(self, filepath):
        "This function only gets ext list for this file"
        
        cmd = "debugfs " + self.devname + " -R 'dump_extents " + filepath + "'"
        print cmd, '......'
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

        ext_list = [] # Use list here in case I want to extract data in Python
        header = []

        max_level = 0
        df_ext = dataframe.DataFrame()
        header = ["Level_index", "Max_level", 
                 "Entry_index", "N_Entry",
                 "Logical_start", "Logical_end",
                 "Physical_start", "Physical_end",
                 "Length", "Flag"]
        df_ext.header = header
        for line in proc.stdout:
            #print "LLL:", line,
            if "Level" in line:
                pass
            else:
                savedline = line
                line = re.sub(r'[/\-]', " ", line)
                tokens = line.split()
                if len(tokens) == 8:
                    # there is no physical end
                    tokens.insert(7, tokens[6]) #TODO: this is dangerous

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
                
                df_ext.addRowByDict(d)

        proc.wait()


        # Put the location of the inode the df_ext, level_index as -1 to
        # indicate that it is a inode

        imapdict = self.imap_of_a_file(filepath)
        d = {}
        d['Level_index'] = '-1'
        d['Max_level'] = '-1'
        d['Entry_index'] = 'NA'
        d['N_Entry'] = 'NA'
        d['Logical_start'] = 'NA'
        d['Logical_end'] = 'NA'
        d['Physical_start'] = imapdict['block_number']
        d['Physical_end'] = imapdict['block_number']
        d['Length'] = '1'
        d['Flag'] = 'NA'

        df_ext.addRowByDict(d)

        df_ext.addColumn(key = "filepath",
                         value = filepath)
        df_ext.addColumn(key = "HEADERMARKER_extlist",
                         value = "DATAMARKER_extlist")
        df_ext.addColumn(key = "jobid",
                         value = self.jobid)
        df_ext.addColumn(key = "monitor_time",
                         value = self.monitor_time)

        return df_ext

    def setBlock(self, blockn, count):
        cmd = "debugfs " + self.devname + \
                " -w -R 'setb " + str(blockn) + " " + str(count) + "'"
        cmd = shlex.split(cmd)

        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
        proc.wait()
        return proc.returncode

    def isAllBlocksInUse(self, blockn, count):
        "if any of the blocks is not in use, return false. return true otherwise"
        cmd = "debugfs " + self.devname + \
                " -w -R 'testb " + str(blockn) + " " + str(count) + "'"
        cmd = shlex.split(cmd)

        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

        for line in proc.stdout:
            if 'not' in line:
                return False
        proc.wait()

        return True



    def dumpextents_sum(self, filepath):
        "TODO: merge this with dump_extents_of_a_file()"
        cmd = "debugfs " + self.devname + " -R 'dump_extents " + filepath + "'"
        print cmd, "........."
        cmd = shlex.split(cmd)

        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

        header = []
        n_entries = [0] * 3 # n_entries[k] is the number of entries at level k
                            # it can be used to calculate number of 
                            # internal/leaf nodes
        max_level = 0
        exttable = ""
        header = ["Level_index", "Max_level", 
                 "Entry_index", "N_Entry",
                 "Logical_start", "Logical_end",
                 "Physical_start", "Physical_end",
                 "Length", "Flag"]
        for line in proc.stdout:
            #print "LLL:", line,
            if "Level" in line:
                pass
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
                
        print "..... finished stdout parsing .... "
        proc.terminate()
        print "..... after terminating .... "



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
    
        print "Reached end of debugfs...."
        return dumpdict

    def filefrag(self, filepath):
        fullpath = os.path.join(self.mountpoint, filepath)  
        cmd = ["filefrag", "-sv", fullpath]
        print cmd
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

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

            for line in proc.stdout:
                paths.append(line.replace("\n", ""))
            proc.wait()
            
        return paths

    def getExtentList_of_a_dir(self, rootdir="."):
        files = self.getAllInodePaths(rootdir)
        df = dataframe.DataFrame()
        for f in files:
            if len(df.header) == 0:
                df = self.dump_extents_of_a_file(f)
            else:
                df.table.extend( self.dump_extents_of_a_file(f).table )
        return df


    def getPerFileBlockCounts(self, rootdir="."):
        files = self.getAllInodePaths(rootdir)
        counts_df = dataframe.DataFrame()
        for f in files:
            d = self.dumpextents_sum(f) 
            if len(counts_df.header) == 0:
                counts_df.header = d.keys()
            counts_df.addRowByDict(d)

        counts_df.addColumns(keylist=["HEADERMARKER_extstats",
                                     "monitor_time",
                                     "jobid"],
                            valuelist=["DATAMARKER_extstats",
                                     self.monitor_time,
                                     self.jobid])
           
        return counts_df
        
    def getFSBlockCount(self, df_files):
        "df_files has number of metablocks datablocks of each file"
        if len(df_files.table) == 0:
            return ""

        fs_nmetablocks = 0
        fs_ndatablocks = 0
        nmetaindex = df_files.header.index('n_metablock')
        ndataindex = df_files.header.index('n_datablock')

        for row in df_files.table:
            fs_nmetablocks += int(row[nmetaindex])
            fs_ndatablocks += int(row[ndataindex])

        headerstr = "fs_nmetablocks fs_ndatablocks monitor_time HEADERMARKER_extstatssum jobid"
        valuelist = [fs_nmetablocks, fs_ndatablocks, self.monitor_time, 
                    'DATAMARKER_extstatssum', self.jobid]
        fsblkcount_df = dataframe.DataFrame(
                            header=headerstr.split(),
                            table=[valuelist])
        return fsblkcount_df

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
        self.resetJobID(jobid=jobid)

        if savedata: 
            if logfile == "":
                filename = self.monitor_time + ".result"
            else:
                filename = logfile
            fullpath = os.path.join(self.logdir, filename)
            f = open(fullpath, 'w')


        ######################
        # get per file block count
        df_bcounts = self.getPerFileBlockCounts()
        if savedata:
            extstats_header = "----------- per file block counts  -------------\n"
            f.write(extstats_header + df_bcounts.toStr())

        # FS block count
        df_fscounts = self.getFSBlockCount(df_bcounts)
        if savedata:
            h = "------------- FS block counts ---------------\n"
            f.write(h+df_fscounts.toStr())
        
        ######################
        # get extents of all files
        extlist = self.getExtentList_of_a_dir()
        if savedata:
            h = "---------------- extent list -------------------\n"
            f.write(h+extlist.toStr())

        ######################
        # e2freefrag
        frag = self.e2freefrag()
        if savedata:
            frag0_header    = "-----------  Extent summary  -------------\n"
            frag1_header    = "----------- Extent Histogram   -------------\n"
            f.write(frag0_header + frag["FragSummary"].toStr())
            f.write(frag1_header + frag["ExtSizeHistogram"].toStr())

        ######################
        # dumpfs
        freespaces = self.dumpfs()
        if savedata:
            dumpfs_header   = "----------- Dumpfs Header ------------\n"
            f.write(dumpfs_header + freespaces['freeblocks'].toStr())
            f.write(dumpfs_header + freespaces['freeinodes'].toStr())

        
        if savedata:
            f.flush()
            f.close()
        return


# Testing
m = FSMonitor('/dev/loop0', '/mnt/loopmount/')
#m.imap_of_a_file('./pid00000.dir00000/pid.00000.file.00000')
print m.dump_extents_of_a_file('./pid00000.dir00000/pid.00000.file.00000').toStr()

