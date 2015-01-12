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

# This module uses # pat_data_struct and pattern_iter to create new types
# of workloads.
# We should keep pat_data_struct and pattern_iter more
# constant and put flexible things in this module.

import pat_data_struct
import pattern_iter
import copy
import pprint
import itertools
import math
import ConfigParser
import os

def build_dir_tree_chkeq( depth, startlevel ):
    dirpaths = build_dir_tree_path( depth, startlevel)

    chkseq = pat_data_struct.get_empty_ChunkSeq() 

    for dirpath in dirpaths:
        cbox = pat_data_struct.get_empty_ChunkBox2()
        op = {
                'opname':'mkdir',
                'optype':'dir',
                'opvalue':dirpath
             }
        # yes, I only put one operation to a chunkbox
        cbox['opseq'] = [op]
        chkseq['seq'].append(cbox)
    return chkseq
        
def dir_level (dirid):
    # given a dirid, it tells you which level the 
    # dir is at
    #      0 ----- level 0
    #    1   2  --- level 1
    #  3  4 5  6  -- level 2
    for level in range(32):
        if 2**level - 1 <= dirid and \
                dirid < 2**(level+1) -1 :
            return level
    return None

def get_dir_path (dirid, startlevel):
    """
    dirid is the in index in the breadth-first
    traversal
    """
    if dirid == 0:
        return ""

    path = [dirid]
    # put parents to path
    # root (0) does not need to be put in it
    parent = (dirid - 1)/2
    while parent > 0 :
        path.insert(0, parent)
        parent = (parent - 1)/2
    
    path = [ x for x in path if dir_level(x) >= startlevel ]
    path = "/".join( ['dir.'+str(x) for x in path] )
    return path

def build_dir_tree_path( depth, startlevel ):
    """
    depth: The depth of a node is the number of edges 
           from the root to the node.

    return: a list of paths, each is a path of a dir

    The dirs are named by their index in breadth-first-order
    traversal.
    For example, if the depth of the binary tree is
    2, we have 7 directories. The root is 0. We have
    6 extra directories to make:
           0
        1      2 
      3   4   5  6  
    The major job of this function is to create paths:
    /1
    /1/3
    /1/4
    /2
    /2/5
    /2/6
    Note that the root does not need to be created.
    """
    dirpaths = []
    n = 2**(depth+1) - 1 
    for dirid in range(1, n):
        path = get_dir_path(dirid, startlevel)
        if path != "":
            dirpaths.append( path )

    return dirpaths

def get_ladder_dir_path( dirid ):
    if dirid == 0:
        return ""

    dirs = range(1, dirid+1)
    dirs = [ 'dir.'+str(dir) for dir in dirs ]
    ret = '/'.join(dirs)
    return ret

def build_conf ( treatment, confparser ):
    """
    This function build a confparser from the treatment. 
    The treatment contains values for different factors.
    Refer to ** Design the experiment for the paper ** in 
    Evernote for more details.
    Note that this function only takes one treatment (a
    point on the region). The distribution of the treatments
    are controlled out of this function. 

    Implementing factors in treatment:
    1. n_dir_depth: we name the directory tree by the index
       of directory in the pre-order traversal. No two dir names
       are the same. 

    treatment = {
                  filesystem:
                  disksize  :
                  free_space_layout_score:
                  free_space_ratio:
                  n_dir_depth:
                  # file id in file_treatment is the index here
                  files: [file_treatment0, file_treatment1, ..],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  filechunk_order: [0, 2, 1, fileid,..]
                }
                  
    Here I utilize the convenient structure of confparser to store treatment
    info.
    """
    
    if not confparser.has_section('system'):
        confparser.add_section('system')
    if not confparser.has_section('workload'):
        confparser.add_section('workload')

    confparser.set('system', 'filesystem', treatment['filesystem'])
    confparser.set('system', 'disksize'  , str(treatment['disksize']))
    confparser.set('system', 'disk_used',
                                   str(treatment['disk_used']))
    confparser.set('system', 'makeloopdevice', 'yes')
    confparser.set('system', 'layoutnumber', 
                    str(treatment['layoutnumber']))
    confparser.set('system', 'mountopts', treatment['mountopts'])
    confparser.set('system', 'core.count', str(treatment['core.count']))

    chkseq = pat_data_struct.get_empty_ChunkSeq()

    # creat directory tree
    dirs_chkseq = build_dir_tree_chkeq( treatment['dir_depth'], 
                                        treatment['startlevel'] )
    chkseq['seq'].extend( dirs_chkseq['seq'] )
   
    # Get chunkseq for each file
    nfiles = len( treatment['files'] )
    files_chkseq_list = []
    for file_treatment in treatment['files']:
        file_treatment['startlevel'] = treatment['startlevel']
        files_chkseq_list.append( 
                    build_file_chunkseq( file_treatment ) )

    # mix the chunks of all files
    ckpos = [0] * nfiles
    for curfile in treatment['filechunk_order']:
        # curfile is not file id.
        # it is the position in files_chkseq_list
        chkseq['seq'].append( 
                files_chkseq_list[curfile]['seq'][ ckpos[curfile] ])
        ckpos[curfile] += 1
    
    confparser.set('workload', 'files_chkseq', str(chkseq))
        
