#include <stdlib.h>
#include <stdio.h>

#ifndef CLASS_DIR
#define CLASS_DIR

using namespace std;
class dir {

    friend ostream &operator<<(ostream &, const dir &);
    //private:
    public:
    int id;
    int depth;
    int subdirs;
    int files;
    int created;
    int parent;
    char path[1024];

    dir();
    dir(int);
    void print();
    void setroot();
    void setparent_depth(int, int, char path[1024]);
    void setid(int);
    int increment_subdirs();
    ~dir(){};
    dir &operator=(const dir &rhs);
    int operator==(const dir &rhs) const;
    int operator<(const dir &rhs) const;
    int getdepth();
    int getid();
};
#endif
