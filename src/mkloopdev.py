import MWpyFS


MWpyFS.FormatFS.makeLoopDevice(
        devname="/dev/loop0"
        tmpfs_mountpoint="/mnt/mytmpfs"),
        sizeMB=1024)
