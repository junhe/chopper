#ifndef __Util_H__
#define __Util_H__

#include <vector>
#include <map>

#ifndef MAP_NOCACHE
// this is a way to tell mmap not to waste buffer cache.  since we just
// read the index files once sequentially, we don't want it polluting cache
// unfortunately, not all platforms support this (but they're small)
#define MAP_NOCACHE 0
#endif


class Util {
    public:
        static ssize_t WriteN(const void *vptr, size_t n, int fd);
        static int Open(const char *fname, int flag);
        static int Close(int fd);
        static int Flush(int fd);
        static void replaceSubStr( std::string del, 
                                   std::string newstr, 
                                   std::string &line, int startpos = 0 );
        static struct timeval Gettime();
        static double GetTimeDurAB(struct timeval a,
                                   struct timeval b);
        static off_t GetFileSize(int fd);
        static void *GetDataBuf(int fd, size_t length);
        static std::vector<std::string> GetIndexFiles(const char *dirpath);
        static std::vector<std::string> GetDirFilenames(const char *dirpath);
};

class Performance {
    public:
        std::map<std::string, std::vector<std::string> > _data;
        int _colwidth; // column width
        
        void put(const char *key, const char *val);
        void put(const char *key, int val);
        void put(const char *key, double val);
        void put(const char *key, float val);
        std::string showColumns();

        Performance(int colwidth=15);
};

void start_timer(struct timeval *start);
double end_timer_get_duration(struct timeval *start);


#endif
