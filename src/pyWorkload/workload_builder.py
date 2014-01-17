# This module takes advantage of the functionality of 
# pat_data_struct and pattern_iter to create new types
# of workloads.
# We should keep pat_data_struct and pattern_iter more
# constant and put flexible things in this module.

import pat_data_struct
import pattern_iter
import copy
import pprint

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


create_workload_sample()

