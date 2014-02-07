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
import math

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

def curve_cuts(curves, nhorizons):
    """
    This funtion will use the that has lower x=0 cut 
    to pick the horizons. Then it calls horizon_curve_cuts()
    to get the cuts.

    The return is a list of cuts.
    """
    cs = []
    for curve in curves:
        cs.append(curve['c'])
    minc = min(cs)
    step = minc/(nhorizons-1)
    horizons = range(0, minc, step)
    horizons.append(minc)
    print horizons

    return horizon_curve_cuts(horizons, curves)

def horizon_curve_cuts(horizons, curves):
    """
    horizons: a list of Y values, e.g. [0,1,2,3..]
    curves: a list of curves. Usually should be two.
            coefficient of y=ax^2+bx+c. It is in
            the format of [{'a':#, 'b':#, 'c':#}, {...}]

    return value: it is a list of list of x values, like:
            [
             [x1,x2],
             [x1,x2,x3],
             ...
            ]
    """
   
    ret_list = []
    for y in horizons:
        xlist = []
        for curve in curves:
            a = curve['a']
            b = curve['b']
            c = curve['c']
            if a == 0: 
                assert b != 0
                x = (y-c)/b 
                xlist.append(x)
            else:
                x = (-b+math.sqrt(b**2-4*a*(c-y)))
                xlist.append(x)
                x = (-b-math.sqrt(b**2-4*a*(c-y)))
                xlist.append(x)
        ret_list.append( xlist )
    return ret_list

def cuts_to_chunkseq(xlists):
    chkseq = pat_data_struct.get_empty_ChunkSeq()
    for xlist in xlists:
        chkbox = pat_data_struct.get_empty_ChunkBox2()
        start = int(min(xlist))
        end = int(max(xlist))
        length = end - start
        chkbox['chunk']['offset'] = start
        chkbox['chunk']['length'] = length
        chkseq['seq'].append( chkbox )

    return chkseq

#a = curve_cuts(horizons = [0,1,2,4], 
        #curves = [
                  #{'a':0, 'b':-1, 'c':4},
                  #{'a':0, 'b':-0.5, 'c':5}
                 #]
               #)
#pprint.pprint( cuts_to_chunkseq(a) )



def get_curves(nwrites, filesize, d):
    """
    You can use d to control if it is 
    1. no overlap, no hole
    2. overlap
    3. hole
    """
    ylow = filesize # ylow can be any value, but we
                    # want it to be larger so that
                    # we have less 0 after decimal point.
                    # higher precision. 
    s = filesize
    yseg = filesize / nwrites
    a = 0
    b = -(ylow+d)/float(s)
    curve1 = {'a':a, 'b':b, 'c':ylow-yseg}
    curve2 = {'a':a, 'b':b, 'c':ylow+d}
    curves = [curve1, curve2]
    
    #pprint.pprint(curves)
    #return curve_cuts( curves, nhorizons=nwrites )
    return curves

#get_curve_coefficiency(nwrites=3, filesize=12*1024, d=0)
#print '------------'
#get_curve_coefficiency(nwrites=3, filesize=12*1024, d=1000)
#print '------------'
#get_curve_coefficiency(nwrites=3, filesize=12*1024, d=-1000)

def cut_curve_workload(nwrites, filesize, mode):
    t = filesize/4
    dic = {'regular':0,
           'overlap':t,
           'sparse' :-t}
    d = dic[mode]
    curves = get_curves(nwrites=nwrites, filesize=filesize, d=d)
    cuts = curve_cuts(curves=curves, nhorizons=3)
    for chkseq in cuts_workload_iter(cuts):
        yield chkseq

def cuts_workload_iter(cuts):
    # assign logical space #################
    chunkseq = cuts_to_chunkseq(cuts) 

    wldic_iter = pattern_iter.single_file_workload_iterator(nchunks=3, 
                           slotnames=['(','C','F',')','S'], 
                           valid_regexp=r'^(\((C+F?)+\)S)+$')

    for workloaddic in wldic_iter:
        for cseq in pattern_iter.chunk_order_iterator(chunkseq):
            # order chunks (assign time) ###############
            cseq_cp = copy.deepcopy(cseq)

            # assign operation ############
            pattern_iter.assign_operations_to_chunkseq( cseq_cp, workloaddic )

            yield cseq_cp
            #break
        #break


#for sq in cut_curve_workload(3, 12*1024):
    #pprint.pprint(sq)

def single_workload(filesize,
                    fsync_bitmap,
                    open_bitmap,
                    write_order,
                    nchunks):
    """
    The return is a ChunkSeq. So it can used to 
    produce a workload file immediatly. 

    Note that this function does not validate
    the parameters. It just generates
    workload (ChunkSeq) according to the paramters 

    Input format
    fsync_bitmap: [True, False, ...]. one boolean for
                  each chunk
    open_bitmap: [True, False, ...]. one boolean for 
                 each chunk
    write_order: [2, 0, 1]. If we name each chunk by its
                 offset order.
    """
    # logical space (setup chunkseq)
    chunksize = filesize / nchunks 
   
    chunkseq = pat_data_struct.get_empty_ChunkSeq()
    for offset in range(0, filesize, chunksize):
        cbox = pat_data_struct.get_empty_ChunkBox2()
        cbox['chunk']['offset'] = offset
        cbox['chunk']['length'] = chunksize
        cbox['chunk']['fileid'] = 0
        chunkseq['seq'].append( cbox )

    chunkseq['seq'] = [ chunkseq['seq'][i] for i in write_order ]

    # operations
    slotnames = ['(', 'C', 'F', ')', 'S']
    opbitmap = pat_data_struct.get_empty_OpBitmap()
    opbitmap['nchunks'] = nchunks
    for i in range(nchunks):
        d = {}
        for name in slotnames:
            d[name] = False

        d['C'] = 'C'
        if fsync_bitmap[i] == True:
            d['F'] = True
        if open_bitmap[i] == True:
            d['('] = True
        
        opbitmap['slotnames'].extend( slotnames )
        opbitmap['values'].extend( [ d[x] for x in slotnames ] )

    # if you open a file, you need to close it first and close it
    # at the end
    if len(opbitmap['values']) > 2:
        opbitmap['values'][-1] = True
        opbitmap['values'][-2] = True
    for i in sorted(range(len(opbitmap['values'])), reverse=True):
        if opbitmap['slotnames'][i] == '(' and \
                opbitmap['values'][i] == True :
            if i-2 >= 0:
                opbitmap['values'][i-1] = True
                opbitmap['values'][i-2] = True
            
    pprint.pprint(opbitmap)

single_workload(filesize=12,
                    fsync_bitmap=[True]*3,
                    open_bitmap=[True]*3,
                    write_order=[0,1,2],
                    nchunks=3)






















