#ifndef __WorkloadFetcher_H__
#define __WorkloadFetcher_H__

#include <queue>
#include <fstream>

class WorkloadEntry {
    public:
        std::string _entry_str;
};

class WorkloadFetcher
{
    public:
        std::ifstream _workloadStream;
        std::queue <WorkloadEntry> _entryBuf;
        int _bufSize; // if _bufSize is 0, then read
                      // from file every time. 
                      // if not, read from buffer if buffer
                      // is no empty
        
        int fetchEntry(WorkloadEntry &entry);

        WorkloadFetcher(int bsize, const char *workloadfilename);
        ~WorkloadFetcher();
    private:
        int readEntryFromStream(WorkloadEntry &entry);
        int fillBuffer();
};


#endif

