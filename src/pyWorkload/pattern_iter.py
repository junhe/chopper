import itertools
import re
import producer
import re
import random
import pprint

N_OPERATIONS = 4 # OPEN FSYNC CLOSE SYNC

def Filter( opstr, keep ):
    # input is like (FSYNC, True)
    if keep:
        return opstr 
    else:
        return ""

def wrappers_to_symbols( wrappers ):
    num_of_chunks = len(wrappers) / N_OPERATIONS
    #strs = ['OPEN', 'FSYNC', 'CLOSE', 'SYNC'] * num_of_chunks
    symbols = ['(', 'C', 'F', ')', 'S'] * num_of_chunks

    #TODO: this can go bad when the number of operations changes
    choices = [ (wrappers[i], True, wrappers[i+1], wrappers[i+2], wrappers[i+3]) \
                    for i in range(0, num_of_chunks*N_OPERATIONS, N_OPERATIONS) ]
    choices = list(itertools.chain.from_iterable(choices))
    seq = map(Filter, symbols, choices)
    seq = ''.join(seq)

    return seq


def IsLegal( wrappers ):
    "conver to string and use regex"
    seq = wrappers_to_symbols( wrappers )
   
    # use regex to check seq
    #
    # GOOD ONE backup: mo = re.match(r'^(\((C+F?)+\)S?)+$', seq, re.M)
    #mo = re.match(r'^(\((C+F)+\))S$', seq, re.M) # always Fsync, only one open-close, must sync
    mo = re.match(r'^(\((C+F?)+\)S)+$', seq, re.M)
    if mo:
        print "good match!", seq
        return True
    else:
        #print 'BAD match!', seq
        return False

def pattern_iter_nfiles(nfiles, filesize, chunksize):
    """
    Input: 
        nfiles: number of files
        filesize: file size
        chunksize: chunk size
    
    Output:
        a iteratorable object like itertool.permutation
    
    Usage:
        for x in pattern_iter(xxx,xxx,xx):
            use x
        OR
        l = list(pattern_iter(xxx,xxx,xxx))
        for x in l:
            use x
        
    Single file case is not hard, multiple is hard.
    """
    nchunks_per_file = filesize/chunksize

    # split to chunks
    file_chunks = [] # it is a list of chunks from different files
    for i in range(nfiles):
        file_chunks.append( 
                split_a_file_to_chunks(filesize  =filesize, 
                                       chunksize =chunksize,
                                       fileid    =i) )

    # sort the chunks
    # SKIPPED at this time
   
    # Separate chunks of different files out

    # Assign only legal operations to chunks for each file
    chk_with_ops = [] # [{'chunks':[], 'operations':[]},{},{},...]

    possible_ops = list(operations_iter( nchunks_per_file )) #{chunks, operations}
    # you now have all k possible operation sequences for a file
    # you need to pick n (could be repeated) from k and assign to
    # the n files
    ## pick n
    ops_for_files = random.sample( possible_ops, nfiles )
    chk_with_ops = zip (file_chunks, ops_for_files)
    chk_with_ops = [ dict( zip( ['chunks', 'operations'], FileEntry) ) \
                                        for FileEntry in chk_with_ops ]
    pprint.pprint( chk_with_ops )

def operations_iter(num_of_chunks):
    """
    It will return an iterable object the iterates all/selected
    operations to the num_of_chunks chunks
    """
    wrapper_iter = itertools.product([False, True], 
                        repeat=num_of_chunks*N_OPERATIONS)
    for wraps in wrapper_iter:
        if not IsLegal(wraps):
            # skip bad ones
            continue
        yield wraps # (True, False, False, ..)

def split_a_file_to_chunks(filesize, chunksize, fileid=0):
    """
    At this time, let me just split the file to 
    equal sizes. Later we can do random splits
    """
    num_of_chunks = filesize / chunksize
    chunk_sizes = [chunksize] * num_of_chunks
    file_ids = [fileid] * num_of_chunks
    offsets = range(0, filesize, chunksize)
    chunks = zip(file_ids, offsets, chunk_sizes)

    # convert to dictionary
    ret = [ dict( zip( ['fileid', 'offset', 'length'], c ) ) \
                                                    for c in chunks ]
    return ret

def pattern_iter(nfiles, filesize, chunksize):
    num_of_chunks = filesize / chunksize
    chunksize = filesize / num_of_chunks
    chunk_sizes = [chunksize] * num_of_chunks
    offsets = range(0, filesize, chunksize)
    chunks = zip(offsets, chunk_sizes)

    chunk_iter = itertools.permutations(chunks)
    for chks in chunk_iter:
        wrapper_iter = itertools.product([False, True], repeat=num_of_chunks*N_OPERATIONS)
        for wraps in wrapper_iter:
            if not IsLegal(wraps):
                # skip bad ones
                continue
            #print chks
            #print wraps
            yield {'chunks':chks, 'wrappers':wraps}

def GenWorkloadFromChunks( chunks,
                           wrappers,
                           rootdir,
                           tofile
                           ):
        
    num_of_chunks = len(chunks)

    # organize it as dictionary
    chunks = [ dict( zip( ['offset', 'length'], c ) ) \
                                                    for c in chunks ]
    # group wrapers to 3 element groups
    wrappers = [wrappers[i:i+N_OPERATIONS] for i in range(0, num_of_chunks*N_OPERATIONS, N_OPERATIONS) ]
    wrappers = [ dict( zip(['OPEN', 'FSYNC', 'CLOSE', 'SYNC'], w) ) \
                                                    for w in wrappers]

    prd = producer.Producer(
            rootdir = rootdir,
            tofile = tofile)
    prd.addDirOp('mkdir', pid=0, dirid=0)

    # ( (off,size), {wrapper} )
    entries = zip(chunks, wrappers)
    for entry in entries:
        #print entry
        if entry[1]['OPEN']:
            prd.addUniOp('open', pid=0, dirid=0, fileid=0)
        
        # the chunk write
        prd.addReadOrWrite('write', pid=0, dirid=0,
               fileid=0, off=entry[0]['offset'], len=entry[0]['length'])

        if entry[1]['FSYNC']: 
            prd.addUniOp('fsync', pid=0, dirid=0, fileid=0)

        if entry[1]['CLOSE']: 
            prd.addUniOp('close', pid=0, dirid=0, fileid=0)

        if entry[1]['SYNC']:
            prd.addOSOp('sync', pid=0)

    prd.display()
    prd.saveWorkloadToFile()
    return True

pattern_iter_nfiles(2, 900, 300)

#for x in pattern_iter(1, 6, 2):
    #print x
