import MWpyFS


MWpyFS.FormatFS.makeLoopDevice(
        devname="/dev/loop0",
        tmpfs_mountpoint="/mnt/mytmpfs",
        sizeMB=4096)

MWpyFS.FormatFS.remakeExt4("/dev/loop0", "/mnt/scratch/", "jhe", "plfs", 
                blockscount=1024*1024, blocksize=4096)
