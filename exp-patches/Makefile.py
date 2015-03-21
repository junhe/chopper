#!/usr/bin/env python
import itertools
import random
import argparse
import re
import subprocess
import os
import sys
import shlex
import time
import glob
from time import localtime, strftime

def shcmd(cmd, ignore_error=False):
    print 'Doing:', cmd
    ret = subprocess.call(cmd, shell=True)
    print 'Returned', ret, cmd
    if ignore_error == False and ret != 0:
        exit(ret)
    return ret

class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

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

#########################################################
# Git helper
# you can use to get hash of the code, which you can put 
# to your results
def git_latest_hash():
    cmd = ['git', 'log', '--pretty=format:"%h"', '-n', '1']
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE)
    proc.wait()
    hash = proc.communicate()[0]
    hash = hash.strip('"')
    print hash
    return hash

def git_commit(msg='auto commit'):
    shcmd('git commit -am "{msg}"'.format(msg=msg), 
            ignore_error=True)

########################################################
# table = [
#           {'col1':data, 'col2':data, ..},
#           {'col1':data, 'col2':data, ..},
#           ...
#         ]
def table_to_file(table, filepath, adddic=None):
    'save table to a file with additional columns'
    with open(filepath, 'w') as f:
        colnames = table[0].keys()
        if adddic != None:
            colnames += adddic.keys()
        colnamestr = ';'.join(colnames) + '\n'
        f.write(colnamestr)
        for row in table:
            if adddic != None:
                rowcopy = dict(row.items() + adddic.items())
            else:
                rowcopy = row
            rowstr = [rowcopy[k] for k in colnames]
            rowstr = [str(x) for x in rowstr]
            rowstr = ';'.join(rowstr) + '\n'
            f.write(rowstr)


###########################################################
###########################################################
def compile_linux():
    #with cd("/mnt/scratch-sda4/"):
        #shcmd("git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git")

    with cd("/mnt/scratch-sda4/linux"):
        #shcmd("cp -vi /boot/config-`uname -r` .config")
        #shcmd("yes ''| make oldconfig")
        #shcmd("sudo apt-get install -y git-core libncurses5 libncurses5-dev libelf-dev asciidoc binutils-dev linux-source qt3-dev-tools libqt3-mt-dev libncurses5 libncurses5-dev fakeroot build-essential crash kexec-tools makedumpfile kernel-wedge kernel-package")
        #shcmd("make menuconfig")
        #shcmd("make -j3")
        shcmd("sudo make INSTALL_MOD_PATH=/mnt/scratch-sda4/ modules_install")
        shcmd("sudo make install")



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

def umountFS(mountpoint):
    cmd = ["umount", mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "umountFS:", p.returncode
    return p.returncode

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

def mkImageFile(filepath, size):
    "size is in MB" 
    #cmd = ['dd', 'if=/dev/zero', 'of='+filepath,
           #'bs=1M', 'count='+str(size)]
    cmd = ['truncate', '-s', str(size*1024*1024), filepath]
    print " ".join(cmd), "......"
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode

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

def mountExt4(devname, mountpoint):
    if not os.path.exists(mountpoint):
        os.makedirs(mountpoint)

    cmd = ["mount", "-t", "ext4", devname, mountpoint]
    p = subprocess.Popen(cmd)
    p.wait()
    print "mountExt4:", p.returncode
    return p.returncode

def makeExt4(devname, blocksize=4096, makeopts=None):
    
    if makeopts == None:
        cmd = ["mkfs.ext4", 
               "-b", blocksize,
               "-O", "has_journal,extent,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize",
               devname]
    else:
        cmd = ["mkfs.ext4", 
               "-b", blocksize]
        cmd.extend(makeopts)
        cmd.extend([devname])

    cmd = [str(x) for x in cmd]
    p = subprocess.Popen(cmd)
    p.wait()
    print "makeExt4:", p.returncode
    return p.returncode

def create_ext4_on_loop():
    makeLoopDevice("/dev/loop0", "/mnt/tmpfs", 4096, img_file=None)
    makeExt4("/dev/loop0", blocksize=4096, makeopts=None)
    mountExt4(devname="/dev/loop0", mountpoint="/mnt/ext4onloop")
    shcmd("sudo chown jhe:FSPerfAtScale -R /mnt/ext4onloop")

def enable_ext4_mballoc_debug():
    shcmd("echo 1|sudo tee /sys/module/ext4/parameters/mballoc_debug")

def disable_ext4_mballoc_debug():
    shcmd("echo 0|sudo tee /sys/module/ext4/parameters/mballoc_debug")

def run_exp():
    filepath = "/mnt/ext4onloop/testfile"

    enable_ext4_mballoc_debug()
    shcmd("./alignment/a.out {path}".format(path=filepath))
    shcmd("filefrag -sv {path}".format(path=filepath))

def run_exp_specialend():
    filepath = "/mnt/ext4onloop/testfile"

    enable_ext4_mballoc_debug()
    shcmd("./specialend/a.out {path}".format(path=filepath))
    shcmd("filefrag -sv {path}".format(path=filepath))

def run_exp_backwards():
    filepath = "/mnt/ext4onloop/testfile"

    enable_ext4_mballoc_debug()
    shcmd("./backwards/a.out {path}".format(path=filepath))
    shcmd("filefrag -sv {path}".format(path=filepath))

###########################################################
###########################################################

def main():
    #function you want to call
    #compile_linux()
    create_ext4_on_loop()
    #enable_ext4_mballoc_debug()
    run_exp()
    #run_exp_specialend()
    #run_exp_backwards()
    pass

def _main():
    parser = argparse.ArgumentParser(
            description="This file hold command stream." \
            'Example: python Makefile.py doexp1 '
            )
    parser.add_argument('-t', '--target', action='store') 
    args = parser.parse_args()

    if args.target == None:
        main()
    else:
        # WARNING! Using argument will make it less reproducible
        # because you have to remember what argument you used!
        targets = args.target.split(';')
        for target in targets:
            eval(target)

if __name__ == '__main__':
    _main()

