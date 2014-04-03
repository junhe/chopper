#ifndef __FSLIB_H
#define __FSLIB_H

#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <dirent.h>
#include <sys/mman.h>
#include <sys/file.h>
#include <linux/unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <sys/mount.h>
#include <sys/vfs.h>

#define CREATE_FILE				1
#define READ_FILE				2
#define WRITE_FILE				3
#define APPEND_FILE				4
#define CREATE_DIR				5
#define READ_DIR				6
#define WRITE_DIR				7
#define MOUNT_FS				8
#define WRITE_DIR_NO_SUBDIR		9
#define UNMOUNT_FS				10

/* for llseek 
#define __USE_FILE_OFFSET64		1
#define __USE_LARGEFILE64		1
#define _FILE_OFFSET_BITS		64
#define _XOPEN_SOURCE			500
#define _LARGEFILE_SOURCE 
#define _LARGEFILE64_SOURCE
#define O_LARGEFILE				0100000
*/

#define OUT_STREAM		stderr
#define MY_BLOCK_SIZE	4096
#define ERR_SEP			"----------------------------------------------"

#define EXIT_ON_ERROR		1
#define NO_ERROR			0

/*
int vp_init_lib(char *logfile);
int vp_init_syslog();
int vp_mine_syslog();
int vp_log_error(char *err_msg, int err_code, int exit_on_err);
int vp_start_log();
int vp_dont_log();
char *vp_get_test_name(int test);
int vp_read(int fd, void *buf, size_t count);
int vp_write(int fd, const void *buf, size_t count);
int vp_open(const char *pathname, int flags);
int vp_creat_open(const char *pathname, int flags, mode_t mode);
int vp_creat(const char *pathname, mode_t mode);
int vp_close(int fd);
int vp_mkdir(const char *pathname, mode_t mode);
DIR *vp_opendir(const char *name);
struct dirent *vp_readdir(DIR *dir);
int vp_closedir(DIR *dir);
int vp_fsync(int fd);
int vp_lseek(int fildes, off_t offset, int whence);
long long vp_llseek(unsigned int fd, unsigned long long offset, unsigned int origin);
int vp_fstat(int filedes, struct stat *buf);
int vp_pthread_create(pthread_t *thread, pthread_attr_t *attr, void *(*start_routine)(void *), void *rq);
int vp_pthread_join(pthread_t th, void **thread_return);
int vp_mount(const char *source, const char *target, const char *filesystemtype, unsigned long mountflags, const void *data);
int vp_umount(const char *target);
int vp_print_err_code(int err_code, char *err_msg);
*/

double diff_time(struct timeval st, struct timeval et);
int log_start_end_msgs(int start, char *routine);
int build_block(char *buffer, int index);
int verify_block(char *buffer, int index);
int verify_dir_contents(struct dirent *dent, int index);
int mount_fs();
int unmount_fs(int argc, char *argv[]);
int create_dir(int argc, char *argv[]);
int read_dir(int argc, char *argv[]);
int write_dir(int argc, char *argv[]);
int create_file_async(int argc, char *argv[]);
int create_file(int argc, char *argv[]);
int read_file(int argc, char *argv[]);
int append_file(int argc, char *argv[]);
int write_file_async(int argc, char *argv[]);
int write_file(int argc, char *argv[]);
int stat_file(int argc, char *argv[]);

#endif
