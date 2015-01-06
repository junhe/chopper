#!/bin/bash - 

set -o nounset                              # Treat unset variables as an error

mountpoint=/mnt/scratch-sda4
#sudo umount $mountpoint
sudo mkdir $mountpoint
sudo mkfs.ext3 -b 4096 /dev/sda4 268435456 #1TB
#sudo mkfs.ext3 -b 4096 /dev/sda4 8388608 #64GB
#sudo mkfs.ext3 /dev/sda4 134217728 #512GB
#sudo mkfs.ext3 -O has_journal,extent,huge_file,flex_bg,uninit_bg,dir_nlink,extra_isize /dev/sda4 1073741824 #512GB
sudo mount /dev/sda4 $mountpoint
sudo chown -R jhe:plfs $mountpoint
sudo bash -c " echo /dev/sda4 /mnt/scratch-sda4 auto defaults 0 2 >> /etc/fstab"
