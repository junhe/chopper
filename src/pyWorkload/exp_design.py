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

import chpConfig
import itertools
from ast import literal_eval
from ConfigParser import SafeConfigParser
import copy
import sys
import os
import pprint
import workload_builder
import random
import math

def get_x_th_percentile(objlist, x):
    """
    x(th)%, x is in range of [0,100],
    it would be more fair if it is [0,100)
    """
    nseg = len(objlist)
    segsize = 100.0/nseg
    segindex = int(x/segsize)
    if segindex == nseg:
        segindex -= 1
    return objlist[segindex]


def get_dirlist(nfiles, dirspan, startlevel):
    # find out the percentile of each file
    startdir = 2**startlevel -1

    if nfiles == 1:
        xths = [100]
    else:
        step = 100.0/(nfiles-1)
        xths = [ step*i for i in range(nfiles) ]

    dirlist = range(startdir, startdir+dirspan)
    #if len(dirlist) > 0 and dirlist[0] != 0:
        #dirlist = [0] + dirlist
    #print 'dirspan', dirspan
    #print 'dirlist', dirlist

    dirs = [ get_x_th_percentile(dirlist, x) for x in xths ]
    return dirs

def read_design_file_blhd_fixednchunks(filepath):
    "put the design to a list"
    f = open(filepath, 'r')
    id = 0
    header = None
    table = []
    for line in f:
        items = line.split()
        if len(items) == 0:
            continue
        if id == 0:
            header = items
            id += 1
            continue
        d = {}
        for i, name in enumerate(header):
            try:
                d[name] = items[i]
            except:
                print line
                print header
        table.append(d)
    f.close()

    return table

def pick_by_level(levelstr, factor_range):
    count = len(factor_range)
    assert count > 0
    i = int(eval(str(count)+'*'+levelstr))
    if i == count:
        # if the index goes beyond range, pull it back 
        i -= 1
    ret = factor_range[i]
    return ret

def row_to_recipe(design_row):
    recipe = {}
    
    space_dic = get_factor_spaces()
    
    # pick one
    for k,space in space_dic.items():
        recipe[k] = pick_by_level( design_row[k], space )

    return recipe

