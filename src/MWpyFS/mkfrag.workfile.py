import random
import math
import subprocess
import pprint
try:
    import matplotlib.pyplot as plt
except ImportError:
    print "This machine does not have matplotlib, skipped importing."


import Monitor
import FormatFS

def plothist(x):
    try:
        plt.hist(x, 1000, facecolor='g', alpha=0.75)
        plt.show()
    except:
        print "Trivial operation skipped"

def generate_lognormal_sizes_uniquebytes( mu, sigma, 
                                        hard_maxbytes):

    MAXI = 30
    # probability list of extent size 2^x *4096
    # pr_list[0]= Pr(0<x<1), 
    # pr_list[1]= Pr(1<x<2), 
    # ...
    pr_list = []
    for a in range(30):
        b = a+1
        pr_ab = lognorm_probability_range(a, b, mu, sigma)
        pr_list.append(pr_ab)
    
    overhead_pr = 0
    for i, pr in enumerate(pr_list):
        overhead_pr += pr / float(2**i)

    ret_sizes = []
    available_bytes = hard_maxbytes*1/float(1+overhead_pr)
    
    for i, pr in enumerate(pr_list):
        # count of extent of size 2^i blocks
        ext_size = 4096*2**i
        ext_cnt = available_bytes * pr / ext_size
        ret_sizes.extend( [ext_size] * ext_cnt )
    
    return ret_sizes

def generate_lognormal_sizes( mu, sigma, 
                             hard_maxbytes, seed=1 ):
    """
    size = 2^x, x follows lognorm distriution
    sum(size) will eventually close to sum_target.
    """
    random.seed(seed)
    # described in the unit of block(4096)
    szlist = []
    xlist = []
    szsum = 4096 # overhead 

    while True:
        x = random.lognormvariate(mu, sigma)
        sz = 4096 * int(2**x)
        # 4096 is the overhead of makeing a hole
        szsum += sz + 4096 
        
        if szsum > hard_maxbytes:
            break

        xlist.append( x )
        szlist.append( sz )
    
    print xlist
    return szlist

def make_holes ( szlist ):
    off = 0
    holelist = []
    for sz in szlist:
        off += 4096
        hole = (off, sz)
        holelist.append( hole )
        off += sz
    holelist.append((-1,-1))

    totalsize = off + 4096
    holelist.insert(0, (0, totalsize)) # seal the end

    return holelist

def save_holelist_to_file(holelist, filepath):
    with open(filepath, 'w') as f:
        for extent in holelist:
            extent = [ str(x) for x in extent ]
            line = ' '.join(extent)
            f.write(line + '\n')
    print 'file saved'

def make_hole_file( holelistfile, targetfile ):
    cmd = ['../puncher', targetfile, holelistfile]
    return subprocess.call(cmd)

def lognorm_cdf(x, mu, sigma):
    "check wikipedia"
    return math.erfc(-(math.log(x)-mu)/(sigma*math.sqrt(2)))/2

def lognorm_probability_range(a, b, mu, sigma):
    "it returns P(a<x<b) by cdf"
    cumu_a = lognorm_cdf(a, mu, sigma)
    cumu_b = lognorm_cdf(b, mu, sigma)
    return abs(cumu_b-cumu_a)

def create_frag_file( layout_estimate, 
                    hard_maxbytes, targetfile):
    dict = {
            #   mu           sigma 
            1: (0.0000000,   1.0),
            2: ( 0.9382696,   0.9),
            3: ( 1.4136933,   0.8),
            4: ( 1.7346011,   0.7),
            5: ( 1.9771627,   0.6),
            6: ( 2.1722233,   0.5),
            7: ( 2.3353749,   0.4),
            8: ( 2.4756043,   0.3),
            9: ( 2.5985660,   0.2),
            10: ( 2.7080502,   0.1)
            }
    mu,sigma = dict[layout_estimate*10]
    #szlist = generate_lognormal_sizes(
                    #mu, sigma, hard_maxbytes, 1 )
    szlist = generate_lognormal_sizes_uniquebytes\
                        (mu, sigma, hard_maxbytes)
    print(szlist)
    holelist = make_holes(szlist) 
    save_holelist_to_file( holelist, 
                            '/tmp/_holelist' )
    ret = make_hole_file( '/tmp/_holelist', targetfile )
    return ret

if __name__ == '__main__':
    create_frag_file( 0.1, 4*1024*1024, 
                        '/mnt/scratch/bigfile')

def generateFragsV2(mu, sigma, sum_target, maxfragexp=15, tolerance=0.5, seed=1):
    """
    TODO: need to try permutation when it is not able to reach sum_target
    Return: fragment sizes in number of blocks
    maxfragexp: 2**maxfragexp is the larget size of fragment in number of blocks
        128MB is 32768 blocks, which is 2^15 blocks
    sum_target: it should be in bytes.
    """
    random.seed(seed)
    blocks_of_frags = []
    betas = []
    print "alpha:", alpha, "beta", beta

    while True:
        k = random.betavariate(alpha, beta)
        betas.append(k)
        sz = int(2**(maxfragexp*k)) 
        blocks_of_frags.append(sz)
        szsum = sum(blocks_of_frags) 
        if szsum >= sum_target * (1 - tolerance) and\
           szsum <= sum_target * (1 + tolerance):
               print "NICE :):):) reach within tolerance"
               print "sum:", szsum
               print "target:", sum_target
               print "count:", len(blocks_of_frags)
               print "max:", max(blocks_of_frags)
               plothist(betas)
               plothist(blocks_of_frags)
               return blocks_of_frags
        elif szsum > sum_target * ( 1 + tolerance ):
            print "Damn....  failed to reach within tolerance!!!!! :( "
            exit(1)


