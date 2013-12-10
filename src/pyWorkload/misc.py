import os
import sys
import shutil
import subprocess


def copy_boot(destdir):
    # first, copy it to a faster place
    # not using /boot /etc because I want it to be consistent
    if not os.path.exists("/tmp/boot"):
        print 'copying boot to /tmp...'
        shutil.copytree("/users/jhe/Home2/boot-etc-files/boot", "/tmp/boot", symlinks=True)
    #if not os.path.exists("/tmp/etc"):
        #print 'copying etc to /tmp...'
        #shutil.copytree("/users/jhe/Home2/boot-etc-files/etc", "/tmp/etc", symlinks=True)
    print 'copying boot to destination...'
    shutil.copytree("/tmp/boot", os.path.join(destdir, "boot"), symlinks=True)
    #print 'copying etc to destination...'
    #shutil.copytree("/tmp/etc", os.path.join(destdir, "etc"), symlinks=True)
    print 'syncing....'
    subprocess.call(['sync'])

#copy_boot("/mnt/")


