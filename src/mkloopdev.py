# Chopper is a diagnostic tool that explores file systems for unexpected
# behaviors. For more details, see paper Reducing File System Tail 
# Latencies With Chopper (http://research.cs.wisc.edu/adsl/Publications/).
#
# Please send bug reports and questions to jhe@cs.wisc.edu.
#
# Written by Jun He at University of Wisconsin-Madison
# Copyright (C) 2015  Jun He (jhe@cs.wisc.edu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import MWpyFS
import os
import sys

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

if len(sys.argv) == 2 and sys.argv[1] == 'nofs':
    # stop here, don't make file system
    exit(0) 

fs_choice = raw_input(
        "What file system do you want to mount on the device?\n"\
        "[0]abort\n"\
        "[1]xfs\n"\
        "[2]ext4\n"\
        "[3]btrfs\n"\
        ":")

if fs_choice.lower() == 'abort' or fs_choice == '0':
    exit(0)
elif fs_choice.lower() == 'xfs' or fs_choice == '1':
    MWpyFS.FormatFS.remakeXFS('/dev/loop0', '/mnt/scratch', 'jhe', 'plfs',
                                blocksize=4096)
elif fs_choice.lower() == 'ext4' or fs_choice == '2':
    MWpyFS.FormatFS.remakeExt4("/dev/loop0", "/mnt/scratch/", "jhe", "plfs", 
                    blockscount=1024*1024, blocksize=4096)
elif fs_choice.lower() == 'btrfs' or fs_choice == '3':
    MWpyFS.FormatFS.btrfs_remake("/dev/loop0", "/mnt/scratch/", "jhe", "plfs", 
                    nbytes=4*1024*1024*1024)

