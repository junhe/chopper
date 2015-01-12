# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import re
import pprint
import subprocess
import dataframe
import Queue

# sample lines for debugging
lines01="""
u = (empty)
"""

lines02="""
next_unlinked = null
u.bmbt.level = 1
u.bmbt.numrecs = 1
u.bmbt.keys[1] = [startoff] 1:[0]
u.bmbt.ptrs[1] = 1:12299
"""

lines03="""
magic = 0x424d4150
level = 1
numrecs = 14
leftsib = null
rightsib = null
keys[1-14] = [startoff] 1:[0] 2:[721600] 3:[924800] 4:[1128000] 5:[1331200] 6:[1534400] 7:[1737600] 8:[1940800] 9:[2144000] 10:[2347200] 11:[2550400] 12:[2753600] 13:[2956800] 14:[3073600]
ptrs[1-14] = 1:196428 2:917764 3:918019 4:918274 5:918529 6:918784 7:919039 8:919294 9:919549 10:919804 11:920060 12:920315 13:920570 14:920825
"""


lines04="""
magic = 0x424d4150
level = 0
numrecs = 254
leftsib = null
rightsib = 917764
recs[1-254] = [startoff,startblock,blockcount,extentflag] 1:[0,12,16,0] 2:[800,44,16,0] 3:[1600,844,512,0] 4:[2400,1868,1024,0] 5:[4000,3916,2048,0] 6:[6400,8012,4096,0] 7:[11200,16204,8192,0] 8:[20000,32588,16384,0] 9:[36800,65356,32768,0] 10:[69600,130892,65536,0] 
"""


def xfs_lines_to_dict(lines):
    "Convert lines like 'key = value' to a dict "
    lines = lines.split('\n')

    # put each line to a dicitionary
    line_dict = {}
    for line in lines:
        #print line
        if "=" in line:
            items = line.split("=")
            assert len(items) == 2

            key = items[0]
            key = key.strip()
            key = re.sub(r'\[.*\]$', "", key, re.M)

            value = items[1]
            value = value.strip()

            assert not line_dict.has_key(key)
            line_dict[key] = value

    #pprint.pprint(line_dict)
    return line_dict

def xfs_empty_u(line_dict):
    if line_dict.has_key('u') and line_dict['u'] == "(empty)":
        return True
    else:
        return False

def xfs_parse_type01(keystr):
    """ it can parse:
            u.bmbt.keys[1] = [startoff] 1:[0]
            keys[1-14] = [startoff] 1:[0] 2:[721600] 3:[924800] ....
        The return is ['0', '721600', '924800', '1128000',....
    """
    keys = re.findall(r'\d+:\[(\d+)\]', keystr)
    return keys

def xfs_parse_type02(ptrstr):
    ptrs = re.findall(r'\d+:(\d+)', ptrstr)
    return ptrs

def xfs_parse_type03(recstr):
    "The return is: [(x,x,x,x), (x,x,x,x), ...]"
    recs = re.findall(r'\d+:\[(\d+),(\d+),(\d+),(\d+)\]', recstr)
    return recs

def xfs_db_commands(commandlist, devname):
    #print "xfs_db..."
    cmdlist = ["-c "+cmd for cmd in commandlist ]
    #print cmdlist
    cmd = ["xfs_db", "-r"] + cmdlist + [devname]
    #print cmd
    #cmd = ["xfs_db", "-r", "-c convert ino 131 fsblock", "/dev/loop0"]
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE)
    output = proc.communicate()[0] # communicate() uses buffer. Don't use it
                                   # when the data is large
    return output

def xfs_convert_ino_to_fsb(ino, devname):
    "convert inode number to fs block number"
    lines = xfs_db_commands(['convert ino '+str(ino)+' fsblock'], devname)
    lines = lines.strip()
    lines = lines.split('\n')

    assert len(lines)==1, "# of lines not right"
    
    for line in lines:
        #print line,
        mo = re.search( r'\((\d+)\)', line, re.M)
        if mo:
            fsb = mo.group(1)
            return fsb

    assert False, "Failed to convert inode number"

def _dataframe_add_an_extent(df, 
                                Level_index, Max_level,
                                Entry_index, N_Entry,
                                Logical_start, Logical_end,
                                Physical_start, Physical_end,
                                Length, Flag):
    d = {}
    d['Level_index'] = Level_index
    d['Max_level'] = Max_level
    d['Entry_index'] = Entry_index
    d['N_Entry'] = N_Entry
    d['Logical_start'] = Logical_start
    d['Logical_end'] = Logical_end
    d['Physical_start'] = Physical_start
    d['Physical_end'] = Physical_end
    d['Length'] = Length
    d['Flag'] = Flag
    df.addRowByDict(d)
    return df

def _dataframe_add_ext_tuple(df, level_index, max_level, ext):
    "ext is a tuple (startoff, startblock, blockcount, extentflag)" 
    assert len(ext)==4
    logical_start = int(ext[0])
    physical_start = int(ext[1])
    length = int(ext[2])
    flag = ext[3]

    df = _dataframe_add_an_extent(df, 
                                Level_index=level_index, Max_level=max_level,
                                Entry_index="NA", N_Entry="NA",
                                Logical_start=logical_start, 
                                Logical_end=logical_start+length-1, # the last block within the extent
                                Physical_start=physical_start, 
                                Physical_end=physical_start+length-1,
                                Length=length, Flag=flag)
    return df


