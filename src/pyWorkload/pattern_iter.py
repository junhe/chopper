import itertools
import producer


def pattern_iter(nfiles, filesize, chunksize):
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
    num_of_chunks = filesize / chunksize
    chunksize = filesize / num_of_chunks
    chunk_sizes = [chunksize] * num_of_chunks
    offsets = range(0, filesize, chunksize)
    chunks = zip(offsets, chunk_sizes)

    chunk_iter = itertools.permutations(chunks)
    for chks in chunk_iter:
        wrapper_iter = itertools.product([False, True], repeat=num_of_chunks*4)
        for wraps in wrapper_iter:
            if not producer.IsLegal(wraps):
                # skip bad ones
                continue
            #print chks
            #print wraps
            yield {'chunks':chks, 'wrappers':wraps}

#for x in pattern_iter(1, 6, 2):
    #print x
