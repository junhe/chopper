# Chopper Tutorial

Chopper is a tool that explores the input space of file systems to find unexpected behaviors. Currently it focuses on block allocators. The input space and quality metrics are described in *Reducing File System Tail Latencies with Chopper* (http://research.cs.wisc.edu/adsl/Publications/). 

This document describes how to run Chopper on your machine. There is another document (http://research.cs.wisc.edu/adsl/Software/chopper/reproduce.html) showing how to analyze Chopper's output, which is done by showing how to reproduce all the figures in the Chopper paper. 

This document has the following sections:
- Quick Start
- Run Chopper in Parallel
- Understand Output
- Configure Chopper
- Create Experimental Design/Plan
- Reproduce a Subset of Experiments

## Quick Start
As a reference, my OS is Ubuntu 12.04 LTS with kernel 3.12.5. Chopper should work in most Linux systems. 

#### Install cmake
We use cmake for compiling C++ files. 
```bash
sudo apt-get update
sudo apt-get install -y cmake
```

#### Install MPI
We use MPI to manage multiple processes, although we don't have many processes at this moment. 

```bash
sudo apt-get install -y openmpi1.5-bin openmpi1.5-doc libopenmpi1.5-dev
```

#### Compile C++ utilities
To avoid confusion, let's define `CHOPPERDIR`.
```bash
CHOPPERDIR=/users/jhe/workdir/chopper/ #replace with your path
```

Then we can compile the C++ files in Chopper by:
```bash
cd $CHOPPERDIR
mkdir build
cd build
cmake ../
make
```
After this, the binary files will be in `build/src/`. Keep them there. Later some Python code will execute them.

#### Copy Configuration File
At this stage, you can simply copy a template file to be the configuration.
```bash
cd $CHOPPERDIR
cd conf
cp template.conf h0.conf
```
For historical reason, the config file is at the fixed path of `conf/h0.conf`. You can change the path in `src/chpConfig.py`.

In `h0.conf`, you can define the input space, change file system to be tested, and do many other things. For Quick Start, we leave it unchanged.  

#### Run Chopper
Make sure you can `sudo` because Chopper needs to make file systems. Then we do:

```bash
cd $CHOPPERDIR
cd src/
sudo python exp_executor.py --mode=batch --resultpath=result.txt
```
It will produce a result file at `$CHOPPER/src/result.txt`. 

## Run Chopper in Parallel
`exp_executor.py` is verbose and more for debugging. Instead of running Chopper sequentially with `exp_executor.py`, we can run it in parallel to speed up. 

#### Start Job Master

Chopper uses a job queue to manage the jobs. `jobmaster.py` creates such a queue. `start_worker.py` spawns worker processes that grab jobs from the queue and send back results to jobmaster, which stores the results to a file. 

To start a jobmaster:
```bash
cd $CHOPPERDIR
python jobmaster.py --jobtag=2015job --resultpath=result.txt --mode=notusefinished
```

`2015job` is an arbitary tag you use to identify this job. When you have run many experiments, you will find this useful for distinguishing them. It appears in the result file. `result.txt` is the path of the output file containing the result table. Note that the actual file will be `result.txt-2015job`. We use the tag for distinguish different jobs. `notusefinished` tells Chopper to start an experiment from scratch. `usefinished` tells Chopper to resume previousely interrupted job if there is one. 

After running the command above, the jobmaster will output the following message, indicating that it is waiting for worker. Also, it shows the progress. 

```
jhe@h0:~/workdir/chopper/src$ python jobmaster.py --resultpath=result.txt --jobtag=2015job --mode=notusefinished
Server started at port 8848
OPTION arg_usefinished: notusefinished
finished_joblist will be not used. new finished jobs will be put in it
finished_joblist []
All groups have been put into job queue
*** total groups: 4 job_total 4 resultcnt 0 at result.txt-2015job *** polled, no result this time. sleep for a while ...
*** total groups: 4 job_total 4 resultcnt 0 at result.txt-2015job *** polled, no result this time. sleep for a while ...
*** total groups: 4 job_total 4 resultcnt 0 at result.txt-2015job *** polled, no result this time. sleep for a while ...
...
```

#### Start Workers
With the jobmaster running, we now can open a new terminal and start workers:
```bash
cd $CHOPPERDIR
python start_worker.py --jobmaster=h0.try01.fsperfatscale --prefix=h --suffix=try01.fsperfatscale --np=2
```
`h0.try01.fsperfatscale` is the hostname of the jobmaster, i.e. the hostname of the machine where you run `start_jobmaster.py`.
`h` is the hostname prefix of all the worker nodes. `try01.fsperfatscale` is the suffix. `2` is the number of workers to spawn. In this example, Chopper will try to start workers on `h0.try01.fsperfatscale` and `h1.try01.fsperfatscale`. 

Note that you should **NOT** start more workers than nodes. If you do, two or more workers will run at the same node and they will try to write to the same place. Chopper will get meaningless results or simply crash.

Note that Chopper invokes OS utilities by `subprocess.call(['sudo', ...])`. That means you need to be able to do `sudo`. 

The worker will have the following output.
```
jhe@h0:~/workdir/chopper/src$ python start_worker.py --jobmaster=h0.try01.fsperfatscale --prefix=h --suffix=try01.fsperfatscale --np=2
['h0.try01.fsperfatscale', 'h1.try01.fsperfatscale']
WORKERINFO [h0.try01]: start
WORKERINFO [h0.try01]: Grabbed group 0 with 1 jobs
WORKERINFO [h1.try01]: start
WORKERINFO [h1.try01]: Grabbed group 1 with 1 jobs
WORKERINFO [h0.try01]: h0.try01 just finished 1 jobs
WORKERINFO [h0.try01]: Grabbed group 2 with 1 jobs
WORKERINFO [h1.try01]: h1.try01 just finished 1 jobs
WORKERINFO [h1.try01]: Grabbed group 3 with 1 jobs
WORKERINFO [h1.try01]: h1.try01 just finished 1 jobs
WORKERINFO [h0.try01]: h0.try01 just finished 1 jobs
WORKERINFO [h0.try01]: master is closed
WORKERINFO [h1.try01]: master is closed
WORKERINFO [h0.try01]: master is closed
WORKERINFO [h1.try01]: master is closed
```

#### Grouping Jobs
Creating disk image is the most time-consuming task in Chopper. So we always want to cache and re-use disk images. However, workers cannot re-use images cached on another machine. Therefore, we need to put jobs that using the same image to the same machine. Job grouping is for this purpose. A group is a set of jobs that is sent as a whole to worker machines. That means all jobs in a group will land on the same machine. To reuse images, we just need to put all jobs sharing the same image to the same group. 

Groups are identified by signatures. Jobs with the same signature will be placed in the same group. Signature can be set in `h0.conf`. 

Here are some sample configs. 
```
group_signature = (str(treatment)) # A group has only one job.
```

```
group_signature = (treatment['filesystem'],treatment['disksize'],treatment['disk_used'],treatment['layoutnumber']) # All jobs with the same disk image are put in the same group. 
```

## Understand Output
After Chopper finishes the job, you will see the result file at `$CHOPPERDIR/src/result.txt` (if you run Chopper with `--resultpath=result.txt`). The file contains a table with columns separated by space. 

For example, you may have:
```
sync            num.chunks      chunk.order     file.size       fullness        num.cores       fsync           num.files       layoutnumber    jobid           disk.size       file.system     disk.used       dir.span        dspan           layout_index    kernel.release  datafiles       datafiles_dspan num_extents     jobtag         
10001           5               40321           44032           1.8             2               10101           19              6               1               8589934592      ext4            0.5             19              1682546688      2449.7668998    3.12.5-031205-generic 0.file|1.file|2.file|3.file|4.file|5.file|6.file|7.file|8.file|9.file|10.file|11.file|12.file|13.file|14.file|15.file|16.file|17.file|18.file 1682538496|1682530304|1682526208|1682395136|1682407424|1682419712|1682432000|1682444288|1682456576|1682264064|1682276352|1682288640|1682300928|1682313216|1682325504|1682337792|1682350080|1682362368|1682374656 4|6|6|6|6|6|6|6|6|6|6|6|6|6|6|6|6|6|6 2015job        
01111           5               31402           125952          2.0             2               11110           13              4               0               2147483648      ext4            0.5             19              1699840         1.0574447717    3.12.5-031205-generic 0.file|1.file|2.file|3.file|4.file|5.file|6.file|7.file|8.file|9.file|10.file|11.file|12.file 1437696|1437696|1437696|126976|126976|126976|126976|126976|126976|126976|126976|126976|126976 1|1|1|1|1|1|1|1|1|1|1|1|1 2015job        
00111           5               21430           44032           2.0             2               01011           11              5               2               4294967296      ext4            0.5             19              4329472         6.65911487997   3.12.5-031205-generic 0.file|1.file|2.file|3.file|4.file|5.file|6.file|7.file|8.file|9.file|10.file 4329472|2121728|2113536|2105344|2097152|2088960|2080768|2072576|2064384|2056192|2048000 4|4|4|4|4|4|4|4|4|4|4 2015job        
00001           5               03412           93184           1.0             2               11011           12              2               3               68719476736     ext4            0.5             19              64548102144     37154.6257135   3.12.5-031205-generic 0.file|1.file|2.file|3.file|4.file|5.file|6.file|7.file|8.file|9.file|10.file|11.file 64548102144|36932898816|36932603904|36932513792|36932423680|36932333568|36932243456|36932153344|36932063232|36931973120|36931883008|36931792896 2|2|2|2|2|2|2|2|2|2|2|2 2015job
```

Each row in the table contains parameter values and resulting responses. So you can feed this table to any analysis software (R, EXCEL, Python, Matlab, etc.). 

#### dspan
Most columns are self-explanatory. Some need to be clarified. `dspan` is the overall data span of all the files written. `datafiles_dspan` contains the data span of each file. The numbers, which are separated by '|', correspond to files in `datafiles`.

For example, in `--a--b-a---b--`, suppose that `-` represents a block. Some are occupied by file `a`. Some by file `b`. This layout has overall `dspan` of 10. `dspanfiles_dspan` is `6|7`. `dspanfiles` is `file.a|file.b`.

#### layoutindex
We can imagine data sectors (512 bytes) as vertices in a path graph (http://en.wikipedia.org/wiki/Path_graph). The shortest distance between any two vertices is the corresponding distance on disk. With such a graph, we can calculate *average shortest path length* (http://en.wikipedia.org/wiki/Average_path_length). `layoutindex` is *average path length / ideal average path length*. Ideally, `layoutindex`=1, which is the smallest value possible. Larger `layoutindex` indicates worse layout. `layoutindex` measures data of all files.

Chopper paper has more discussion about `layoutindex`. Its main advantage is that it can distinguish layouts with same `dspan`.

#### num_extents
Column `num_extents` has the extent count of each file in `datafiles`. For ext4, it counts each internal extent tree node as one extent. 

## Configure Chopper
There are 3 sections in `h0.conf`: *system*, *setup*, and *space*. *system* and *setup* are for general setting. *space* is for input space setting. 

#### General Setting
The following is an example. 
```
[system]
username                      =jhe
groupname                     =FSPerfAtScale
workloaddir                   =/tmp/
mpirunpath                    =/usr/bin/mpirun
playerpath                    =../build/src/player           
makeloopdevice                =yes ;yes|no  if it is yes, make sure partition is a loop dev
partition                     =/dev/loop0
mountpoint                    =/mnt/scratch/   ; you'd better put '/' in the end since I was lazy to use os.path.join() 
tmpfs_mountpoint              =/mnt/mytmpfs
resultdir_prefix              =/mnt/resultdir/
diskimagedir                  =/mnt/diskimages/

[setup]
filesystem   = ext4    ;ext4 or xfs
mountopts    = 
design.path   = ./designs/design.sample
reproducer.path = ./designs/reproducer.sample 
# layoutnumber:(mu, sigma). mu and sigma define a lognormal distribution
layoutnumbers = {1:(0.6931472,1), 2:(1.9095425,0.775), 3:(2.442347,0.55), 4:(2.7880929,0.325), 5:(3.0445224,0.1)}
```

- **username, groupname**: They should be the current user's username and group. Chopper assigns newly created directories to the user. 
- **workloaddir**: This is where the workload description is temporarily stored. We use Python to generate workload descriptions and use a C++ program to play the descriptions. For me, it is much easier to use Python to describe workload than C/C++. 
- **mpirunpath**: the path of `mpirun`.
- **playerpath**: the path of the workload player written in C++. 
- **makeloopdevice**: whether we use a loop device. This has to be yes all the time. 
- **partition**: which disk partition the file system is mounted on. Because we use loop device, here it is `/dev/loop0`.
- **mountpoint**: where in the file system Chopper should mount the file system to be tested. 
- **tmpfs_mountpoint**: Loop device is backed by a file in tmpfs, which is mounted on `tmpfs_mountpoint`. 
- **resultdir_prefix**: this option is deprecated. It was used to store detailed layout information such as the extent trees of all files. Now those functions are disabled.
- **diskimagedir**: Chopper creates disk images and re-use them to accelerate experiments. `diskimagedir` is where Chopper caches the disk images. 
- **filesystem**: file system to be tested. ext4 and XFS are supported. btrfs is partially supported (`layoutnumber` is not implemented for btrfs. In addition, the module to get physical location of data is too complicated and I think it will break.).
- **mountopts**: options to be used when mounting.
- **design**.path: experimental design file. See Create Experimental Design for details.
- **reproducer**.path: a file describing some experiments to be reproduced in the *reproduce* mode (the `--mode` option when running `exp_executor.py`).
- **layoutnumbers**: it defines the distributions of each `layoutnumber`. Each pair of *mu* and *sigma* define a lognormal distribution. Note that `layoutnumber` 6 is reserved for 'not manually fragmented'. 
- **group_signature**: see Group Signature for details. 

#### Input Space
The input spaces of all the factors are defined in the `space` section of `h0.conf`. Each option accpets a Python list. 

This is an example:

```
[space]
disk.size    = [(2**x)*(2**30) for x in range(0, 7) ]
disk.used    = [0, 0.2, 0.4, 0.6] 
dir.span     = range(1,13) 
file.size    = [ x*1024 for x in range(8, 256+1, 8) ]
fullness     = [x/10.0 for x in range(2, 21, 2)]
num.cores    = [1,2]
num.files    = range(1,3)
layoutnumber = range(1,7)
num.chunks   = [4]
```

The contents to the right of `=` will be evaluated by `eval()` by Chopper. This allows you to use basic Python code to easily generate the spaces. 

All factors are introduced in the Chopper paper. Here we give a little more details. 

- **disk.size**: the unit is byte. You can include very large disk sizes. But that would be very slow. If you do want that, you can use *dloop*, which is a modified loop device driver implementing the idea in paper *Emulating Goliath Storage Systems with David* (http://research.cs.wisc.edu/adsl/Publications/david-fast11.pdf). dloop is available at https://github.com/junhe/dloop. It does not have any document at this moment. 
- **disk.used**: it is implemented by fallocating a file. 
- **dir.span**: The span cannot be larger than the number of directory nodes. The size of direcotry tree can be modified in `pyWorkload/exp_design.py` (look for `dir_depth`). 
- **file.size**: don't use 0 byte.
- **fullness**: Don'e use 0. I haven't tried it. Note that if both your file size and fullness are small, you have have some rounding problem (chunk size may be rounded to 0.)
- **num.cores**: it should be between 1 and the max number of cores in your system. I use `/sys/devices/system/cpu/cpu{id}/online` to enable/disable cores. So you need to first check if you have those files. If your system does not have these files, you can disable setting CPU count by removing `_set_cpu()` in `exp_executor.py`.
- **num.files**: Don't use 0. 
- **layoutnumber**: use only numbers defined in `[setup]:layoutnumbers`. 
- **num.chunks**: Currently, we only support fixed number of chunks. That means you can only have one element in the list for `num.chunks`. Allowing multiple chunks would complicate the experimental design. You may want to Google 'nested design' if you want to do that. Also, do not use large `num.chunks` at this moment. I tried `num.chunks=16` and got "out of memory". That's because Chopper naively stores the input space in memory. Having 16 chunks means have 16!=2.092279e+13 order strings and many other Sync and Fsync stored in memory. This can be improved by using a function to find the i-th item in space dynamically, instead of saving the whole space in a list.

Note that the input space's distribution does not need to be uniform. It can be any distribution you want. For example, if you want to test small file sizes more, you can have `file.size=[4KB, 5KB, 6KB, 7KB, 8KB, 1MB, 2MB]`, or any other distributions that have higher density at small sizes. 

## Create Experimental Design/Plan
Experimental design file tells Chopper which value in the input space to choose for each run. `$CHOPPERDIR/src/designs/blhd_12factors_2to14runs.txt` is such a file, which is formatted as a table. The header contains factor names. The contents are numbers between 0 and 1, which are used to pick a level in the input space of a particular factor. For example, if the input space for a factor is `[a,b,c,d]` and number in the design is `0.3`, then `b` is picked. This is because `round(4*0.3)=1` (`4` is the number of levels. The resulting `1` is the index of `b`.).

Such a design can be generated by many statistics tools, such as Matlab and R. I used R to generate the design used in the paper. The script is simple:
```r
library(lhs)
mydesign = randomLHS(n = 16384, k = 12)
write.table(mydesign, file = 'mydesignfile.txt', row.names = FALSE)
```
It saves the design to a local file `mydesignfile.txt`. You need to open the file and replace the column names with our factor names. The order does not matter. 

## Reproduce a Subset of Experiments
When you find that some experiments produce weird results, you may want to reproduce the result and trace the file system behaviors. The *reproduce* mode is for this purpose. 

#### Pick the Runs
To reproduce, first pick the runs you need in the result file (the file has columns such as `dspan`, `layoutindex`) and keep the headers. Save the contents to a text file. We have a sample file at `$CHOPPERDIR/src/designs/reproducer.sample`. The file simply has the header and some rows of the result file produced by Chopper. 

Example:
```
sync num.chunks chunk.order file.size fullness num.cores fsync num.files layoutnumber                      jobid   disk.size file.system disk.used dir.span       dspan layout_index kernel.release
1111          4        2013     57344      1.0         1  0110         2            4 3.12.5noloop.nosetaffinity 34359738368        ext4       0.4       10 10741727232    105390.56   3.12.5noloop
```

#### Set the Path
Open `h0.conf` and change `reproducer.path` to the file containing your picked runs. For example

```
reproducer.path = ./designs/reproducer.sample 
```

#### Run Chopper in Reproduce Mode
```
sudo python exp_executor.py --mode=reproduce --resultpath=reproduce.result.txt
```


