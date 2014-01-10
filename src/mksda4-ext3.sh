#!/bin/bash - 

set -o nounset                              # Treat unset variables as an error

mountpoint=/mnt/scratch-sda4
sudo mkdir $mountpoint
sudo mkfs.ext3 /dev/sda4 8388608
sudo mount /dev/sda4 $mountpoint

