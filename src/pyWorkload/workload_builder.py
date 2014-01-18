# This module takes advantage of the functionality of 
# pat_data_struct and pattern_iter to create new types
# of workloads.
# We should keep pat_data_struct and pattern_iter more
# constant and put flexible things in this module.

import pat_data_struct
import pattern_iter
import copy
import pprint
import itertools

def create_workload_sample():
    nchunks = 3

    
    # assign logical space #################
    chunkseq = pat_data_struct.get_empty_ChunkSeq()
    for i in range(0, 3):
        cbox = pat_data_struct.get_empty_ChunkBox2()
        cbox['chunk']['offset'] = i
        chunkseq['seq'].append(cbox)

    wldic_iter = pattern_iter.single_file_workload_iterator(nchunks=3, 
                           slotnames=['(','C','F',')','S'], 
                           valid_regexp=r'^(\((C+F?)+\)S)+$')

    for workloaddic in wldic_iter:
        for cseq in pattern_iter.chunk_order_iterator(chunkseq):
            # order chunks (assign time) ###############
            cseq_cp = copy.deepcopy(cseq)

            # assign operation ############
            pattern_iter.assign_operations_to_chunkseq( cseq_cp, workloaddic )
            for cbox in cseq_cp['seq']:
                print cbox['chunk']['offset'],
            print
            pprint.pprint(pat_data_struct.ChunkSeq_to_strings(cseq_cp))
            break

def overwrite_workload_iter( filesize ):
    """
    The output of this function is ChunkSeq
    The workload is to write file size and overwrite first 4kb,
    or the other way around
    """
    chunkbox1 = pat_data_struct.get_empty_ChunkBox2()
    chunkbox1['chunk']['offset'] = 0
    chunkbox1['chunk']['length'] = filesize
    chunkbox1['chunk']['fileid'] = 0

    chunkbox2 = pat_data_struct.get_empty_ChunkBox2()
    chunkbox2['chunk']['offset'] = 0
    chunkbox2['chunk']['length'] = 4096
    chunkbox2['chunk']['fileid'] = 0 

    chkseq = pat_data_struct.get_empty_ChunkSeq()
    chkseq['seq'].extend( [chunkbox1, chunkbox2] )


    wldic_iter = pattern_iter.single_file_workload_iterator(nchunks=1, 
                           slotnames=['(','C','F',')','S'], 
                           valid_regexp=r'^(\((C+F?)+\)S)+$')
    wldics = list(wldic_iter)
    wldics = list(itertools.product(wldics, repeat=2))

    for t_chkseq in pattern_iter.chunk_order_iterator( chkseq ):
        # t_chkseq is ordered
        # now assign operations
        for wldic in wldics:
            for i,wld in enumerate(wldic):
                pattern_iter.assign_operations_to_chunkbox(
                                        chunkbox = t_chkseq['seq'][i],
                                        workloaddic = wld )
            for off in [0, filesize/2, filesize-4096]:
                chunkbox2['chunk']['offset'] = off
                pprint.pprint( t_chkseq )
                yield t_chkseq

       
#pprint.pprint( list(overwrite_workload_iter(12*1024)) )
#overwrite_workload_iter(12*1024)













