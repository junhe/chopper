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
import time
import MWpyFS
import os
import sys
import itertools
import pprint
import chpConfig

# where we mount the fs to be tested and run workload
workmount = chpConfig.parser.get('system', 'mountpoint')
tmpmount = chpConfig.parser.get('system', 'tmpfs_mountpoint')
username = chpConfig.parser.get('system', 'username')
usergroup = chpConfig.parser.get('system', 'groupname')

def ParameterCominations(parameter_dict):
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

def fill_solid_file(filepath, size):
    cmd = ['../build/src/filefiller',
           filepath, size]
    cmd = [str(x) for x in cmd]
    ret = subprocess.call(cmd)
    if ret != 0:
        with open('/tmp/make_disk_image.log', 'a') as f:
            msg = "Failed to fill {0} of size {1}\n".\
                    format(filepath, size)
            f.write(msg)
            f.flush()
    return ret

def fallocate_solid_file(filepath, size):
    cmd = ['fallocate',
           '-o', 0,
           '-l', size,
           filepath]
    cmd = [str(x) for x in cmd]
    print cmd
    ret = subprocess.call(cmd)
    if ret != 0:
        with open('/tmp/make_disk_image.log', 'a') as f:
            msg = "Failed to allocate {0} of size {1}\n".\
                    format(filepath, size)
            f.write(msg)
            f.flush()
        exit(1)
    return ret


def produce_new_inputfile(orig_path, 
                          new_path,
                          config_dict):
    """
    config_dict = {
                    'FSused:': [4, 'GB'] 
                  }
    """
    orig_f = open(orig_path, 'r')
    new_f = open(new_path, 'w')

    for line in orig_f:
        #print line,
        items = line.split()
        #print items
        if len(items) > 0 and items[0] in config_dict.keys():
            newline = [items[0]] + config_dict[items[0]]
            newline = [str(x) for x in newline]
            newline = ' '.join( newline )
            newline += '\n'
        else:
            newline = line
        #print newline,
        new_f.write( newline )
    orig_f.close()
    new_f.close()

def run_impressions(config_dict):
    inputpath = '/tmp/newinputfile'
    produce_new_inputfile('./impressions-v1/inputfile.orig',
                          inputpath,
                          config_dict)
    cmd = ['./impressions-v1/impressions',
           inputpath]
    proc = subprocess.Popen(cmd)
    proc.wait()

def make_file_system(fstype, disksize):
    """
    fstype: ext4, xfs, btrfs
    disksize: in Bytes
    """
    if not os.path.exists(tmpmount):
        print tmpmount, "does not exist. Creating..."
        os.mkdir(tmpmount)
    MWpyFS.FormatFS.makeLoopDevice(
            devname="/dev/loop0",
            tmpfs_mountpoint=tmpmount,
            sizeMB=disksize/(1024*1024))

    print "Loop device has been made :)"

    if not os.path.exists(workmount):
        print workmount, "does not exist. Creating..."
        os.mkdir(workmount)

    if fstype == 'xfs':
        MWpyFS.FormatFS.remakeXFS('/dev/loop0', 
                                  workmount,
                                  username, usergroup,
                                  blocksize=4096)
    elif fstype == 'ext4':
        MWpyFS.FormatFS.remakeExt4("/dev/loop0", 
                                   workmount,
                                   username, usergroup, 
                                   blockscount=disksize/4096, 
                                   blocksize=4096)
    elif fstype == 'ext3':
        MWpyFS.FormatFS.remakeExt3("/dev/loop0", 
                                   workmount,
                                   username, usergroup, 
                                   blockscount=disksize/4096, 
                                   blocksize=4096)
    elif fstype == 'btrfs':
        MWpyFS.FormatFS.btrfs_remake("/dev/loop0", 
                                     workmount,
                                     username, usergroup, 
                                     nbytes=disksize)

def release_image():
    # umount the FS mounted on loop dev
    devname = '/dev/loop0'
    if MWpyFS.FormatFS.isMounted(devname):
        if MWpyFS.FormatFS.umountFS(devname) != 0:
            print "unable to umount", devname
            exit(1)
        else:
            print devname, 'umounted'
    else:
        print devname, "is not mounted"

    # delete the loop device
    if MWpyFS.FormatFS.isLoopDevUsed(devname):
        if MWpyFS.FormatFS.delLoopDev(devname) != 0:
            print "Failed to delete loop device"
            exit(1)
    else:
        print devname, "is not in use"

def use_one_image(fstype, disksize, used_ratio, layoutnumber, mountopts):
    imgpath = get_image_path(fstype, disksize, 
                             used_ratio, layoutnumber)

    if not os.path.exists(imgpath):
        # image is not there, need to make one
        # then use the one just made
        print 'need to make a new image'
        make_one_image_solidfile(fstype, disksize, 
                          used_ratio, layoutnumber)
        print '-------- before mkLoopDevOnFile'
        MWpyFS.FormatFS.mkLoopDevOnFile('/dev/loop0', 
                os.path.join(tmpmount, 'disk.img'))
    else:
        # there is a image, just use it
        print 'have the image already, just use it'
        if not os.path.exists(tmpmount):
            print tmpmount, "does not exist. Creating..."
            os.mkdir(tmpmount)
        MWpyFS.FormatFS.makeLoopDevice(
                devname="/dev/loop0",
                tmpfs_mountpoint=tmpmount,
                sizeMB=disksize/(1024*1024),
                img_file = imgpath
                )
    MWpyFS.FormatFS.mountFS('/dev/loop0', workmount, opts=mountopts)

