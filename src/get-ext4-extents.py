import os, sys
import MWpyFS



def main():
    args = sys.argv 
    if len(args) != 5:
        print "Usage: python", args[0], \
                "mountpoint partition output-dir output-filename"
        exit(1)
    mountpoint = args[1]
    partition  = args[2]
    resultdir  = args[3]
    filename   = args[4]
    
    monitor = MWpyFS.Monitor.FSMonitor(
             partition, mountpoint, resultdir, 'ext4')

    if not os.path.exists(resultdir):
        os.makedirs(resultdir)

    ret = monitor.display(savedata=True, 
                logfile=filename,
                monitorid='used-to-separate-different-runs',
                jobid='jobid-as-you-wish'
                )

if __name__ == '__main__':
    main()

