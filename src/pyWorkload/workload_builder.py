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


#create_workload_sample()

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

    chkseq1 = pat_data_struct.get_empty_ChunkSeq()
    chkseq1['seq'].append( chunkbox1 )

    chunkbox2 = pat_data_struct.get_empty_ChunkBox2()
    chunkbox2['chunk']['offset'] = 0
    chunkbox2['chunk']['length'] = 4096
    chunkbox2['chunk']['fileid'] = 0

    chkseq2 = pat_data_struct.get_empty_ChunkSeq()
    chkseq2['seq'].append( chunkbox2 )

    chkseq_list = [chkseq1, chkseq2]

    wldic_iter = pattern_iter.single_file_workload_iterator(nchunks=1, 
                           slotnames=['(','C','F',')','S'], 
                           valid_regexp=r'^(\((C+F?)+\)S)+$')
    wldics = list(wldic_iter)
    wldics = itertools.product(wldics, repeat=2)

    for wldic in wldics:
        for cseq, wld in zip(chkseq_list, wldic):
            pattern_iter.assign_operations_to_chunkseq(
                                cseq, wld)
        chkseq = pat_data_struct.get_empty_ChunkSeq()
        chkseq['seq'] = [ cbox for cs in chkseq_list for cbox in cs['seq'] ]
        #print pat_data_struct.ChunkSeq_to_strings(chkseq) 
        yield chkseq
        

overwrite_workload_iter(12*1024)


























