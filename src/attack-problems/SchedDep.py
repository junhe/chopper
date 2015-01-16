import os, sys
import itertools
import random
import subprocess

curdir = os.path.dirname( os.path.abspath( __file__ ) )
lib_path = os.path.join(curdir, '../') 
sys.path.append(lib_path)
import MWpyFS
import pyWorkload


MOUNTPOINT = '/mnt/scratch/'
WORKLOADPATH = '/tmp/_workload'
PLAYERPATH = '../../build/src/player'
CHUNKSIZE = None 
DEV = '/dev/sdc'

def ParameterCombinations(parameter_dict):
    """
    Get all the cominbation of the values from each key
    http://tinyurl.com/nnglcs9
    Input: parameter_dict={
                    p0:[x, y, z, ..],
                    p1:[a, b, c, ..],
                    ...}
    Output: [
             {p0:x, p1:a, ..},
             {..},
             ...
            ]
    """
    d = parameter_dict
    return [dict(zip(d, v)) for v in itertools.product(*d.values())]


def create_fs():
    if not os.path.exists(MOUNTPOINT):
        os.makedirs(MOUNTPOINT)
    MWpyFS.FormatFS.remakeExt4(DEV, MOUNTPOINT, "jhe", "ScalableFS", 
                    blockscount=698*1024*1024, blocksize=4096, 
                    makeopts= ["-O", "has_journal,extent,huge_file,^flex_bg,uninit_bg,dir_nlink,extra_isize"]
                    )

def create_dirs(toppath, n):
    "create n dirs at toppath"
    for i in range(n):
        dirname = get_dirname(i)
        dirpath = os.path.join(toppath, dirname)
        os.makedirs(dirpath)
        subprocess.call(['sync'])

def get_dirname(i):
    return 'dir.'+str(i)

def create_sparse_lg_prealloc(prod, dirids, cpuids):
    pairs = zip(dirids, cpuids)
    
    # create preaclloc
    for dirid, cpuid in pairs:
        filepath = os.path.join(get_dirname(dirid), 'file.cpu.'+str(cpuid))
        prod.addSetaffinity(pid=0, cpuid=cpuid)
        prod.addUniOp2(op='open', pid=0, path=filepath)
        prod.addReadOrWrite2(op='write', pid=0, path=filepath, off=0, len=CHUNKSIZE)
        prod.addUniOp2(op='fsync', pid=0, path=filepath)
        prod.addUniOp2(op='close', pid=0, path=filepath)

def create_speadfile(prod, cpuids, fileid):
    # create spreading files
    fpath = 'spreadfile.'+str(fileid)
    prod.addUniOp2(op='open', pid=0, path=fpath)
    #random.shuffle(cpuids)
    for cpuid in cpuids:
        prod.addSetaffinity(pid=0, cpuid=cpuid)
        prod.addReadOrWrite2(op='write', pid=0, path=fpath, off=CHUNKSIZE*cpuid, len=CHUNKSIZE)
        prod.addUniOp2(op='fsync', pid=0, path=fpath)
    prod.addUniOp2(op='close', pid=0, path=fpath)

def create_workload(cpuids, nfiles):
    prod = pyWorkload.producer.Producer(rootdir=MOUNTPOINT, tofile=WORKLOADPATH)
    
    dirids = [id*2 for id in cpuids]
    create_sparse_lg_prealloc(prod, dirids, cpuids)

    for fileid in range(nfiles):
        create_speadfile(prod, cpuids, fileid)

    #prod.display() 
    prod.saveWorkloadToFile()
    
def play_workload(descpath):
    # find out how many proc we need
    max_rank = 0
    with open( WORKLOADPATH, 'r' ) as f:
        for line in f:
            items = line.split(";")
            rank  = int(items[0])
            if rank > max_rank:
                max_rank = rank

    cmd = ['mpirun', 
           '-mca', 'btl',  '^openib',  
            "-np", max_rank+1, PLAYERPATH, WORKLOADPATH]
    cmd = [str(x) for x in cmd]

    proc = subprocess.Popen(cmd) 
    proc.wait()
    return proc.returncode

def create_big_file():
    f = open("/boot/initrd.img-3.12.5-031205-generic", 'r')
    buf = f.read(2**20)
    f.close()

    f = open("/tmp/bigs2", "w")
    for i in range(128):
        f.write(buf)
    f.close()