def make_hole_file(filepath, filesize, 
                   layoutnumber, punchmode, specfilesize=True):
    # this function fragments the free space on disk by 
    # allocating free space to a large file and punch holes
    # in the large file.
    ret = \
     MWpyFS.filepuncher.create_frag_file(
             layoutnumber, filesize, 
             filepath, punchmode, specfilesize)
    return ret

def get_image_path(fstype, disksize, used_ratio, 
                   layoutnumber):
    newimagename = ['fstype', fstype, 
                    'disksize', disksize, 
                    'used_ratio', used_ratio,
                    'layoutnumber', layoutnumber,
                    'img'] 
    newimagename = [ str(x) for x in newimagename ]
    newimagename = '.'.join( newimagename )
    dir = chpConfig.parser.get('system', 'diskimagedir') 
    path = os.path.join(dir, newimagename)
    print path
    return path

def get_disk_free_bytes(diskpath):
    stats = os.statvfs(diskpath)
    #return stats.f_bfree * stats.f_bsize
    return stats.f_bavail * stats.f_bsize

def make_one_image_solidfile(fstype, disksize, 
                      used_ratio, layoutnumber
                      ):
    """
    It uses a solid file to hold the place on disk,
    instead of using Impressions.
    """
    # make a brand new loop device, starting from 
    # making a tmpfs
    make_file_system(fstype=fstype, 
                     disksize=disksize)
    bytes_holefile = int(disksize * (1 - used_ratio))

    print 'bytes_holefile', bytes_holefile
    time.sleep(1)
    
    if fstype in ['ext4','xfs','btrfs']:
        if used_ratio > 0:
            # only do placeholder when the used_ratio > 0
            bytes_left = disksize - bytes_holefile
            print "creating place holder file... size:", bytes_left
            fallocate_solid_file(os.path.join(workmount, 'placeholder'),
                                 bytes_left)
        if layoutnumber != 6:
            # when layoutnumber==6, we do not
            # frag the file system
            bytes_left = get_disk_free_bytes(workmount)
            bytes_holefile = int(bytes_left * 0.99)
            print "creating hole file... size:", bytes_holefile, \
                    " layoutnumber:", layoutnumber
            ret = make_hole_file(os.path.join(workmount, "punchfile"),
               bytes_holefile,
               layoutnumber,
               0, True
               )

            if ret != 0:
                msg = 'it is unable to make a hole file. {} disksize: {} {} {}'.format(
                                    fstype, disksize, used_ratio, layoutnumber)
                print msg
                with open('/tmp/make_disk_image.log', 'a') as f:
                    f.write(msg + '\n')
                    f.flush()
                exit(1)

    elif fstype in ['ext2', 'ext3']:
        if used_ratio > 0:
            print "creating hole file (no hole yet)...", bytes_holefile
            fill_solid_file(os.path.join(workmount, 'punchfile'),
                                 bytes_holefile)
            bytes_left = get_disk_free_bytes(workmount)
            print "creating place holder file....", bytes_left
            fill_solid_file(os.path.join(workmount, 'placeholder'),
                                 bytes_left)           
        if layoutnumber != 6:
            if os.path.exists(os.path.join(workmount, 'punchfile')):
                print "Deleting punchfile..."
                os.remove(os.path.join(workmount, 'punchfile'))
            print "create punch file again...", bytes_holefile
            ret = make_hole_file(os.path.join(workmount,"/punchfile"),
               bytes_holefile,
               layoutnumber,
               1, True 
               )

            if ret != 0:
                msg = 'it is unable to make a hole file. {} disksize: {} {} {}'.format(
                                    fstype, disksize, used_ratio, layoutnumber)
                print msg
                with open('/tmp/make_disk_image.log', 'a') as f:
                    f.write(msg + '\n')
                    f.flush()
                exit(1)
    else:
        print 'file system is not supported with any punchmode'
        exit(1)


        
    subprocess.call(['sync'])

    # copy and save the image file
    release_image()
    newimagepath = get_image_path(fstype, disksize, 
                                  used_ratio, layoutnumber)

    dirpath = os.path.dirname(newimagepath)
    if not os.path.exists(dirpath): 
        os.makedirs(dirpath)

    cmd = ['cp', os.path.join(tmpmount, 'disk.img'), newimagepath]
    print cmd
    ret = subprocess.call(cmd)
    if ret != 0:
        print "failed to copy disk.img"
        exit(1)

def make_images():
    "for testing"
    para_dict = {
            #'fstype': ['ext4', 'xfs', 'btrfs'],
            'fstype': ['btrfs'],
            'disksize': [ x*(2**30) for x in [1]],
            'used_ratio': [ 0.4 ],
            'layoutnumber': [ 3 ]
            }
    paras = ParameterCominations(para_dict) 
    for para in paras:
        print para
        print 'finished one.............'
        time.sleep(2) 
        use_one_image(fstype=para['fstype'],
                       disksize=para['disksize'],
                       used_ratio=para['used_ratio'],
                       layoutnumber=para['layoutnumber'])
        time.sleep(2) 
        exit(0)

