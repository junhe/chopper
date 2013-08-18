#ifndef __WorkloadFetcher_H__
#define __WorkloadFetcher_H__

#include <queue>
#include <fstream>

class WorkloadEntry {
    public:
        std::string _entry_str;
        std::vector<std::string> _tokens;
        pid_t       _pid;
        std::string _path;
        std::string _operation;

        void setEntry(const std::string &line);
        bool isHEAD() const;
        WorkloadEntry(){};
        WorkloadEntry(const std::string &line);
    private:
        bool setItemCache();
};

class WorkloadFetcher
{
    public:
        int fetchEntry(WorkloadEntry &entry); // only interface

        WorkloadFetcher(int bsize, const char *workloadpath);
        ~WorkloadFetcher();
    private:
        std::ifstream _workloadStream;
        std::queue <WorkloadEntry> _entryBuf;
        int _bufSize; // if _bufSize is 0, then read

        int readEntryFromStream(WorkloadEntry &entry);
        int fillBuffer();
};


#endif

