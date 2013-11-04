import MWpyFS
import os

if not os.path.exists("/mnt/mytmpfs"):
    print "/mnt/mytmpfs does not exist. Creating..."
    os.mkdir("/mnt/mytmpfs")
MWpyFS.FormatFS.makeLoopDevice(
        devname="/dev/loop0",
        tmpfs_mountpoint="/mnt/mytmpfs",
        sizeMB=4096)
exit()
if not os.path.exists("/mnt/scratch"):
    print "/mnt/scratch does not exist. Creating..."
    os.mkdir("/mnt/scratch")
MWpyFS.FormatFS.remakeExt4("/dev/loop0", "/mnt/scratch/", "jhe", "plfs", 
                blockscount=1024*1024, blocksize=4096)
