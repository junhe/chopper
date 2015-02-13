Attack Scheduler Dependency
=========================

The code in this folder tries to benchmark Scheduler Dependency and see its
consequences. 

Files
-------------------------
- Makefile: it compiles all the C++ files.
- SchedDep.py: it uses the existing Chopper modules to creates workloads
  and run it on ext4. It also manages the experiments. The function names are
  self-explanatory.
- Util.cpp: some utility C++ funcitons. Its main job here is to format
  performance output.
- perform.cpp: it performs read and write on the files created by SchedDep.py
  and measures the time. 


Workload
-------------------------
The creating workload uses setaffinity() to simulate that multiple threads write the same
file. The thread migrates after writing some data of the file, which will make
ext4 to use different locality group preallocations. To achieve this effect, you
have to have multiple cores.


