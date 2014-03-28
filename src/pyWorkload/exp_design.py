import itertools
import copy
import sys
import os
import pprint
import workload_builder
import random
import math
##sys.path.append( os.path.abspath("..") )
#import pyWorkload

def read_design_file(filepath):
    """
    should put the total number of levels along with levels
quantative:
    chunk.number    disk.size   disk_used f.dir   file.size   fullness  w.number 
qualitative:
    fsync   sync    c.order
   """


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
            d[name] = int(items[i]) #let's start from 0
        table.append(d)

    f.close()

    quant_level = 4
    nlevels = {
            'disk.size'      : quant_level,
            'disk.used'      : quant_level,
            'dir.id'          : quant_level,
            'file.size'      : quant_level,
            'fullness'       : quant_level,
            'num.cores'       : quant_level
            }
    for row in table:
        nchunks = row['num.chunks']
        nlevels['fsync'] = 2**nchunks
        nlevels['sync']  = 2**(nchunks-1)
        nlevels['chunk.order'] = math.factorial(nchunks)

        for k,v in nlevels.items():
            row[k] = str(row[k]-1)+'/'+str(nlevels[k])
        
    #pprint.pprint( table )
    return table

def read_design_file_blhd(filepath):
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
                d[name] = items[i] #let's start from 0
            except:
                print line
                print header
        table.append(d)
    f.close()

    nlevels = {}
    for row in table:
        row['num.chunks'] = int(row['num.chunks'])
        nchunks = row['num.chunks']
        nlevels['fsync'] = 2**nchunks
        nlevels['sync']  = 2**(nchunks-1)
        nlevels['chunk.order'] = math.factorial(nchunks)

        for k,v in nlevels.items():
            row[k] = str(int(row[k])-1)+'/'+str(nlevels[k])

    #pprint.pprint( table )
    return table

def dir_distance_iter():
    """
    Each yield is a treatment
    """
    file_treatment = {
           'parent_dirid' : -1,
           'fileid'       : 8848,
           'writer_pid'   : 1,
           'chunks'       : [
                           {'offset':0, 'length':4096}
                          ],
                          #chunk id is the index here
           'write_order'  : [0],
           # The bitmaps apply to ordered chunkseq
           'open_bitmap'  : [True],
           'fsync_bitmap' : [False],
           'close_bitmap' : [True],
           'sync_bitmap'  : [True],
           'writer_cpu_map': [0] # set affinity to which cpu
           }
    #pprint.pprint(build_file_chunkseq( file_treatment ))

    treatment = {
                  'filesystem': 'ext4',
                  'disksize'  : 64*1024*1024*1024,
                  'free_space_layout_score': 1,
                  'free_space_ratio': 0.7,
                  'dir_depth'     : 3,
                  # file id in file_treatment is the index here
                  'files': [file_treatment, 
                            copy.deepcopy(file_treatment)],
                  #'files': [file_treatment],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  'filechunk_order': [0, 1]
                  #'filechunk_order': [0,0,0,0]
                }
    workload_builder.correctize_fileid(treatment)

    ndirs = 2**(3+1)-1
    parentdirs = itertools.product(range(ndirs), repeat=2)
    for dirs in parentdirs:
        for filetreatment, dir in zip(treatment['files'], dirs):
            filetreatment['parent_dirid'] = dir
        #pprint.pprint( treatment )
        yield treatment
#dir_distance_iter()


def one_file_treatment(filesize, 
                       close_bitmap, 
                       fsync_bitmap,
                       write_order):
    """
    Each yield is a treatment
    """
    nchunks = 3
    file_treatment = {
           'parent_dirid' : 0,
           'fileid'       : 0,
           'writer_pid'   : 0,
           'chunks'       : [],
                          #chunk id is the index here
           'write_order'  : write_order,
           # The bitmaps apply to ordered chunkseq
           'open_bitmap'  : [True]+close_bitmap[0:nchunks-1],
           'fsync_bitmap' : fsync_bitmap,
           'close_bitmap' : close_bitmap,
           'sync_bitmap'  : close_bitmap,
           'writer_cpu_map': [-1]*nchunks # set affinity to which cpu
           }
    #pprint.pprint(build_file_chunkseq( file_treatment ))

    chunksize = filesize/3
    for i in range(nchunks):
        d = {
             'offset': chunksize*i,
             'length': chunksize
            }
        file_treatment['chunks'].append(d)
    file_treatment['filesize'] = filesize

    treatment = {
                  'filesystem': 'ext4',
                  'disksize'  : 64*1024*1024*1024,
                  'free_space_layout_score': 1,
                  'free_space_ratio': 0.7,
                  'dir_depth'     : 0,
                  # file id in file_treatment is the index here
                  'files': [file_treatment],
                  #'files': [file_treatment],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  'filechunk_order': [0]*nchunks
                  #'filechunk_order': [0,0,0,0]
                }
    workload_builder.correctize_fileid(treatment)
    #pprint.pprint( treatment )
    return treatment

