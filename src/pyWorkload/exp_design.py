import itertools
import copy
import sys
import os
import pprint
import workload_builder
#sys.path.append( os.path.abspath("..") )
#import pyWorkload


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
    nchunks_set = [3] 
    cnt = 0
    for nchunks in nchunks_set:
        binspace = itertools.product( [False, True], repeat=nchunks)
        binspace = [list(x) for x in binspace] 
        
        #filesize_sp = [12*1024*i for i in range(1,3)]
        filesize_sp = range(1, 64, 1) + \
                      range(64, 256, 8) + \
                      range(256, 1024, 32) + \
                      range(1024, 64*1024, 256)
        randsamples = random.sample(xrange(64*1024), 50)

        for s in randsamples:
            if not s in filesize_sp:
                filesize_sp.append( s )
        print filesize_sp
        filesize_sp = [ x*1024 for x in filesize_sp ]
        exit(1)

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

onefile_iter2()