def build_file_chunkseq ( file_treatment ):
    """
    *********************************************
    PROVIDE ONLY THE MECHANISM, LEAST POLICY HERE
    TIRED IMPLEMENTING SIMILAR MECHANISM FOR DIFFERENT POLICIES
    *********************************************

    file_treatment = {
           parent_dirid :
           fileid       : make this globally unique
           writer_pid   : writer pid
           (DEL)overlap : This one should be specified out of this
                          function. It changes chunks
           chunks       : [{'offset':, 'length':},{}]  
                          #chunk id is the index here
           write_order  : [0,1,2,3,..]
           # The bitmaps apply to ordered chunkseq
           open_bitmap  : [True, .. ]
           fsync_bitmap : [True, False, ...]
           close_bitmap : [True, .. ]
           sync_bitmap  : [True, .. ]
           writer_cpu_map: [0,1,0,1] # set affinity to which cpu, 
                                     # -1 means not schedule explicitly
           }
    This function returns a chunkseq of this treatment
    """
    # logical space (setup chunkseq)
    nchunks = len(file_treatment['write_order'])
   
    chunkseq = pat_data_struct.get_empty_ChunkSeq()
    for pair in file_treatment['chunks']:
        cbox = pat_data_struct.get_empty_ChunkBox2()
        cbox['chunk']['offset'] = pair['offset'] 
        cbox['chunk']['length'] = pair['length']
        cbox['chunk']['fileid'] = file_treatment['fileid']
        cbox['chunk']['parent_dirid'] = file_treatment['parent_dirid']
        cbox['chunk']['filepath'] = os.path.join(
                #get_ladder_dir_path(file_treatment['parent_dirid']),
                get_dir_path(file_treatment['parent_dirid'],
                             file_treatment['startlevel']
                    ),
                str( file_treatment['fileid'] ) + ".file" )
        cbox['chunk']['writer_pid'] = file_treatment['writer_pid']
        chunkseq['seq'].append( cbox )

    # Order it
    chunkseq['seq'] = [ chunkseq['seq'][i] \
                        for i in file_treatment['write_order'] ]

    # apply the bitmaps
    slotnames = ['A', '(', 'C', 'F', ')', 'S']
    opbitmap = pat_data_struct.get_empty_OpBitmap()
    opbitmap['nchunks'] = nchunks
    for writer_cpu, open_bit, fsync_bit, close_bit, sync_bit\
            in zip( 
                    file_treatment['writer_cpu_map'],
                    file_treatment['open_bitmap'], 
                    file_treatment['fsync_bitmap'], 
                    file_treatment['close_bitmap'],
                    file_treatment['sync_bitmap'] ):
        # each iteration in the loop is for a chunk
        d = {
             'A': writer_cpu,
             '(': open_bit,
             'C': 'C',
             'F': fsync_bit,
             ')': close_bit,
             'S': sync_bit
            }

        opbitmap['slotnames'].extend( slotnames )
        opbitmap['values'].extend( [ d[x] for x in slotnames ] )

    #pprint.pprint(opbitmap)
    pattern_iter.assign_operations_to_chunkseq( chunkseq, opbitmap )
    return chunkseq


if __name__ == '__main__':
    for i in range(20):
        print i, dir_level(i)

