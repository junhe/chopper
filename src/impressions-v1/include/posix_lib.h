#ifndef __POSIX_LIB_H
#define __POSIX_LIB_H

#include "fslib.h"

int pos_access(const char *pathname, int mode);
int pos_chdir(const char *path);
int pos_chmod(const char *path, mode_t mode);
int pos_chown(const char *path, uid_t owner, gid_t group);
int pos_chroot(const char *path);
int pos_creat(const char *pathname, mode_t mode);
int pos_stat(const char *file_name, struct stat *buf);
int pos_statfs(const char *path, struct statfs *buf);
int pos_fsync(int fd);
int pos_truncate(const char *path, off_t length);
ssize_t pos_getdirentries(int fd, char *buf, size_t  nbytes, off_t *basep);
int pos_link(const char *oldpath, const char *newpath);
int pos_lstat(const char *file_name, struct stat *buf);
int pos_mkdir(const char *pathname, mode_t mode);
int pos_mount(const char *source, const char *target, const char *filesystemtype, unsigned long mountflags, const void *data);
int pos_creat_open(const char *pathname, int flags, mode_t mode);
int pos_open(const char *pathname, int flags);
int pos_read(int fd, void *buf, size_t count);
int pos_readlink(const char *path, char *buf, size_t bufsiz);
int pos_rename(const char *oldpath, const char *newpath);
int pos_rmdir(const char *pathname);
int pos_symlink(const char *oldpath, const char *newpath);
void pos_sync(void);
mode_t pos_umask(mode_t mask);
int pos_unlink(const char *pathname);
int pos_umount(const char *target);
int pos_utimes(char *filename, struct timeval *tvp);
int pos_write(int fd, const void *buf, size_t count);
int pos_close(int fd);
#endif
