import os, sys
import subprocess

curdir = os.path.dirname( os.path.abspath( __file__ ) )
lib_path = os.path.join(curdir, '../') 
sys.path.append(lib_path)
import MWpyFS
import pyWorkload

MOUNTPOINT = '/mnt/scratch/'
WORKLOADPATH = '/tmp/_workload'
PLAYERPATH = '../../build/src/player'


def create_fs():
    if not os.path.exists(MOUNTPOINT):
        os.makedirs(MOUNTPOINT)
    MWpyFS.FormatFS.remakeExt4("/dev/sdb", MOUNTPOINT, "jhe", "FSPerfAtScale", 
                    blockscount=50*1024*1024, blocksize=4096, 
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

def create_sparse_lg_prealloc(dirids, cpuids):
    pairs = zip(dirids, cpuids)
    print pairs

    prod = pyWorkload.producer.Producer(rootdir=MOUNTPOINT, tofile=WORKLOADPATH)
    
    # create preaclloc
    for dirid, cpuid in pairs:
        filepath = os.path.join(get_dirname(dirid), 'file.cpu.'+str(cpuid))
        prod.addSetaffinity(pid=0, cpuid=cpuid)
        prod.addUniOp2(op='open', pid=0, path=filepath)
        prod.addReadOrWrite2(op='write', pid=0, path=filepath, off=0, len=4096)
        prod.addUniOp2(op='fsync', pid=0, path=filepath)
        prod.addUniOp2(op='close', pid=0, path=filepath)

    # create spreading files
    fpath = 'spreadfile'
    prod.addUniOp2(op='open', pid=0, path=fpath)
    for cpuid in cpuids:
        prod.addSetaffinity(pid=0, cpuid=cpuid)
        prod.addReadOrWrite2(op='write', pid=0, path=fpath, off=4096*cpuid, len=4096)
        prod.addUniOp2(op='fsync', pid=0, path=fpath)
    prod.addUniOp2(op='close', pid=0, path=fpath)

    prod.display() 
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

    cmd = ['mpirun', "-np", max_rank+1, PLAYERPATH, WORKLOADPATH]
    cmd = [str(x) for x in cmd]

    proc = subprocess.Popen(cmd) 
    proc.wait()
    return proc.returncode




def main():
    create_fs()
    create_dirs(MOUNTPOINT, 32)

    #create_sparse_lg_prealloc([0, 7, 9, 11, 13, 15, 17, 19], range(8))
    create_sparse_lg_prealloc(range(0, 16, 2), range(8))
    print 'return', play_workload(WORKLOADPATH)

if __name__ == '__main__':
    main()



