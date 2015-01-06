import random
import os
import math
import subprocess
import pprint
try:
    import matplotlib.pyplot as plt
except ImportError:
    #print "This machine does not have matplotlib, skipped importing."
    pass


import Monitor
import FormatFS

# Making image
# 1. calculate the size of hole file and spaceholder file
#    the sum of them should be very close to the disk size.
# 2. create hole file
# 3. create spaceholder file
# 4. a. punch hole file
#    b. or delete hole file and fragment by seeking and
#       writing.
# 
# Note that, since we want the hole file and place holder
# files to be as contiguous as possible, but ext3 is really
# bad at it if you write it block by block. So you'd better
# write bigger chunks at a time in ext3 (and ext2). 
#
# TODO: 
# 1. implement solid file creator for btrfs, ext4, ...
#   "As  of the Linux Kernel v2.6.31, the fallocate system call is supported
#   by the btrfs, ext4, ocfs2, and xfs filesystems."
#   So we can use fallocate system call to create solid
#   file for ext4, btrfs, xfs.
# 2. implement solid file creator for ext3/2...
# 3. implement file puncher for btrfs, ...
# 4. implement file puncher for ext3, ...
# 5. implement hole file -> place holder -> punching file


def plothist(x):
    try:
        plt.hist(x, 1000, facecolor='g', alpha=0.75)
        plt.show()
    except:
        print "Trivial operation skipped"


def get_extent_distribution( mu, sigma ):
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

    ret_dic = {
                'ratios': pr_list,
                'overhead': overhead_pr
              }
    return ret_dic

def generate_lognormal_sizes_uniquebytes( mu, sigma, 
                                        hard_maxbytes):
    # Search my Evernot for title "overhead calculation of puncher"
    # for the explanation of overhead calculation

    dist = get_extent_distribution(mu, sigma)
    pr_list = dist['ratios']
    overhead_pr = dist['overhead']

    ret_sizes = []
    available_bytes = hard_maxbytes*1/float(1+overhead_pr)

    print 'available_bytes', available_bytes
    
    for i, pr in enumerate(pr_list):
        # count of extent of size 2^i blocks
        ext_size = 4096*2**i
        ext_cnt = available_bytes * pr / ext_size
        #print i, pr, ext_cnt
        ext_cnt = int(ext_cnt)
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
    
    #print xlist
    return szlist

def make_holes ( szlist, specfilesize ):
    off = 0
    holelist = []
    for sz in szlist:
        off += 4096
        hole = (off, sz)
        holelist.append( hole )
        off += sz
    holelist.append((-1,-1))

    totalsize = off + 4096

    if specfilesize == False:
        totalsize = -2
    holelist.insert(0, (0, totalsize))

    return holelist

def save_holelist_to_file(holelist, filepath):
    with open(filepath, 'w') as f:
        for extent in holelist:
            extent = [ str(x) for x in extent ]
            line = ' '.join(extent)
            f.write(line + '\n')
    print 'file saved'

def make_hole_file( holelistfile, targetfile, punchmode):
    curdir = os.path.dirname( os.path.abspath( __file__ ) )
    puncherpath = os.path.join( curdir, '../../build/src/puncher' )

    cmd = [puncherpath, targetfile, holelistfile, punchmode]
    cmd = [str(x) for x in cmd]
    return subprocess.call(cmd)

def lognorm_cdf(x, mu, sigma):
    "check wikipedia"
    #print 'x:', x
    if x == 0:
        return 0

    top = -(math.log(x)-mu)
    down = sigma*math.sqrt(2)
    return math.erfc(top/down)/2
    #return math.erfc(-(math.log(x)-mu)/(sigma*math.sqrt(2)))/2

def lognorm_probability_range(a, b, mu, sigma):
    "it returns P(a<x<b) by cdf"
    cumu_a = lognorm_cdf(a, mu, sigma)
    cumu_b = lognorm_cdf(b, mu, sigma)
    return abs(cumu_b-cumu_a)

def layoutnumber2mu_sigma(layoutnumber):
    #d = data.frame(meanlog=log(seq(2,21,length=5)), sdlog=seq(1,0.1,length=5))
    dict = {
        1 : ( 0.6931472 , 1 ),
        2 : ( 1.9095425 , 0.775 ),
        3 : ( 2.442347 , 0.55 ),
        4 : ( 2.7880929 , 0.325 ),
        5 : ( 3.0445224 , 0.1 )
        }
    mu,sigma = dict[layoutnumber]

    return (mu,sigma)

def create_frag_file( layoutnumber, 
                    hard_maxbytes, 
                    targetfile, 
                    punchmode, specfilesize):

    mu,sigma = layoutnumber2mu_sigma(layoutnumber)

    szlist = generate_lognormal_sizes_uniquebytes\
                        (mu, sigma, hard_maxbytes)
    random.seed(1)
    random.shuffle( szlist )
    #print(szlist)
    holelist = make_holes(szlist, specfilesize) 
    save_holelist_to_file( holelist, 
                            '/tmp/_holelist' )
    ret = make_hole_file( '/tmp/_holelist', targetfile, punchmode )
    return ret

    
