import os
import subprocess
import pprint


def btrfs_debug_tree(partition):
    cmd = ['btrfs-debug-tree', partition]
    proc = subprocess.Popen(cmd, 
                            stdout=subprocess.PIPE)

    db_tree_lines = [] 
    for line in proc.stdout:
        db_tree_lines.append(line)
    proc.wait()
    return db_tree_lines


pprint.pprint(btrfs_debug_tree('/dev/loop0'))
#print btrfs_debug_tree('/dev/loop0')