def recipe_to_treatment(recipe, optsdict=None):
    """
    recipe is a configuration that will be implmented
    by the underlying treatment mechanism. 
    receipe is intended to be parameters of one setting
    from our experimental design.
    
    recipe is a dictionary. It is the levels we pick
    by our experimental design.
    recipe = {
        num.chunks   
        disk.size     
        disk.used   
        dir.span(was dir.id)
        file.size   
        fullness     
        num.cores    
        fsync
        sync   
        chunk.order
        num.files
        }
    """
    ###############################################
    ###############################################
    ###############################################
    r = recipe # for short

    # hard tunables 
    nrealcores = 2
    dir_depth  = 4 # we'll have level 0,1,2,3,4
    startlevel = 2

    # get a nicer looking
    nchunks    = r['num.chunks']
    file_size  = r['file.size']
    fullness   = r['fullness']
    n_virtual_cores = r['num.cores']
    nfiles     = r['num.files']

    # The code is no longer used.
    # figure out the cpu map by n_virtual_cores
    writer_cpu_map  = list(
            itertools.repeat( range(n_virtual_cores), 
                       1+(nchunks/n_virtual_cores) ))
    writer_cpu_map = [ y for x in writer_cpu_map for y in x ]
    writer_cpu_map = writer_cpu_map[0:nchunks]
    writer_cpu_map = [ x % nrealcores for x in writer_cpu_map ]
    
    # we do not specifically put writing process to a core any more. 
    if optsdict != None and optsdict['enable_setaffinity'] == False:
        writer_cpu_map = [ -1 for x in writer_cpu_map ]

    # This defines what to do with a single file
    file_treatment = {
           'parent_dirid' : None, # will be assigned later in the function
           'fileid'       : 0,
           'writer_pid'   : 0,
           'chunks'       : [],
                          #chunk id is the index here
           'write_order'  : r['chunk.order'],
           # The bitmaps apply to ordered chunkseq
           'open_bitmap'  : [True]+r['sync'][0:nchunks-1],
           'fsync_bitmap' : r['fsync'],
           'close_bitmap' : r['sync'],
           'sync_bitmap'  : r['sync'],
           'writer_cpu_map': writer_cpu_map, # set affinity to which cpu
           # just for the purpose of record, not real effect.
           # the real effect is in writer_cpu_map
           'n_virtual_cores': n_virtual_cores, 
           'fullness'       : fullness,
           'filesize'       : file_size
           }

    chunksize = file_size/nchunks #be careful about rounding

    filetreatment_list = []
    fullnessLeft = fullness
    while fullnessLeft > 0:
        if fullnessLeft > 1:
            curfullness = 1
            fullnessLeft -= 1
        else:
            curfullness = fullnessLeft
            fullnessLeft = 0

        solid_region = int(chunksize * curfullness)
        hole = chunksize - solid_region
        file_treatment['chunks'] = []
        for i in range(nchunks):
            d = {
                 'offset': chunksize*i+hole,
                 'length': solid_region 
                }
            file_treatment['chunks'].append(d)
        filetreatment_list.append( 
                       copy.deepcopy(file_treatment) )


    filechunk_order = []
    for i,ft in enumerate(filetreatment_list):
        filechunk_order += [i]*len(ft['write_order'])
    # a round is a time you use a filetreatment for a fileid
    # you may use a fileid for many rounds.
    # This filerounds indicates the number rounds you used
    # a particular file id.
    filerounds = len(filetreatment_list)
    #[ x+k*off for x in l for k in range(off)  ]
    # make the files interleave
    filechunk_order = [ x+k*filerounds for x in filechunk_order \
                                        for k in range(nfiles) ]
    
    dirlist = get_dirlist(nfiles  = nfiles,
                          dirspan = r['dir.span'],
                          startlevel = startlevel
                          )
    #print dirlist
    nfiletreatment_list = []
    for filei, dirid in zip(range(nfiles), dirlist):
        # dirid is the dirid of filei
        ftreat_list = copy.deepcopy( filetreatment_list )
        # update file id
        for ftreat in ftreat_list:
            ftreat['fileid'] = filei
            ftreat['parent_dirid']  = dirid
        nfiletreatment_list.extend( ftreat_list )

    #filechunk_order = []
    #for i,filetreat in enumerate(filetreatment_list):
        #filechunk_order += [i] * len(filetreat['chunks'])
    
    if fullness > 1:
        unique_bytes = nfiles * file_size * 1
    else:
        unique_bytes = nfiles * file_size * fullness

    treatment = {
                  'filesystem': None, # will be replaced later
                  'disksize'  : r['disk.size'],
                  'disk_used'    : r['disk.used'],
                  'dir_depth'     : dir_depth,
                  # file id in file_treatment is the index here
                  'files': nfiletreatment_list,
                  # for display only, no effect
                  'num.files': nfiles,
                  'dir.span' : r['dir.span'],
                  #'files': [file_treatment],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  'filechunk_order': filechunk_order,
                  #'filechunk_order': [0,0,0,0]
                  'unique.bytes'   : unique_bytes,
                  'layoutnumber'   : r['layoutnumber'],
                  'startlevel'     : startlevel,
                  'core.count'     : n_virtual_cores
                }
    # shold not correct now, because I will write the 
    # same file many times
    #workload_builder.correctize_fileid(treatment)
    #pprint.pprint( treatment )
    return treatment


