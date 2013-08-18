#!/usr/bin/python 

import subprocess
import os

def formatToOnePart(devname, confpath):
    conffile = open(confpath, "r")

    cmd = ["sfdisk", devname]
    #cmd = ["cat"]
    p = subprocess.Popen(cmd, stdin=conffile)
    p.wait()
    
    conffile.close()
    print "formatToOnePart:", p.returncode
    return p.returncode

def makeExt4(devname):
    cmd = ["mkfs.ext4", devname]
    p = subprocess.Popen(cmd)
    p.wait()
    print "makeExt4:", p.returncode
    return p.returncode

def umountFS(mountpoint):
    cmd = ["umount", "-f", mountpoint]
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

def buildNewExt4(devname, mountpoint, confpath):
    devname_part1 = devname+"1"
    
    ret = umountFS(mountpoint)

    ret = formatToOnePart(devname, confpath)
    if ret != 0:
        print "this should not happen"
        return ret
    ret = makeExt4(devname_part1)
    if ret != 0:
        print "this should not happen"
        return ret
    ret = mountExt4(devname_part1, mountpoint)
    if ret != 0:
        print "this should not happen"
        return ret

buildNewExt4("/dev/sdb", "/mnt/scratch", "../../conf/sfdisk.conf")

