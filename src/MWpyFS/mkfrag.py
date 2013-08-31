import scipy as sp
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import Monitor
import FormatFS


def plothist(x):
    plt.hist(x, 1000, facecolor='g', alpha=0.75)
    plt.show()


def generateFrags(alpha, beta, count, sum_lim):
    "Using R to find proper parameters (because I am better with R..)"
    l = np.random.beta(alpha, beta, count)
    expl = []
    for x in l:
        expl.append( 2**(10*x) )
    sm = 0
    for x in expl:
        sm += x
    fragsz = []
    for x in expl:
        fragsz.append( sum_lim*x/sm )
    plothist(fragsz)
        
def probeAndAssign(partition, mountpoint):
    mo = Monitor.FSMonitor(dn=partition, 
                           mp=mountpoint)
    groups = mo.dumpfs()['freeblocks']

    print groups.toStr()

    # extract start and end from groups
    si = groups.header.index('start')
    ei = groups.header.index('end')
    free_ranges = []
    for row in groups.table:
        free_ranges.append( [int(row[si]), int(row[ei])] )

    free_sizes = []
    for row in free_ranges:
        free_sizes.append( row[1] - row[0] )

    print 'free_ranges', free_ranges
    print 'free_sizes', free_sizes

def applyFrags(free_zone_ranges, frags_of_zones ):
    """
    free_zone_ranges: [[startblock, endblock], [],...]
    frags_of_zones: [[frag size of zone0], [], ...]
    """
    # do it zone by zone
    for zi,zone in free_zone_ranges:
        zstart = zone[0]
        zfirst_avail = zstart
        zend = zone[1]
        for fragsize in frags_of_zones[zi]:
            setBlock(zfirst_avail+fragsize, 1)




def assignFragsToZones(free_zone_sizes, frag_sizes):
    """
    input: a list of sizes, each representing an existing free zone.
           A zone is very likely to be a free space of a group
           a list of sizes, each representing size of a fragment
    output: multiple sets of sizes, each of which is for one group
            the return is the assignment
    
    note that right now the returned values are sorted. you can shuffle
    them later.
    This zone is different from the zone concept in Minix.
    """
    nzones = len(free_zone_sizes)
    nfrags = len(frag_sizes)
    # a table, row i has frag sizes for zone i
    zone_frags = [[] for i in range(nzones)  ] 
    # a list, i has free space left for zone i
    free_zone_spaces = list(free_zone_sizes) # shallow copy
    
    sum_zone_sizes = 0
    for x in free_zone_sizes:
        sum_zone_sizes += x

    sum_frag_impl_sizes = 0
    for x in frag_sizes:
        sum_frag_impl_sizes += x
    # to separate one segment to two fragments, you need
    # at least one block in the middle of the two fragments
    # To separate one segment to n fragments, you need
    # at least n-1 barriers. However, by having k zones,
    # you already have k-1 barriers. You all you need is
    # (n-1) - (k-1) barriers.
    sum_frag_impl_sizes += (nfrags - 1) - (nzones - 1)

    if sum_frag_impl_sizes > sum_zone_sizes:
        print "fragment size exceeds free zone sizes",
        exit(1)

    # the allocation algorithm is greedy.
    # pick the largest fragment and put it in the group
    # with largest free space
    frag_sizes = sorted(frag_sizes, reverse=True)
    for frg in frag_sizes:
        space = sorted(free_zone_spaces, reverse=True)[0]
        g_idx = free_zone_spaces.index(space)

        if frg <= space:
            # put frg in group[g_idx]
            zone_frags[g_idx].append(frg)
            free_zone_spaces[g_idx] -= (frg+1) # +1 for the 
                                               #barrier after this frag
        else:
            print "not good, this should not happend"
            exit(1)

    print "frags of each group:", zone_frags
    print "free space of each group:", free_zone_spaces
    return zone_frags

#fragplan([100, 100], [3,44,2,4,3,3,2,3,9,2])

#frags(100, 8, 1000, 100)
par = '/dev/ram0'
mp = '/mnt/scratch'
FormatFS.remakeExt4(partition=par,
                    mountpoint=mp,
                    username="junhe",
                    groupname="junhe",
                    blockscount=65536)
print 'remade fs'
probeAndAssign(partition=par, 
               mountpoint=mp)

#a = stats.lognorm(scale=0.1)
#a = np.random.beta(0.75, 0.25, 10000)
#print a.rvs(2, size=10)
#help(stats.lognorm.rvs)
#help(a.rvs)
#plothist(a)