def xfs_get_extent_tree(inode_number, devname):
    inode_lines = xfs_db_commands(["inode "+str(inode_number), "print u"], 
                                  devname)
    print inode_lines
    inode_dict = xfs_lines_to_dict(inode_lines)
    pprint.pprint(inode_dict)

    df_ext = dataframe.DataFrame()
    header = ["Level_index", "Max_level", 
             "Entry_index", "N_Entry",
             "Logical_start", "Logical_end",
             "Physical_start", "Physical_end",
             "Length", "Flag"]
    df_ext.header = header

    # Find out the fsb of the inode
    inode_fsb = xfs_convert_ino_to_fsb(inode_number, devname)
    df_ext = _dataframe_add_an_extent(df_ext, 
                                Level_index="-1", Max_level="-1",
                                Entry_index="NA", N_Entry="NA",
                                Logical_start="NA", Logical_end="NA",
                                Physical_start=inode_fsb, Physical_end=inode_fsb,
                                Length='1', Flag='NA')

        
    if inode_dict.has_key('u.bmx'):
        print "All extents pointers are in inode"
        exts = xfs_parse_type03(inode_dict['u.bmx'])
        #print "exts",exts
        for ext in exts:
            df_ext = _dataframe_add_ext_tuple(df_ext, level_index=0, max_level=0, ext=ext)
        return df_ext

    if inode_dict.has_key('u.bmbt.level'):
        # in this case, we have a B+tree
        max_level = int(inode_dict['u.bmbt.level'])
        cur_xfs_level = int(inode_dict['u.bmbt.level'])
        ptrs = xfs_parse_type02( inode_dict['u.bmbt.ptrs'] ) # the root of B+Tree


        # Initialize the tree for traversing
        ptr_queue = Queue.Queue()
        for p in ptrs:
            ptr_queue.put_nowait(p)
            df_ext = _dataframe_add_an_extent(df_ext, 
                            Level_index=max_level-cur_xfs_level, Max_level=max_level,
                            Entry_index="NA", N_Entry="NA",
                            Logical_start="NA", Logical_end="NA",
                            Physical_start=p, Physical_end=p,
                            Length='1', Flag='NA')

        while not ptr_queue.empty():
            cur_blk = ptr_queue.get_nowait()
            block_lines = xfs_db_commands(["fsb "+str(cur_blk), "type bmapbta", "p"], 
                                  devname)
            #print "********* block_lines  *******"
            #print block_lines
            block_attrs = xfs_lines_to_dict(block_lines)

            cur_xfs_level = int(block_attrs['level'])

            if cur_xfs_level > 0:
                # This is still an internal node of the tree
                # It has pointers in ptrs
                ptrs = xfs_parse_type02( block_attrs['ptrs'] )
                for p in ptrs:
                    ptr_queue.put_nowait(p)
                    df_ext = _dataframe_add_an_extent(df_ext, 
                                    Level_index=max_level-cur_xfs_level, Max_level=max_level,
                                    Entry_index="NA", N_Entry="NA",
                                    Logical_start="NA", Logical_end="NA",
                                    Physical_start=p, Physical_end=p,
                                    Length='1', Flag='NA')
            else:
                # This is a leaf of the tree
                # The data extents are in recs[]
                exts = xfs_parse_type03( block_attrs['recs'] ) 
                #print exts
                for ext in exts:
                    df_ext = _dataframe_add_ext_tuple(df_ext, 
                                        level_index=max_level-cur_xfs_level,
                                        max_level=max_level, 
                                        ext=ext)

        return df_ext
    # It is empty
    return df_ext

def xfs_bmap_of_a_file (self, filepath):
    "find all extents of a file in xfs by inode number"
    cmd = 'xfs_bmap -v ' + filepath 
    cmd = shlex.split(cmd)

    print cmd
    proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)
    
    lines = proc.communicate()[0]
    lines = lines.strip()
    lines = lines.split('\n')

    #print "------------------------"
    #print lines
    df_ext = dataframe.DataFrame()
    header = ["Level_index", "Max_level", 
             "Entry_index", "N_Entry",
             "Logical_start", "Logical_end",
             "Physical_start", "Physical_end",
             "Length", "Flag"]       
    df_ext.header = header

    for i, line in enumerate(lines):
        #print line
        if i < 2:
            # skip the header line
            continue
        nums = re.findall(r'\d+', line, re.M)
        assert len(nums) == 9, "xfs_bmap, number parsing failed"

        d = {
                "Level_index":"NA",
                "Max_level"  :"NA",
                "Entry_index":"NA",
                "N_Entry"    :"NA",
                # this output of xfs_bmap is in 512 byte block
                # we convert it to use 4096 byte block by
                # blocknumber * 512/4096=blocknumber/8
                "Logical_start": int(nums[1])/8,
                "Logical_end": int(nums[2])/8,
                "Physical_start": int(nums[3])/8,
                "Physical_end": int(nums[4])/8,
                "Length": int(nums[8])/8,
                "Flag": "NA"
                }
        df_ext.addRowByDict(d)
    #print df_ext.toStr()

    inode_number = self.stat_a_file(filepath)['inode_number']
    inode_fsb = self.xfs_convert_ino_to_fsb(int(inode_number))
    d = {}
    d['Level_index'] = '-1'
    d['Max_level'] = '-1'
    d['Entry_index'] = 'NA'
    d['N_Entry'] = 'NA'
    d['Logical_start'] = 'NA'
    d['Logical_end'] = 'NA'
    d['Physical_start'] = inode_fsb
    d['Physical_end'] = inode_fsb
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

def main():
    #d = xfs_parse_lines(lines04)
    #xfs_parse_keys(d['keys'])
    #print xfs_parse_ptrs(d['ptrs'])
    #print xfs_parse_recs(d['recs'])
    #print xfs_parse_empty_u(d)
    #xfs_parse_lines(lines02)
    #lines = xfs_db_commands(["inode 132", "p"], "/dev/loop0")
    print xfs_get_extent_tree(132, "/dev/loop0").toStr()


if __name__ == "__main__":
    #main()
    pass

