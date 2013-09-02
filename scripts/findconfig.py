import itertools
import pprint


def product(elems):
    prd = 1
    for x in elems:
        prd *= x
    return prd

def getWorkloadParameters():
    targetsize = 1*1024*1024*1024

    nseasons=[4]
    np = [1,4,8]
    ndir_per_pid = [1,4,8]
    nfiles_per_dir = [1,4,16]
    nwrites_per_file = [1024, 4096]
    wstride_factors = ["contigous", "onewritehole"]
    #wsize = 
    #wstride = 


    parameters = [nseasons, np, ndir_per_pid, 
                  nfiles_per_dir, nwrites_per_file, wstride_factors]
    paralist = list(itertools.product(*parameters))

    settingtable = [] # each row is a dictionary
    cnt = 0
    for para in paralist:
        print cnt
        cnt += 1
        para = list(para)
        totaldirs = product(para[0:3])
        totalfiles = product(para[0:4])
        totalwrites = product(para[0:5])

        wsize = targetsize/totalwrites
        if para[5] == "contigous":
            wstride = wsize
        else:
            wstride = wsize*2
        para[5] = wstride
        
        print para, "totaldirs:", totaldirs, "totalfiles:", \
                totalfiles, "totalwrites:", totalwrites, "wsize:", \
                wsize, "wstride:", wstride,\
                "aggfilesize:", product(para)

        dict = {"np":para[1],
                "ndir_per_pid":para[2],
                "nfiles_per_dir":para[3],
                "nwrites_per_file":para[4],
                "wsize":wsize,
                "wstride":wstride}
        # trim several unrealistic bad ones
        #if wsize > 1*1024*1024:
            #print "Skip this...."
            #continue

        settingtable.append(dict)

    pprint.pprint(settingtable)

getWorkloadParameters()