def onefile_iter():
    nchunks = 3
    binspace = itertools.product( [False, True], repeat=nchunks)
    binspace = [list(x) for x in binspace] 
    
    filesize_sp = [12*1024*i for i in range(1,16)]
    close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    close_sp = [ list(x)+[True] for x in close_sp ] # always close
    fsync_sp = binspace
    write_order = list(itertools.permutations( range(nchunks) ))

    #filesize_sp = [12*1024]
    #close_sp = [ [False, False, True] ] # always close
    #fsync_sp = [ [True, False, False] ]
    #write_order = [ [0, 1, 2] ]  

    cnt = 0
    for fs, clos, fsync, ord in itertools.product(
            filesize_sp, close_sp, fsync_sp, write_order):
        trt = one_file_treatment(filesize=fs, 
                           close_bitmap=clos, 
                           fsync_bitmap=fsync,
                           write_order=ord)
        #if cnt % 1000 == 0:
            #trt['makeloopdevice'] = 'yes'
        #else:
            #trt['makeloopdevice'] = 'no'
        
        cnt += 1

        yield trt


##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
def one_file_treatment2(filesize, 
                       close_bitmap, 
                       fsync_bitmap,
                       write_order,
                       nchunks
                       ):
    """
    Each yield is a treatment
    """
    file_treatment = {
           'parent_dirid' : 0,
           'fileid'       : 0,
           'writer_pid'   : 0,
           'chunks'       : [],
                          #chunk id is the index here
           'write_order'  : write_order,
           # The bitmaps apply to ordered chunkseq
           'open_bitmap'  : [True]+close_bitmap[0:nchunks-1],
           'fsync_bitmap' : fsync_bitmap,
           'close_bitmap' : close_bitmap,
           'sync_bitmap'  : close_bitmap,
           'writer_cpu_map': [-1]*nchunks # set affinity to which cpu
           }
    #pprint.pprint(build_file_chunkseq( file_treatment ))

    chunksize = filesize/nchunks
    for i in range(nchunks):
        d = {
             'offset': chunksize*i,
             'length': chunksize
            }
        file_treatment['chunks'].append(d)
    file_treatment['filesize'] = filesize

    treatment = {
                  'filesystem': 'ext4',
                  'disksize'  : 64*1024*1024*1024,
                  'free_space_layout_score': 1,
                  'free_space_ratio': 0.7,
                  'dir_depth'     : 0,
                  # file id in file_treatment is the index here
                  'files': [file_treatment],
                  #'files': [file_treatment],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  'filechunk_order': [0]*nchunks
                  #'filechunk_order': [0,0,0,0]
                }
    workload_builder.correctize_fileid(treatment)
    #pprint.pprint( treatment )
    return treatment

def onefile_iter2():
    #nchunks_set = [1,2,3,4,5] 
    print '------------0000-------------'
    nchunks_set = [3,4] 
    cnt = 0
    for nchunks in nchunks_set:
        binspace = itertools.product( [False, True], repeat=nchunks)
        binspace = [list(x) for x in binspace] 
        
        #filesize_sp = [12*1024*i for i in range(1,3)]
        if nchunks in [1,2,3]:
            filesize_sp = range(1, 64, 1) + \
                          range(64, 256, 8) + \
                          range(256, 1024, 32) + \
                          range(1024, 64*1024, 256)
        else:
            filesize_sp = range(1, 64, 1) + \
                          range(64, 256, 16) + \
                          range(256, 1024, 32) + \
                          range(1024, 64*1024, 1024)

        random.seed(1)
        randsamples = random.sample(xrange(64*1024), 50)

        for s in randsamples:
            if not s in filesize_sp:
                filesize_sp.append( s )
        print filesize_sp
        filesize_sp = [ x*1024 for x in filesize_sp ]

        close_sp = itertools.product( [False, True], repeat=nchunks-1 )
        close_sp = [ list(x)+[True] for x in close_sp ] # always close
        fsync_sp = binspace
        write_order = list(itertools.permutations( range(nchunks) ))

        #print 'nchunk', nchunks, '--------------'
        #print 'close_sp', close_sp
        #print 'fsync_sp', fsync_sp
        #print 'write_order', write_order
        #continue

        #filesize_sp = [12*1024]
        #close_sp = [ [False, False, True] ] # always close
        #fsync_sp = [ [True, False, False] ]
        #write_order = [ [0, 1, 2] ]  

        for fs, clos, fsync, ord in itertools.product(
                filesize_sp, close_sp, fsync_sp, write_order):
            trt = one_file_treatment2(filesize=fs, 
                               close_bitmap=clos, 
                               fsync_bitmap=fsync,
                               write_order=ord,
                               nchunks=nchunks)
            cnt += 1
            yield trt

