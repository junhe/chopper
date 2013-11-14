import MWpyFS
import os

if not os.path.exists("/mnt/mytmpfs"):
    print "/mnt/mytmpfs does not exist. Creating..."
    os.mkdir("/mnt/mytmpfs")
MWpyFS.FormatFS.makeLoopDevice(
        devname="/dev/loop0",
        tmpfs_mountpoint="/mnt/mytmpfs",
        sizeMB=4096)

print "Loop device has been made :)"

if not os.path.exists("/mnt/scratch"):
    print "/mnt/scratch does not exist. Creating..."
    os.mkdir("/mnt/scratch")

fs_choice = raw_input(
        "What file system do you want to mount on the device?([0]abort[1]xfs|[2]ext4):")

if fs_choice.lower() == 'abort' or fs_choice == '0':
    exit(0)
elif fs_choice.lower() == 'ext4' or fs_choice == '2':
    MWpyFS.FormatFS.remakeExt4("/dev/loop0", "/mnt/scratch/", "jhe", "plfs", 
                    blockscount=1024*1024, blocksize=4096)
elif fs_choice.lower() == 'xfs' or fs_choice == '1':
    MWpyFS.FormatFS.remakeXFS('/dev/loop0', '/mnt/scratch', 'jhe', 'plfs',
                                blocksize=4096)