def get_factor_spaces():
    parser = chpConfig.parser # for short

    space_dic = {}

    space_dic['num.chunks']   = eval(parser.get('space', 'num.chunks'))
    assert len(space_dic['num.chunks']) == 1, \
            "We only support having one and only one chunk number"
    nchunks = space_dic['num.chunks'][0]

    binspace = itertools.product( [False, True], repeat=nchunks)
    binspace = [list(x) for x in binspace] 

    close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    close_sp = [ list(x)+[True] for x in close_sp ] # always close

    #space_dic['disk.size']    = [(2**x)*(2**30) for x in range(0, 7) ]
    space_dic['disk.size']    = eval(parser.get('space', 'disk.size'))
    #space_dic['disk.used']    = [0, 0.2, 0.4, 0.6] 
    space_dic['disk.used']    = eval(parser.get('space', 'disk.used'))
    #space_dic['dir.span']     = range(1,13) 
    space_dic['dir.span']     = eval(parser.get('space', 'dir.span'))
    #space_dic['file.size']    = [ x*1024 for x in range(8, 256+1, 8) ]
    space_dic['file.size']    = eval(parser.get('space', 'file.size'))
    #space_dic['fullness']     = [x/10.0 for x in range(2, 21, 2)]
    space_dic['fullness']     = eval(parser.get('space', 'fullness'))
    #space_dic['num.cores']    = [1,2]
    space_dic['num.cores']    = eval(parser.get('space', 'num.cores'))
    space_dic['fsync']        = binspace
    space_dic['sync']         = close_sp
    space_dic['chunk.order']  = list(itertools.permutations( range(nchunks) ))
    #space_dic['num.files']    = range(1,3)
    space_dic['num.files']    = eval(parser.get('space', 'num.files'))
    #space_dic['layoutnumber']    = range(1,7)
    space_dic['layoutnumber']    = eval(parser.get('space', 'layoutnumber'))
    #space_dic['num.chunks']   = [nchunks]

    return space_dic

def rawtable_to_recipe(raw_tb):
    for row in raw_tb:
        for k,v in row.items():
            #print k
            if k in ['fsync','sync']:
                row[k] = [bool(int(x)) for x in v]
            elif k in ['chunk.order']:
                row[k] = [int(x) for x in v]
            elif k in ['disk.size', 'dir.span',
                       'file.size', 'num.cores',
                       'num.files', 'layoutnumber',
                       'num.chunks']:
                row[k] = int(v)
            elif k in ['disk.used', 'fullness']:
                row[k] = float(v)
            #else:
                #print 'skipped key', k

    return raw_tb

def read_rawtable(filepath):
    "Read reproduce file and store them in a list of dictionaries"
    f = open(filepath)
    lines = f.readlines()
    f.close()

    if len(lines) <= 1:
        print 'no data in file', filepath
        exit(1)
    
    # first line is the table head  
    colnames = lines[0].split()
    treatments = []
    for line in lines[1:]:
        line  = line.strip()
        if len(line) == 0:
            continue
        d = {}
        values = line.split()
        for k,v in zip(colnames, values):
            d[k] = v
        treatments.append(d)
    return treatments

def reproducer_iter(rawtable_path):
    rtb = read_rawtable(rawtable_path)
    recipes = rawtable_to_recipe(rtb)

    mountopts = chpConfig.parser.get('setup', 'mountopts')

    for recipe in recipes:
        opts = {'enable_setaffinity':False} # alway set this to disable 
                                            # an depreted function
        treatment = recipe_to_treatment(recipe, optsdict=opts)
        treatment['filesystem'] = recipe['file.system']
        treatment['mountopts'] = mountopts
        yield treatment
        #pprint.pprint(treatment)


def fourbyfour_iter(design_path):
    design_table = read_design_file_blhd_fixednchunks(design_path)
    cnt = 0

    parser = chpConfig.parser

    fs = parser.get('setup', 'filesystem')
    mountopts = parser.get('setup', 'mountopts')

    for design_row in design_table:
        # recipe is a treatment with exact experiment config
        recipe = row_to_recipe( design_row )
        opts = {'enable_setaffinity':False} # alway set this to disable 
                                            # an depreted function
        treatment = recipe_to_treatment(recipe, optsdict=opts) 
        treatment['filesystem'] = fs
        treatment['mountopts'] = mountopts
        cnt += 1
        yield treatment
    
if __name__ == '__main__':
    # This part is only for testing.
    reproducer_iter('./tmp.txt')
    exit(0)
    #a = read_design_file_blhd_fixednchunks('../designs/sanity.test.design.txt')
    fourbyfour_iter('../designs/sanity.test.design.txt')
    exit(0)

    recipe = {
            'num.chunks': 2,
            'disk.size':  8,
            'disk.used':  2,
            'dir.span' :  32,
            'file.size':  4096,
            'fullness' :  1.5,
            'num.cores':  2,
            'fsync'    :  [True, True],
            'sync'     :  [True, True],
            'chunk.order': [0,1],
            'num.files'  : 2
        }
    pprint.pprint( recipe_to_treatment(recipe) )


    exit(0)

