
/* Copyright notice

Copyright 2009, 2010 Nitin Agrawal
nitina@cs.wisc.edu
Developed at the University of Wisconsin-Madison.

This file is part of Impressions.

Impressions is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Impressions is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Impressions.  If not, see <http://www.gnu.org/licenses/>.

GNU General Public License in file named COPYING

*/

#include "montecarlo.h"
#include "classes.h"
#include "impress.h"

int max_dir_depth;

list<dir> LD;
list<dir>::iterator li;
list<dir>::iterator ni;

// multimap for Dirs with depth
struct ltint {
    bool operator() (const int a, const int b) const {
        return (a < b);
    }
};

multimap<int, dir> DirDepthmultimap;
multimap<int, int> Dircountfilesmmap[DEPTH_ENTRIES]; 

/* 1 for each depth; each havin FILES_PERDEPTH keys
   list<Dircountfilesmmap> LD_Dircountfilesmmap;
   list<Dircountfilesmmap>::iterator li_map;
   */

// map for Dirs with id
map<int, dir> DirIDmap;

dir *Dirs;
dir Mdir;

/* ****************************************************
    
   Functions for operations on the directory data structure 

   **************************************************** */
dir::dir () {
    id=0;
    depth=0;
    subdirs=0;
    files=0;
    created=0;
    parent=0;
}

dir::dir (int ID_a) {
    id=ID_a;
    depth=0;
    subdirs=0;
    files=0;
    created=0;
    parent=0;
}

void dir::print () {
    print_debug(1, " (Dir: %d, depth: %d, Subdirs: %d, Files: %d, Parent: %d) \n", id, depth, subdirs, files, parent);
}

int dir::increment_subdirs () {
    subdirs++;
}

void dir::setparent_depth(int my_parent, int parent_depth, char parent_path[1024]) {
    parent= my_parent;
    depth = parent_depth+1;
    sprintf( path, "%s%d/", parent_path, id);
}

ostream &operator<<(ostream &output, const dir &aaa)
{
    output << aaa.id << "\t" << aaa.depth << "\t" << aaa.subdirs << "\t" << aaa.parent << "\t"<< aaa.path <<endl;
    return output;
}

dir& dir::operator=(const dir &rhs)
{
    this->subdirs = rhs.subdirs;
    this->depth = rhs.depth;
    this->files = rhs.files;
    return *this;
}

int dir::operator==(const dir &rhs) const 
{   
    if( this->id != rhs.id) 
        return 0;
    //if( this->y != rhs.y) return 0;   
    //if( this->z != rhs.z) return 0;
    
    return 1;
}
    
// This function is required for built-in STL list functions like sort
int dir::operator<(const dir &rhs) const{
    //if( this->x == rhs.x && this->y == rhs.y && this->z < rhs.z) return 1;   
    //if( this->x == rhs.x && this->y < rhs.y) return 1;
    
    if( this->subdirs > rhs.subdirs ) 
        return 1;   
    
    return 0;
}
void dir::setroot() {    

    parent=-1;
    depth=0;    
    strcpy(path, "/");
}

void dir::setid(int id_A) {    
    id = id_A;
}

int dir::getid() {
    return id;
}
int dir::getdepth() {
    return depth;
}


/* ****************************************************
    
   Functions for operations on the directory data structure ends 

   **************************************************** */


int my_gettimeofday() {
    struct timeval st;
    gettimeofday(&st, NULL);
    return st.tv_sec*1000000 + st.tv_usec; 
}



/* ****************************************************
    
   Create a nested deep tree with numdirs total directories 

   **************************************************** */
int deep_tree(int numdirs) {


    int local_err=0;
    extern int ACTUAL_FILE_CREATION;
    if(numdirs > 1000) {
        print_debug(1, "Caution: REALLY DEEP trees may cause buffer overflows of the path buffer\n");
        return -1;
    }
    for (int i =0;i<numdirs; i++)
        Dirs[i].setid(i);
    Dirs[0].setroot();
    LD.push_front(Dirs[0]);
    li=LD.begin();

    char parent_path[5000], old_parent_path[5000],strerr[100];
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH | S_IRWXU;
    sprintf( old_parent_path, "%s",  PARENT_PATH);
    for(int i=1; i<numdirs; i++, li++) { // root is already there
        Dirs[i].setparent_depth((*li).id, (*li).depth, (*li).path);
        LD.push_back(Dirs[i]);
        sprintf( parent_path,"%s/%d", old_parent_path, i);
        if(IMP_input->Actualfilecreation==1 || IMP_input->Actualfilecreation==2){
            if((local_err = pos_mkdir(parent_path, mode)) <0) {
                strerror_r(errno, strerr, 100);
                print_debug(1, "Error: Unable to mkdir (pathname = %s %d\n", parent_path, errno);
            }
        }
        sprintf( old_parent_path,"%s",parent_path);
    }
    return 1;
}