def generateFrags(alpha, beta, count, sum_lim, seed=1):
    "Using R to find proper parameters (because I am better with R..)"
    #l = np.random.beta(alpha, beta, count)
    random.seed(seed)
    l = []
    for i in range(count):
        l.append( random.betavariate(alpha, beta) )

    plothist(l)
    expl = []
    for x in l:
        expl.append( 2**(17*x) )
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

    print sorted(fragsz)
    plothist(fragsz)
    return fragsz

##############
#  for test
#
#def test_main():
    #sum_target = 3*1024*1024*1024/4096 # sum of fragments is 3G
    #seed = 1
    #para = [
            #[10,2],
            #[5,2],
            #[2,5],
            #[5,5],
            #[1,1],
            #[2,10]
            #]
    
    #for a, b in para:
        #generateFragsV2(a, b, sum_target, tolerance=0.1, seed=1)

#test_main()


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

    setter = Monitor.FSMonitor(dn=partition, mp=mountpoint)

    # do it zone by zone
    for zi,zone in enumerate(free_zone_ranges):
        print zi, zone
        zstart = zone[0]
        zfirst_avail = zstart
        zend = zone[1]
        for fragsize in frags_of_zones[zi]:
            toset = zfirst_avail+fragsize 
            if toset > zend:
                print "what you want to set is beyond this zone"
                exit(1)
            
            # try not to set wrong blocks, very dangerous
            if toset > zend:
                print "you dont want to set blocks beyond the end"
                exit(1)

            ret = setter.setBlock(toset, 1)
            #print toset, 1
            #print "testing if blocks are in use...."
            if not setter.isAllBlocksInUse(toset, 1):
                print "you failed to set some blocks as in used"
                exit(1)
            #print "setter return:", ret
            zfirst_avail = toset + 1
        if zfirst_avail <= zend:
            cnt = zend - zfirst_avail + 1
            ret = setter.setBlock(zfirst_avail, cnt)
            #print zfirst_avail, cnt
            #print "testing if blocks are in use...."
            if not setter.isAllBlocksInUse(zfirst_avail, cnt):
                print "you failed to set some blocks as in used"
                exit(1)
            #print "setter return:", ret


# test applyFrags
#applyFrags([[1, 100], [200, 3000]], [[1,2,3,4,5], [33,2,11,22,3,444,3]] )
#exit(0)

def assignFragsToZones(free_zone_sizes, frag_sizes, seed=1):
    """
    input: 1. A list of sizes, each representing an existing free zone.
             A zone is very likely to be a free space of a group
           2. A list of sizes, each representing size of a fragment
    output: multiple sets of sizes, each of which is for one group
            the return is the assignment
    
    note that right now the returned values are sorted. you can shuffle
    them later.
    This zone is different from the zone concept in Minix.
    """
    random.seed(seed)
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
    # with largest free zone
    frag_sizes = sorted(frag_sizes, reverse=True)
    for frg in frag_sizes:
        zone = sorted(free_zone_spaces, reverse=True)[0]
        g_idx = free_zone_spaces.index(zone)

        if frg <= zone:
            # put frg in group[g_idx]
            zone_frags[g_idx].append(frg)
            free_zone_spaces[g_idx] -= (frg+1) # +1 for the 
                                               #barrier after this frag
        else:
            print "not good, this should not happend"
            exit(1)
    # sometimes, some zone is never touched, in which case
    # it will not be divided to smaller fragments. 
    # Let us assign a 0-length fragment to it, so later the
    # whole zone will be marked as allocated and no fragments in
    # it (as we expected)
    for i, frags_of_a_zone in enumerate(zone_frags):
        if len(frags_of_a_zone) == 0:
            # it has not been touched
            zone_frags[i].append(0)
        # it is just convenient to do it here
        random.shuffle(zone_frags[i]) 

    #print "frags of each group:"
    #printwithindex(zone_frags)
    #print "free zone of each group:"
    #printwithindex(free_zone_spaces)
    return zone_frags

def makeFragmentsOnFS(partition, mountpoint, 
                      alpha, beta, sumlimit, seed=1, tolerance=0.1):
    # zones are described by the unit of block
    free_zones = getFreeZonesOfPartition(
                                partition=partition,
                                mountpoint=mountpoint) 
    # unit: block
    zone_sizes = _getSizeFromRange(free_zones)
    #print "free_zones"
    #printwithindex(free_zones)
    #print "free_zones sizes"
    #printwithindex(zone_sizes)

    fragment_list = generateFragsV2(alpha=alpha, beta=beta, sum_target=sumlimit, 
            maxfragexp=15, tolerance=tolerance, seed=seed)

    #print "fragment_list"
    #printwithindex(fragment_list)

    zone_frags = assignFragsToZones(zone_sizes, fragment_list, seed)
    #print "zone_frags:"
    #printwithindex(zone_frags)

    applyFrags(free_zones, zone_frags, partition, mountpoint)

    # check the free zones
    free_zones = getFreeZonesOfPartition(
                                partition=partition,
                                mountpoint=mountpoint)
    zone_sizes = _getSizeFromRange(free_zones)
    
    #for i, zone in enumerate(free_zones):
    #    print i, zone, zone_sizes[i]

def printwithindex( l ):
    for i, x in enumerate(l):
        print i, x



#FormatFS.makeLoopDevice('/dev/loop0', '/mnt/mytmpfs', 512)
#FormatFS.remakeExt4('/dev/loop0', '/mnt/scratch/', 'junhe', 'junhe',
                    #512*1024)
#makeFragmentsOnFS(partition='/dev/loop0', mountpoint='/mnt/scratch/')


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
