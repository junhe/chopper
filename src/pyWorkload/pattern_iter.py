import itertools
import producer
import re
import random
import pprint
import subprocess
import pat_data_struct
import copy

def assign_operations_to_chunkseq( chunkseq, opbitmap ):
    """
    chunkseq and opbitmap has the same number of chunks.
    WARNING: chunkseq's operations should be empty! otherwise
             they will be overwritten.
    """
    nchunks = len( chunkseq['seq'] )
    assert nchunks == opbitmap['nchunks']

    # clean all the operations 
    for chkbox in chunkseq['seq']:
        chkbox['opseq'] = []
    
    seq = chunkseq['seq']
    nslots_per_chunk = len(opbitmap['slotnames']) / nchunks
    cnt = 0
    for symbol, value in zip( opbitmap['slotnames'],
                            opbitmap['values'] ):
        chunkid = int(cnt / nslots_per_chunk)
        cbox = seq[chunkid]  
        op = {
                'opname': pat_data_struct.symbol2name(symbol),
                'optype': pat_data_struct.symbol2type(symbol),
                'opvalue': value
             }      
        cbox['opseq'].append( op )
        cnt += 1
    return chunkseq