/* ****************************************************
    
   Create a flat directory tree with numdirs total directories 
   all at level 1

   **************************************************** */
int flat_tree(int numdirs) {

    int local_err=0;
    extern int ACTUAL_FILE_CREATION;
    char parent_path[1024], strerr[100];
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH | S_IRWXU;

    for (int i =0;i<numdirs; i++)
        Dirs[i].setid(i);
    Dirs[0].setroot();
    LD.push_front(Dirs[0]);
    li = LD.begin();
    // do not increment li in this case since all parent is root
    for(int i=1; i<numdirs; i++) { // root is already there
        Dirs[i].setparent_depth((*li).id, (*li).depth, (*li).path);
        LD.push_back(Dirs[i]);
        sprintf( parent_path,"%s/%d", PARENT_PATH, i);
        if(IMP_input->Actualfilecreation==1 || IMP_input->Actualfilecreation==2){
            if((local_err = pos_mkdir(parent_path, mode)) <0) {
                strerror_r(errno, strerr, 100);
                print_debug(1, "Error: Unable to mkdir (pathname = %s %d\n", parent_path, errno);
            }
        }
    }
    return 1;
}

/* ****************************************************
    
   Run the montecarlo simulation for creating a directory 
   tree according to the generative model in Agrawal Et. Al.
   FAST 2007

   **************************************************** */
int montecarlo(int numdirs) {

    int mapdepth=0, mapid=0; 
    extern int ACTUAL_FILE_CREATION;
    int local_err=0;
    mode_t mode = S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH | S_IRWXU;
    srand(deseeder());
    int root=0; 
    long i=0, j=0;
    char parent_path[1024], strerr[100];
    int my_parent=0, parent_depth =0;
    for (i =0;i<numdirs; i++)
        Dirs[i].setid(i);

    long current_dirs=0, token=0, token_uptil_now =0, sum_childs_plus2=0;

    Dirs[0].setroot();
    DirIDmap[mapid] = Dirs[0];//Mdir;//(Dirs+sizeof(Dirs)*i);
    DirDepthmultimap.insert(pair<int, dir>(mapdepth,Dirs[0]));
    LD.push_front(Dirs[0]);
    current_dirs++;
    sum_childs_plus2+=2;

    for(i=1; i < numdirs; i++) 
    {   
        token_uptil_now =0;
        token = (rand() % sum_childs_plus2) + 1; // any one will be parent
        
        #ifdef DEBUG 
        for(li=LD.begin(), j=0; j< current_dirs; li++, j++) 
            cout << (*li).subdirs+2 << " "; 
        cout <<  "======" << endl;
        cout << "Token: " << token << " CurrentDirs " << current_dirs \
            << " sum_childs_plus2 " << sum_childs_plus2 << endl;
        #endif

        ni=LD.begin();
        token_uptil_now+= (*ni).subdirs+2;
        while(token_uptil_now < token) {
            ni++;
            token_uptil_now+= (*ni).subdirs+2; // fix this
        }
        // ni is the chosen parent
        
        #ifdef DEBUG
        cout << "Chosen parent " << (*ni).id << endl;
        #endif

        (*ni).subdirs++;
        my_parent= (*ni).id;
        parent_depth = (*ni).depth;
        strcpy(parent_path, (*ni).path);
        Dirs[i].setparent_depth((*ni).id, (*ni).depth, parent_path);

        // Add to list
        mapdepth = Dirs[i].getdepth();
        mapid = Dirs[i].getid();
        
        print_debug(0, "mapdepth: %d %d\n", mapdepth, mapid);
        
        LD.push_back(Dirs[i]);
        //DirIDmap.insert(std::pair<int, dir>((*li).id), Mdir);
        DirIDmap[mapid] = Dirs[i];//Mdir;//(Dirs+sizeof(Dirs)*i);
        DirDepthmultimap.insert(pair<int, dir>(mapdepth,Dirs[i]));

        //LD.sort();
        current_dirs++;
        sum_childs_plus2+=2+1;
        if(((*ni).depth+1) > max_dir_depth)
            max_dir_depth = (*ni).depth+1;
    }
    
    /* IMP_input->Actualfilecreation
        0: Do not create files or dir
        1: Create both
        2: Create only dir (for testing maybe)
    */
    
    if(IMP_input->Actualfilecreation==1 || IMP_input->Actualfilecreation==2){
        li = LD.begin();
        li++; // skip the root, already created
        for(; li != LD.end(); li++) {
            sprintf( parent_path,"%s/%s", PARENT_PATH, (*li).path);
            if((local_err = pos_mkdir(parent_path, mode)) <0) {
                strerror_r(errno, strerr, 100);
                print_debug(1, "Error: Unable to mkdir (pathname = %s %d\n", parent_path, errno);
            }
        }    
    }
    return 1;
}
