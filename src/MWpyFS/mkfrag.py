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
    
    # since the atom unit is block and we cannot
    # have a fraction of a block, so we rount it
    # this is dangerous though, if in fragsz, they
    # are all 0.x, you end up with all 0s. 
    # So, be carefuly when generating it.
    for i,x in enumerate(fragsz):
        fragsz[i] = int(x)

    plothist(fragsz)
    return fragsz
        
def _getSizeFromRange(zone_ranges):
    sizes = []
    for row in zone_ranges:
        sizes.append( row[1] - row[0] )

    return sizes



def getFreeZonesOfPartition(partition, mountpoint):
    "Note that the index of zone here may not match the group index"
    mo = Monitor.FSMonitor(dn=partition, 
                           mp=mountpoint)
    groups = mo.dumpfs()['freeblocks']

    #print groups.toStr()

    si = groups.header.index('start')
    ei = groups.header.index('end')
    free_zones = []
    for row in groups.table:
        free_zones.append( [int(row[si]), int(row[ei])] )

    return free_zones

def applyFrags(free_zone_ranges, frags_of_zones, partition, mountpoint):
    """
    free_zone_ranges: [[startblock, endblock], [],...]
    frags_of_zones: [[frag size of zone0], [], ...]
    """

    print "free_zone_ranges", free_zone_ranges
    print "frags_of_zones", frags_of_zones

    setter = Monitor.FSMonitor(dn=partition, mp=mountpoint)

    # do it zone by zone
    for zi,zone in enumerate(free_zone_ranges):
        print zone
        zstart = zone[0]
        zfirst_avail = zstart
        zend = zone[1]
        for fragsize in frags_of_zones[zi]:
            toset = zfirst_avail+fragsize 
            
            # try not to set wrong blocks, very dangerous
            if toset > zend:
                print "you dont want to set blocks beyond the end"
                exit(1)

            ret = setter.setBlock(zfirst_avail+fragsize, 1)
            print "setter return:", ret
            zfirst_avail = toset + 1
        if zfirst_avail <= zend:
            ret = setter.setBlock(zfirst_avail, zend-zfirst_avail+1)
            print "setter return:", ret


# test applyFrags
#applyFrags([[1, 100], [200, 3000]], [[1,2,3,4,5], [33,2,11,22,3,444,3]] )
#exit(0)

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

def makeFragments(partition, mountpoint):
    free_zones = getFreeZonesOfPartition(
                                partition=partition,
                                mountpoint=mountpoint)
    zone_sizes = _getSizeFromRange(free_zones)
    print "free_zones", free_zones
    print "free_zones sizes", zone_sizes

    fragment_list = generateFrags(2, 3, 100, 10000)
    print "fragment_list", fragment_list

    zone_frags = assignFragsToZones(zone_sizes, fragment_list)
    print "zone_frags:", zone_frags

    applyFrags(free_zones, zone_frags, partition, mountpoint)

    # check the free zones
    print "free zone after all:", getFreeZonesOfPartition(
                                partition=partition,
                                mountpoint=mountpoint)


makeFragments(partition='/dev/ram0', mountpoint='/mnt/scratch/')
#fragplan([100, 100], [3,44,2,4,3,3,2,3,9,2])

#frags(100, 8, 1000, 100)
#par = '/dev/ram0'
#mp = '/mnt/scratch'
#FormatFS.remakeExt4(partition=par,
                    #mountpoint=mp,
                    #username="junhe",
                    #groupname="junhe",
                    #blockscount=65536)
#print 'remade fs'
#probeAndAssign(partition=par, 
               #mountpoint=mp)

##a = stats.lognorm(scale=0.1)
##a = np.random.beta(0.75, 0.25, 10000)
#print a.rvs(2, size=10)
#help(stats.lognorm.rvs)
#help(a.rvs)
#plothist(a)