#onefile_iter2()
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################
##########################################################

def pick_by_level(levelstr, factor_range):
    count = len(factor_range)
    assert count > 0
    i = int(eval(str(count)+'*'+levelstr))
    if i == count:
        i -= 1
    ret = factor_range[i]
    return ret

def row_to_treatment(design_row):
    """
    quantative:
        chunk.number    disk.size   disk_used f.dir   file.size   fullness  w.number 
    qualitative:
        fsync   sync    c.order
    """
    #print 'Entering row_to_treatment...'
    #print design_row
    nchunks = design_row['num.chunks']

    # Define space
    #disk_size_range  = [ x*(2**30) for x in [4, 8, 16, 32] ]
    #disk_used_range  = range(3) 
    #dir_id_range      = range(0,32)
    #file_size_range  = [ x*1024 for x in [48, 84, 144, 224] ]
    #fullness_range   = [1.5, 2, 3, 4]
    #num_vcores_range   = [1,2,3,4]

    #binspace = itertools.product( [False, True], repeat=nchunks)
    #binspace = [list(x) for x in binspace] 
    #close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    #close_sp = [ list(x)+[True] for x in close_sp ] # always close
    #fsync_sp = binspace
    #write_order_sp = list(itertools.permutations( range(nchunks) ))

    # Define space
    #disk_size_range  = [ x*(2**30) for x in [4, 8, 16, 32] ]
    #disk_used_range  = range(3) 
    #dir_id_range      = range(0,32)
    #file_size_range  = [ x*1024 for x in range(12, 180, 1) ]
    #fullness_range   = [x/10.0 for x in range(1, 30)]
    #num_vcores_range   = [1,2,3,4]

    #binspace = itertools.product( [False, True], repeat=nchunks)
    #binspace = [list(x) for x in binspace] 
    #close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    #close_sp = [ list(x)+[True] for x in close_sp ] # always close
    #fsync_sp = binspace
    #write_order_sp = list(itertools.permutations( range(nchunks) ))


    # This is the setting with bug fixed from Duy's reporting
    #disk_size_range  = [x*(2**30) for x in range(4, 20) ]
    #disk_used_range  = [0,1,2,3] 
    #dir_id_range      = range(0,32)
    #file_size_range  = [ x*1024 for x in range(12, 1024, 1) ]
    #fullness_range   = [x/10.0 for x in range(1, 40)]
    #num_vcores_range   = [1,2,3,4]

    #binspace = itertools.product( [False, True], repeat=nchunks)
    #binspace = [list(x) for x in binspace] 
    #close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    #close_sp = [ list(x)+[True] for x in close_sp ] # always close
    #fsync_sp = binspace
    #write_order_sp = list(itertools.permutations( range(nchunks) ))

    # a new design 
    disk_size_range  = [x*(2**30) for x in range(4, 20) ]
    disk_used_range  = [0,1,2,3] 
    dir_id_range      = range(0,16)
    file_size_range  = [ x*1024 for x in range(12, 524, 4) ]
    fullness_range   = [x/10.0 for x in range(1, 21)]
    num_vcores_range   = [1,2]

    binspace = itertools.product( [False, True], repeat=nchunks)
    binspace = [list(x) for x in binspace] 
    close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    close_sp = [ list(x)+[True] for x in close_sp ] # always close
    fsync_sp = binspace
    write_order_sp = list(itertools.permutations( range(nchunks) ))


    # temp
    #disk_size_range  = [x*(2**30) for x in range(4,5) ]
    #disk_used_range  = [2] 
    #dir_id_range      = range(0,32)
    #file_size_range  = [ x*1024 for x in range(12, 1024, 1) ]
    #fullness_range   = [x/10.0 for x in range(1, 40)]
    #num_vcores_range   = [1,2,3,4]

    #binspace = itertools.product( [False, True], repeat=nchunks)
    #binspace = [list(x) for x in binspace] 
    #close_sp = itertools.product( [False, True], repeat=nchunks-1 )
    #close_sp = [ list(x)+[True] for x in close_sp ] # always close
    #fsync_sp = binspace
    #write_order_sp = list(itertools.permutations( range(nchunks) ))

    # pick one
    dir_id    = pick_by_level( design_row['dir.id'], dir_id_range )
    disk_size = pick_by_level( design_row['disk.size'], disk_size_range )
    disk_used = pick_by_level( design_row['disk.used'], disk_used_range )
    file_size = pick_by_level( design_row['file.size'], file_size_range )
    fullness  = pick_by_level( design_row['fullness'], fullness_range )
    # this is the number of VIRTUAL cores for all the chunk
    # if there is only one vcore, then all chunks will be written by one
    # core, like writer_cpu_map: [0,0,0,0]
    # if there are two vcores, then they will be written by two cores,
    # like [0,1,0,1], 
    # if there are 3 vcores, then like [0,1,2,0,1,2]
    # but the virtual cores will later be mapped to real cores.
    n_virtual_cores = pick_by_level( design_row['num.cores'], num_vcores_range )
    writer_cpu_map  = list(itertools.repeat( range(n_virtual_cores), 
                                       1+(nchunks/n_virtual_cores) ))
    writer_cpu_map = [ y for x in writer_cpu_map for y in x ]
    writer_cpu_map = writer_cpu_map[0:nchunks]
    #print writer_cpu_map
    nrealcores = 2
    writer_cpu_map = [ x % nrealcores for x in writer_cpu_map ]
    #print f_dir, disk_size, disk_used, file_size
    #print writer_cpu_map
    #return

    fsync_bitmap = pick_by_level( design_row['fsync'], fsync_sp )
    close_bitmap = pick_by_level( design_row['sync'], close_sp )
    sync_bitmap  = close_bitmap
    write_order  = pick_by_level( design_row['chunk.order'], write_order_sp )
    #print fsync_bitmap
    #print close_bitmap
    #print sync_bitmap
    #print write_order

    ###############################################
    ###############################################
    ###############################################
    file_treatment = {
           'parent_dirid' : dir_id, 
           'fileid'       : 0,
           'writer_pid'   : 0,
           'chunks'       : [],
                          #chunk id is the index here
           'write_order'  : write_order,
           # The bitmaps apply to ordered chunkseq
           'open_bitmap'  : [True]+close_bitmap[0:nchunks-1],
           'fsync_bitmap' : fsync_bitmap,
           'close_bitmap' : close_bitmap,
           'sync_bitmap'  : sync_bitmap,
           'writer_cpu_map': writer_cpu_map, # set affinity to which cpu
           'n_virtual_cores': n_virtual_cores,
           'fullness'       : fullness,
           'filesize'       : file_size
           }

    chunksize = file_size/nchunks

    filetreatment_list = []
    fullnessLeft = fullness
    #fullnessLeft = 2.5
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
    for i,filetreat in enumerate(filetreatment_list):
        filechunk_order += [i] * len(filetreat['chunks'])

    treatment = {
                  'filesystem': 'ext4',
                  'disksize'  : disk_size,
                  'disk_used'    : disk_used,
                  'dir_depth'     : 32,
                  # file id in file_treatment is the index here
                  'files': filetreatment_list,
                  #'files': [file_treatment],
                  # the number of item in the following list
                  # is the number of total chunks of all files
                  'filechunk_order': filechunk_order
                  #'filechunk_order': [0,0,0,0]
                }
    # shold not correct now, because I will write the 
    # same file many times
    #workload_builder.correctize_fileid(treatment)
    #pprint.pprint( treatment )
    return treatment

def fourbyfour_iter(design_path):
    #design_table = read_design_file(design_path)
    design_table = read_design_file_blhd(design_path)
    cnt = 0
    #design_table = [ design_table[i] 
             #for i in sorted(range(len(design_table)), reverse=True)]
    for fs in ['ext4', 'xfs', 'btrfs']:
        for design_row in design_table:
            #pprint.pprint( row_to_treatment(design_row) )
            #row_to_treatment(design_row) 
            #if design_row['chunk.number'] != 4:
                #continue
            treatment = row_to_treatment(design_row)
            treatment['filesystem'] = fs
            #pprint.pprint( treatment )
            yield treatment
            cnt += 1
            #break
            #if cnt <= 168:
                #continue
    
if __name__ == '__main__':
    #read_design_file_blhd('../design_blhd-4by4.txt')
    fourbyfour_iter('../design_blhd-4by4.txt')
    exit(0)

