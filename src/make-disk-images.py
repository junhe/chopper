import subprocess
import MWpyFS
import os
import sys
import itertools
import pprint

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

def make_disk_image():
    """
    This function will first make a file system on 
    loop device. Then, it will run Impressions on it
    to make a image. The output of Impressions and the input
    file will be saved along with the image. 

    For each image, it has these attributes:
    1. disk size
    2. file system type
    3. impression configuration
    """
    pass

def run_impressions():
    pass

def make_file_system(fstype, disksize):
    """
    fstype: ext4, xfs, btrfs
    disksize: in Bytes
    """
    if not os.path.exists("/mnt/mytmpfs"):
        print "/mnt/mytmpfs does not exist. Creating..."
        os.mkdir("/mnt/mytmpfs")
    MWpyFS.FormatFS.makeLoopDevice(
            devname="/dev/loop0",
            tmpfs_mountpoint="/mnt/mytmpfs",
            sizeMB=disksize/(1024*1024))

    print "Loop device has been made :)"

    if not os.path.exists("/mnt/scratch"):
        print "/mnt/scratch does not exist. Creating..."
        os.mkdir("/mnt/scratch")

    if fstype == 'xfs':
        MWpyFS.FormatFS.remakeXFS('/dev/loop0', 
                                  '/mnt/scratch', 
                                  'jhe', 'plfs',
                                  blocksize=4096)
    elif fstype == 'ext4':
        MWpyFS.FormatFS.remakeExt4("/dev/loop0", 
                                   "/mnt/scratch/", 
                                   "jhe", "plfs", 
                                   blockscount=disksize/4096, 
                                   blocksize=4096)
    elif fstype == 'btrfs':
        MWpyFS.FormatFS.btrfs_remake("/dev/loop0", 
                                     "/mnt/scratch/", 
                                     "jhe", "plfs", 
                                     nbytes=disksize)


#make_file_system(fstype='btrfs', disksize=256*1024*1024)
#exit(0)


def make_images():
    para_dict = {
            #'fstype': ['ext4', 'xfs', 'btrfs'],
            'fstype': ['ext4'],
            'disksize': [ x*(2**20) for x in [256, 512]],
            'used_ratio': [ x/10.0 for x in range(0,10,5) ]
            }
    pprint.pprint( ParameterCominations(para_dict) )

def main():
    make_images()
    exit()
    config_dict = {
                    'Parent_Path:': ['/mnt/scratch/', 1],
                    'FSused:': [1, 'GB'] 
                  }
    produce_new_inputfile( './impressions-v1/inputfile.orig',
                           './impressions-v1/newinputfile',
                           config_dict
                           )

if __name__ == '__main__':
    main()

