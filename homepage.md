Chopper: A File System Diagnostic Tool
====================================

Chopper is a diagnostic tool that explores file systems for unexpected behaviors. Currently, it focuses on block allocators. For more details, please read Reducing File System Tail Latencies with Chopper (http://research.cs.wisc.edu/adsl/Publications/).


### Source Code 
The source code repository is at https://github.com/junhe/chopper. You can download Chopper releases from https://github.com/junhe/chopper/releases. 

### Tutorial
We have a Chopper Tutorial at https://github.com/junhe/chopper (it is the README.md), which has the following sections:

- Quick Start
- Run Chopper in Parallel
- Understand Output
- Configure Chopper
- Create Experimental Design/Plan
- Reproduce a Subset of Experiments

### Analyzing Chopper Outputs
To make our research reproducible, we provide all the analysis codes (written in R), by which you can reproduce all the figures in the paper. You can modify the code to fit your needs. The analysis intructions are at http://research.cs.wisc.edu/adsl/Software/chopper/reproduce.html. 

### Linux ext4 Patches
We have found four issues in ext4 block allocator. The patches are at https://github.com/junhe/chopper/tree/master/ext4-patches. Use it at your own risk. 

### Bug & Questions
Please send bug reports and questions to Jun He at jhe@cs.wisc.edu. 

### Citing Chopper
```
@InProceedings{HeEtAl15-Chopper,
    title = "{Reducing File System Tail Latencies with Chopper}",
   author = "Jun He and Duy Nguyen and Andrea C. Arpaci-Dusseau and Remzi H. Arpaci-Dusseau",
booktitle = "Proceedings of the 13th USENIX Conference on File and Storage Technologies (FAST '15)",
    month = "Feb",
     year = "2015",
  address = "Santa Clara, CA",
}
```
