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

import subprocess
import os
import re
import getpass
import pwd
import grp

def formatToOnePart(devname, confpath):
    conffile = open(confpath, "r")

    cmd = ["sfdisk", devname]
    #cmd = ["cat"]
    p = subprocess.Popen(cmd, stdin=conffile)
    p.wait()
    
    conffile.close()
    print "formatToOnePart:", p.returncode
    return p.returncode

def mountTmpfs(mountpoint, size):
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)
    cmd = ['mount', '-t', 'tmpfs',
           '-o', 'size='+str(size), 'tmpfs', mountpoint]
    cmd = [str(x) for x in cmd]
    print " ".join(cmd), "......"
    proc = subprocess.Popen(cmd)
    proc.wait()
    
    return proc.returncode

def mkImageFile(filepath, size):
    "size is in MB" 
    #cmd = ['dd', 'if=/dev/zero', 'of='+filepath,
           #'bs=1M', 'count='+str(size)]
    cmd = ['truncate', '-s', str(size*1024*1024), filepath]
    print " ".join(cmd), "......"
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode

def mkLoopDevOnFile(devname, filepath):
    cmd = ['losetup', devname, filepath]
    cmd = [str(x) for x in cmd]
    print " ".join(cmd), "......"
    proc = subprocess.Popen(cmd)
    proc.wait()

    return proc.returncode

def delLoopDev(devname):
    cmd = ['losetup', '-d', devname]
    cmd = [str(x) for x in cmd]
    print " ".join(cmd), "......"
    proc = subprocess.Popen(cmd)
    proc.wait()

    return proc.returncode

def isMounted(name):
    "only check is a name is in mounted list"
    name = name.rstrip('/')
    print "isMounted: name:", name
    with open('/etc/mtab', 'r') as f:
        for line in f:
            #print "line:", line,
            line = " " + line + " " # a hack
            if re.search(r'\s'+name+r'\s', line):
                #print " YES"
                return True
            #print " NO"
    return False

def isLoopDevUsed(path):
    cmd = ['losetup','-f']
    proc = subprocess.Popen(cmd, 
            stdout=subprocess.PIPE)
    
    proc.wait()

    outstr = proc.communicate()[0]
    outstr = outstr.strip()
    print "isLoopUsed:", outstr+"END"
    if outstr > path:
        return True
    else:
        return False

def makeLoopDevice(devname, tmpfs_mountpoint, sizeMB, img_file=None):
    "size is in MB. The tmpfs for this device might be bigger than sizeMB"
    if not devname.startswith('/dev/loop'):
        print 'you are requesting to create loop device on a non-loop device path'
        exit(1)

    if not os.path.exists(tmpfs_mountpoint):
        os.makedirs(tmpfs_mountpoint)

    # umount the FS mounted on loop dev
    if isMounted(devname):
        if umountFS(devname) != 0:
            print "unable to umount", devname
            exit(1)
        else:
            print devname, 'umounted'
    else:
        print devname, "is not mounted"

    # delete the loop device
    if isLoopDevUsed(devname):
        if delLoopDev(devname) != 0:
            print "Failed to delete loop device"
            exit(1)
    else:
        print devname, "is not in use"


    # umount the tmpfs the loop device is on
    if isMounted(tmpfs_mountpoint):
        if umountFS(tmpfs_mountpoint) != 0:
            print "unable to umount tmpfs at", tmpfs_mountpoint
            exit(1)
        print tmpfs_mountpoint, "umounted"
    else:
        print tmpfs_mountpoint, "is not mounted"


    mountTmpfs(tmpfs_mountpoint, int(sizeMB*1024*1024*1.1))
    imgpath = os.path.join(tmpfs_mountpoint, "disk.img")
    if img_file == None:
        mkImageFile(imgpath, sizeMB)
    else:
        cmd = ['cp', img_file, imgpath]
        print 'doing...', cmd
        subprocess.call(cmd)

    mkLoopDevOnFile(devname, imgpath) 

def makeXFS(devname, blocksize=4096):
    "TODO: blockscount is not used"
    cmd = ["mkfs.xfs", 
           "-f",
           "-b", 'size='+str(blocksize),
           devname]
    cmd = [str(x) for x in cmd]
    p = subprocess.Popen(cmd)
    p.wait()
    print "makeXFS:", p.returncode
    return p.returncode


def makeExt4(devname, blockscount=16777216, blocksize=4096, makeopts=None):
    
    if makeopts == None:
        cmd = ["mkfs.ext4", 
               "-b", blocksize,
               "-O", "has_journal,extent,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize",
               devname, blockscount]
    else:
        cmd = ["mkfs.ext4", 
               "-b", blocksize]
        cmd.extend(makeopts)
        cmd.extend([devname, blockscount])

    cmd = [str(x) for x in cmd]
    p = subprocess.Popen(cmd)
    p.wait()
    print "makeExt4:", p.returncode
    return p.returncode

def makeExt3(devname, blockscount, blocksize):
    cmd = ['mkfs.ext3',
           '-b', blocksize,
           devname, blockscount]
    cmd = [str(x) for x in cmd]
    p = subprocess.Popen(cmd)
    p.wait()
    print "makeExt3:", p.returncode
    return p.returncode