def clean_all_cache(mountpoint):
    MWpyFS.FormatFS.remountFS(DEV, mountpoint)

    print 'cleanging caches...'
    subprocess.call(['sync'])
    cmd = "echo 3 > /proc/sys/vm/drop_caches"
    subprocess.call(cmd, shell=True)

    if not os.path.exists('/tmp/bigs2'):
        create_big_file()
    cmd = "cp /tmp/bigs2 "+mountpoint
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print cmd, 'failed'
        exit(1)

    subprocess.call(['sync'])
    cmd = "echo 3 > /proc/sys/vm/drop_caches"
    subprocess.call(cmd, shell=True)

    cmd = "mv "+mountpoint+"/bigs2 /tmp/bigs3"
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print cmd, 'failed'
        exit(1)

    subprocess.call(['sync'])
    cmd = "echo 3 > /proc/sys/vm/drop_caches"
    subprocess.call(cmd, shell=True)

def run_exp(mode, mountpoint, filenames, size, info=None):
    if info == None:
        header = ' '
        datas = ' '
    else:
        header = ' '.join(info.keys())
        datas = [str(x) for x in info.values()]
        datas = ' '.join(datas)

    filepaths = [os.path.join(mountpoint, filename) for filename in filenames]
    filepaths = ','.join(filepaths)
    cmd = ['./perform', mode, filepaths, size,
           header, datas ]
    cmd = [str(x) for x in cmd]
    #print cmd
    subprocess.call(cmd)

def batch_experiments(nfiles, ncpus, repeat):
    create_fs()
    create_dirs(MOUNTPOINT, 128)

    create_workload(range(ncpus), nfiles)
    ret = play_workload(WORKLOADPATH)

    print '--------------- read 8 extents------------'
    for i in range(repeat):
        filenames = ['spreadfile.'+str(i) for i in range(nfiles)]
        clean_all_cache(MOUNTPOINT)
        run_exp('r', MOUNTPOINT, filenames, ncpus*CHUNKSIZE, {'nextents':ncpus, 'ncpus':ncpus, 'nfiles':nfiles} )

    print '--------------- write 8 extents------------'
    for i in range(repeat):
        filenames = ['spreadfile.'+str(i) for i in range(nfiles)]
        clean_all_cache(MOUNTPOINT)
        run_exp('w', MOUNTPOINT, filenames, ncpus*CHUNKSIZE, {'nextents':ncpus, 'ncpus':ncpus, 'nfiles':nfiles} )

    #print '--------------- delete ------------'
    #filenames = ['spreadfile.'+str(i) for i in range(nfiles)]
    #for filename in filenames:
        #os.remove(os.path.join(MOUNTPOINT, filename))
    #subprocess.call(['sync'])

    create_fs()

    print '--------------- write 1 extents------------'
    for i in range(repeat):
        filenames = ['spreadfile.'+str(i) for i in range(nfiles)]
        clean_all_cache(MOUNTPOINT)
        run_exp('w', MOUNTPOINT, filenames, ncpus*CHUNKSIZE, {'nextents':1, 'ncpus':ncpus, 'nfiles':nfiles} )

    print '--------------- read 1 extents------------'
    for i in range(repeat):
        filenames = ['spreadfile.'+str(i) for i in range(nfiles)]
        clean_all_cache(MOUNTPOINT)
        run_exp('r', MOUNTPOINT, filenames, ncpus*CHUNKSIZE, {'nextents':1, 'ncpus':ncpus, 'nfiles':nfiles})


def main():
    global CHUNKSIZE
    paras = { 
              #'nfiles':[1, 50],
              #'ncpus'  :[2, 64]

              'nfiles':[1, 10, 100],
              'ncpus'  :[2, 4, 8, 16, 64]
            }
    paralist = ParameterCombinations(paras)
    paralist = paralist * 5
    random.shuffle(paralist)
    for conf in paralist:
        #print conf
        CHUNKSIZE = 64*1024/conf['ncpus']
        batch_experiments(nfiles=conf['nfiles'], ncpus=conf['ncpus'], repeat=1)

if __name__ == '__main__':
    main()

