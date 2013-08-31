import scipy as sp
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt



def plothist(x):
    plt.hist(x, 1000, facecolor='g', alpha=0.75)
    plt.show()


def frags(alpha, beta, count, sum_lim):
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
        
def fragplan(group_sizes, frag_sizes):
    """
    input: a list of sizes, each representing a group
           a list of sizes, each representing size of a fragment
    output: multiple sets of sizes, each of which is for one group
    """
    ngrps = len(group_sizes)
    nfrags = len(frag_sizes)
    # a table, row i has frag sizes for group i
    grp_frags = [[] for i in range(ngrps)  ] 
    # a list, i has free space left for group i
    free_grp_spaces = list(group_sizes) # shallow copy
    
    sum_grp_sizes = 0
    for x in group_sizes:
        sum_grp_sizes += x

    sum_frag_impl_sizes = 0
    for x in frag_sizes:
        sum_frag_impl_sizes += x
    # to separate one segment to two fragments, you need
    # at least one block in the middle of the two fragments
    # To separate one segment to n fragments, you need
    # at least n-1 barriers. However, by having k groups,
    # you already have k-1 barriers. You all you need is
    # (n-1) - (k-1) barriers.
    sum_frag_impl_sizes += (nfrags - 1) - (ngrps - 1)

    if sum_frag_impl_sizes > sum_grp_sizes:
        print "fragment size exceeds group sizes",
        exit(1)

    # the allocation algorithm is greedy.
    # pick the largest fragment and put it in the group
    # with largest free space
    frag_sizes = sorted(frag_sizes, reverse=True)
    for frg in frag_sizes:
        space = sorted(free_grp_spaces, reverse=True)[0]
        g_idx = free_grp_spaces.index(space)

        if frg <= space:
            # put frg in group[g_idx]
            grp_frags[g_idx].append(frg)
            free_grp_spaces[g_idx] -= (frg+1) # +1 for the 
                                               #barrier after this frag
        else:
            print "not good, this should not happend"
            exit(1)

    print grp_frags

fragplan([10, 10], [2,3,9,2])

#frags(100, 8, 1000, 100)

#a = stats.lognorm(scale=0.1)
#a = np.random.beta(0.75, 0.25, 10000)
#print a.rvs(2, size=10)
#help(stats.lognorm.rvs)
#help(a.rvs)
#plothist(a)
