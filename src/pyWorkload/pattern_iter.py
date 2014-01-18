import itertools
import producer
import re
import random
import pprint
import subprocess
import pat_data_struct
import copy

#####################################
# Let me clarify how pattern iteration works
# -- how to generate a workload by regular expression
#
# ======= OPERATION: Prepare operations
# 1, get some 0 and 1 sequence for operations,
#   these 0 and 1 indicate whether or not we use
#   an operation in the position of the number.
#   It is like:
#       slotnames: CFSCSF
#       values   : 001010
# 2, put 'C' into the values(01..)
# 3, transform the values(01..) to symbols(CFS...),
#    keep the 'C's
# 4, Check if the workload symbols are legal. If not,
#    drop it.
#
# Now in the workload symbols, we have operations. But
# we don't know what we should do with the 'C' (chunk).
# The information of the chunks are not clear. We need
# to figure out the details of each chunk.
#
# ======== LOGICAL SPACE: Put chunks in logical space
# 1, initialize n chunks as ChunkBox. 
#    The initialization includes offset, length, fileid.
#    This step defines this poistion of the chunk
#    in the logical space.
# 
# ======== PID
# Assign each chunk a pid (which process will write it).
#
# ======== TIME: decide the order to write the chunks
# Put the ChunkBox's to ChunkSeq
#
# ===========================================================
# ===========================================================
# ===========================================================
#
# TIME, OPERATION and LOGICAL SPACE is related since the legal
# check of operation is only for one file. 
# One convenient way to do it is:
# a) LOGICAL SPACE -> TIME -> OPERATION:
#    1. assign offset, length, fileid, ..
#    2. put in ChunkSeq
#    3. figure out valid operations for each file, assign to files
# 
# Note that TIME order is useless if the chunks have not been assigned
# logical space. Without logical info, they are just placeholders.
# So it has to be LOGICAL SPACE -> TIME.
#
# OPERATION is independent of LOGICAL SPACE and TIME. As long as you
# know how many chunks there are and the possible operations, you can
# figure out the valid operations. 
#
#
# NOTE: The approach described above (Let's name it as REGSQUEEZE -
# using regular expression to squeeze a large pattern space) 
# is quite different to the other  one, which uses filesize, 
# holesize, stride, .. to define a pattern (let's call it PARA - PARAMETERIZED)
# 
# The REGSQUEEZE one start with a very large space (all permutations of
# 0 and 1) and use regular expression to SHRINK the space. 
# 
# The PARA one start with a small space. It adds more parameters, 
# enlarge the parameter range. You may need more and more parameters
# to decribe complex pattern. But in the REGSQ, it is more general 
# and flexible since you don't add parameters, you manipulate the 
# existing ones to get new pattern.
#

def assign_operations_to_chunkbox(chunkbox, workloaddic):
    chunkbox['opseq'] = []
    for symbol, value in zip( workloaddic['slotnames'],
                              workloaddic['values'] ):
        op = {
                'opname': pat_data_struct.symbol2name(symbol),
                'optype': pat_data_struct.symbol2type(symbol),
                'opvalue': value
             }      
        chunkbox['opseq'].append( op )

def assign_operations_to_chunkseq_by_fileid( chunkseq, 
                                             workloaddic, 
                                             fileid ):
    """
    assign workloaddic to chunkboxs in chunkseq of fileid
    """
    t_chkseq = pat_data_struct.get_empty_ChunkSeq()
    for cbox in chunkseq['seq']:
        if cbox['chunk']['fileid'] == fileid:
            t_chkseq['seq'].append( cbox )
    
    assign_operations_to_chunkseq( t_chkseq, workloaddic )

def assign_operations_to_chunkseq( chunkseq, workloaddic ):
    """
    chunkseq and workloaddic has the same number of chunks.
    WARNING: chunkseq's operations should be empty! otherwise
             they will be overwritten.
    """
    nchunks = len( chunkseq['seq'] )
    assert nchunks == workloaddic['nchunks']

    # clean all the operations 
    for chkbox in chunkseq['seq']:
        chkbox['opseq'] = []
    
    seq = chunkseq['seq']
    nslots_per_chunk = len(workloaddic['slotnames']) / nchunks
    cnt = 0
    for symbol, value in zip( workloaddic['slotnames'],
                            workloaddic['values'] ):
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

def chunk_order_iterator( chunkseq ):
    """
    The input chunkseq should not have operations assigned, otherwise
    reordering the chunks will break the legal operations
    """
    ret_chkseq = pat_data_struct.get_empty_ChunkSeq()
    seq_iter = itertools.permutations( chunkseq['seq'] )
    for seq in seq_iter:
        ret_chkseq['seq'] = seq
        yield ret_chkseq 

def single_file_workload_iterator(nchunks, slotnames, valid_regexp):
    """
    Input:
        slotnames is a list: ['(','C',')'..], repeat once

    The output of this functaion should be
     dic={
            'slotnames':[C,F,S,C,S,F..],
            'values'   :[True, False,..]
         }
    """
    nslots_per_chunk = len( slotnames )
    nslots = nchunks * nslots_per_chunk
    nops_per_chunk = nslots_per_chunk - 1 # one is data data
    nops = nchunks * nops_per_chunk
    chunkpos = slotnames.index('C') # 'C' always represent Chunk

    # Now iterate all possible operation combinations, 
    # including invalid ones
    allops = itertools.product([False, True], repeat=nops)
    allnames = slotnames * nchunks
    for op_seq in allops:
        # first, insert 'C' to operations
        op_seq = list( op_seq )
        #print op_seq
        values = [ op_seq[i:i+chunkpos]
              +['C']
              +op_seq[i+chunkpos:i+nops_per_chunk] \
                for i in range(0, nops, nops_per_chunk) ]
        values = [ y for x in values for y in x ]
        #print values

        used_str = pat_data_struct.ChunkBox_filter_used_ops(
                            { 'slotnames':allnames,
                              'values': values } )
        used_str = ''.join(used_str)
        if is_legal(used_str, valid_regexp):
            workloaddic = {
                  'nchunks'  : nchunks,
                  'slotnames': allnames,
                  'values'   : values }
            yield workloaddic

def is_legal( workload_str, valid_regexp ):
    mo = re.match(valid_regexp, workload_str, re.M)
    if mo:
        return True
    else:
        return False

#a = valid_workload_iterator(nchunks=3, 
                       #slotnames=['(','C','F',')','S'], 
                       #valid_regexp=r'^(\((C+F?)+\)S)+$')
#a = list(a)
#pprint.pprint( a )
#exit(1) 

def regldg(max_length, num_words_output, regstr):
    #./regldg --debug-code=1 --universe-set=7 --universe-checking=3 --max-length=8 --readable-output --num-words-output=100 "(a|b)[cd]{2}\1"
    cmd = [
            './regldg-1.0.0/regldg', 
            '--debug-code=1', 
            '--universe-set=33', 
            '--universe-checking=3',
            '--max-length='+str(max_length),
            '--readable-output',
            '--num-words-output='+str(num_words_output),
            regstr
            ]
    proc = subprocess.Popen(cmd, 
                    stdout = subprocess.PIPE)
    proc.wait()

    wordlist = []
    for line in proc.stdout:
        wordlist.append(line.strip())
    
    pprint.pprint( wordlist )
    return wordlist