def umountFS(mountpoint):
    cmd = ["umount", mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "umountFS:", p.returncode
    return p.returncode

def mountExt4(devname, mountpoint):
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)

    cmd = ["mount", "-t", "ext4", devname, mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "mountExt4:", p.returncode
    return p.returncode

def remountFS(devname, mountpoint):
    umountFS(mountpoint)
    mountFS(devname, mountpoint)

def mountFS(devname, mountpoint, opts=""):
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)

    if opts != "":
        cmd = ["mount", '-o', opts, devname, mountpoint]
    else:
        cmd = ["mount", devname, mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "mountFS", p.returncode
    return p.returncode


def mountXFS(devname, mountpoint):
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)

    cmd = ["mount", "-t", "xfs", "-o", "osyncisosync", devname, mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "mountFS", p.returncode
    return p.returncode

def chDirOwner(mountpoint, username, groupname):
    try:
        uid = pwd.getpwnam(username).pw_uid
        gid = grp.getgrnam(groupname).gr_gid
    
        print username,groupname,uid,gid
        os.chown(mountpoint, uid, gid)
    except:
        print "cannot chown", username, ":", groupname, "in system"

    return 0

def remakeXFS(partition, mountpoint, username, groupname, 
                blocksize=4096):
    "= format that partition"
    print "remaking XFS...."
    if isMounted(mountpoint):
        print mountpoint, "is mounted"
        ret = umountFS(mountpoint)
        if ret != 0:
            print "Error in umountFS: this should not happen"
            exit(1)
        else:
            print mountpoint, "is umounted"
    else:
        print mountpoint, "is NOT mounted."

    ret = makeXFS(partition, blocksize=blocksize)
    if ret != 0:
        print "Error in makeXFS: this should not happen"
        exit(1)
    ret = mountXFS(partition, mountpoint)
    if ret != 0:
        print "Error in mountFS: this should not happen"
        exit(1)

    # all of the above has to success except this one
    chDirOwner(mountpoint, username, groupname)


def remakeExt4(partition, mountpoint, username, groupname, 
                blockscount=16777216, blocksize=4096, makeopts=None):
    "= format that partition"
    print "remaking ext4...."
    if isMounted(mountpoint):
        print mountpoint, "is mounted"
        ret = umountFS(mountpoint)
        if ret != 0:
            print "Error in umountFS: this should not happen"
            exit(1)
        else:
            print mountpoint, "is umounted"
    else:
        print mountpoint, "is NOT mounted."

    ret = makeExt4(partition, blockscount, blocksize, makeopts)
    if ret != 0:
        print "Error in makeExt4: this should not happen"
        exit(1)
    ret = mountExt4(partition, mountpoint)
    if ret != 0:
        print "Error in mountExt4: this should not happen"
        exit(1)

    # all of the above has to success except this one
    chDirOwner(mountpoint, username, groupname)

def remakeExt3(partition, mountpoint, username, groupname, 
                blockscount=16777216, blocksize=4096):
    "= format that partition"
    print "remaking ext3...."
    if isMounted(mountpoint):
        print mountpoint, "is mounted"
        ret = umountFS(mountpoint)
        if ret != 0:
            print "Error in umountFS: this should not happen"
            exit(1)
        else:
            print mountpoint, "is umounted"
    else:
        print mountpoint, "is NOT mounted."

    ret = makeExt3(partition, blockscount, blocksize)
    if ret != 0:
        print "Error in makeExt3: this should not happen"
        exit(1)
    ret = mountFS(partition, mountpoint)
    if ret != 0:
        print "Error in mountExt3: this should not happen"
        exit(1)

    # all of the above has to success except this one
    chDirOwner(mountpoint, username, groupname)

def buildNewExt4(devname, mountpoint, confpath, username, groupname):
    devname_part1 = devname+"1"
    
    ret = umountFS(mountpoint)
    if ret != 0:
        print "Error in umountFS: this should not happen"
        print "Tolerated"

    ret = formatToOnePart(devname, confpath)
    if ret != 0:
        print "Error in formatToOnePart: this should not happen"
        print "Tolerated"

    remakeExt4(devname_part1, mountpoint, username, groupname)

def enable_ext4_mballoc_debug(enable):
    with open("/sys/kernel/debug/ext4/mballoc-debug", 'w') as f:
        if enable == True:
            f.write("1")
        else:
            f.write("0")
    return

def send_dmesg(msg):
    with open("/dev/kmsg", 'w') as f:
        f.write(msg)

def xfs_freeze(mountpoint):
    cmd = ["xfs_freeze", "-f", mountpoint]
    return subprocess.call(cmd)

def xfs_unfreeze(mountpoint):
    cmd = ["xfs_freeze", "-u", mountpoint]
    return subprocess.call(cmd)

def xfs_repair(devname):
    cmd = ["xfs_repair", devname]
    return subprocess.call(cmd)

def btrfs_mkfs(devname, nbytes):
    cmd = ['mkfs.btrfs', '-b', str(nbytes), devname]
    return subprocess.call(cmd)

def btrfs_mount(devname, mountpoint):
    cmd = ['mount', devname, mountpoint]
    return subprocess.call(cmd)

def btrfs_remake(partition, mountpoint, username, groupname, 
                nbytes):
    "= format that partition"
    print "remaking btrfs...."
    if isMounted(mountpoint):
        print mountpoint, "is mounted"
        ret = umountFS(mountpoint)
        if ret != 0:
            print "Error in umountFS: this should not happen"
            exit(1)
        else:
            print mountpoint, "is umounted"
    else:
        print mountpoint, "is NOT mounted."

    ret = btrfs_mkfs(partition, nbytes)
    if ret != 0:
        print "Error in btrfs_mkfs: this should not happen"
        exit(1)
    ret = btrfs_mount(partition, mountpoint)
    if ret != 0:
        print "Error in btrfs_mount: this should not happen"
        exit(1)

    # all of the above has to success except this one
    chDirOwner(mountpoint, username, groupname)

