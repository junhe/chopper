
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


#include "posix_lib.h"

#ifdef LOGGING
extern char * logfile;

int log_error(char * errmsg, int err_code, int exit_on_error)
{
	FILE * fp;
	fp = fopen(logfile,"a");
	
	if(errmsg)
	{
		fprintf(fp,"MSG -- %s\n",errmsg);
		
		if(err_code != NO_ERROR)
		{
			fprintf(fp,"Error: %s\n",strerror(err_code));
		}
	}
	fclose(fp);
	
    return 1;
}
#endif


int pos_access(const char *pathname, int mode)
{
	int ret;

	//log_error("access: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = access(pathname, mode)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to access file (path = %s)", pathname);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("access: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_chdir(const char *path)
{
	int ret;

	//log_error("chdir: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = chdir(path)) < 0) {
		char err_msg[4096];
		int err_code = errno;
		printf("\n Error: Unable to chdir (path = %s) : errcode = %d\n", path, errno);
		sprintf(err_msg, "Error: Unable to chdir (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}
	else	{ 
		printf("\n Scuccess chdir (path = %s) : errcode = %d\n", path, errno);
	//	creat("./myfile", S_IRWXU);	
	//	creat("/mnt/sba/bigdir1/bigdir4/othermyfile", S_IRWXU);	
		system("pwd");
		//system("echo 123 > /root/code/filehere");
		
	}
	//log_error("chdir: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_chmod(const char *path, mode_t mode)
{
	int ret;

	//log_error("chmod: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = chmod(path, mode)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to chmod (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("chmod: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_chown(const char *path, uid_t owner, gid_t group)
{
	int ret;

	//log_error("chown: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = chown(path, owner, group)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to chown (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("chown: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_chroot(const char *path)
{
	int ret;

	//log_error("chroot: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = chroot(path)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to chroot (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("chroot: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_creat(const char *pathname, mode_t mode)
{
	int ret;

	//log_error("creat: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = creat(pathname, mode)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to create file (path = %s mode = %d)", 
		pathname, mode);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("creat: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_stat(const char *file_name, struct stat *buf)
{
	int ret;

	//log_error("stat: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = stat(file_name, buf)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to stat file (file_name = %s)", file_name);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("stat: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_statfs(const char *path, struct statfs *buf)
{
	int ret;

	//log_error("statfs: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = statfs(path, buf)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to statfs (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("statfs: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_fsync(int fd)
{
	int ret;

	//log_error("fsync: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = fsync(fd)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to fsync file (fd = %d)", fd);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("fsync: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_truncate(const char *path, off_t length)
{
	int ret;

	//log_error("truncate: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = truncate(path, length)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to truncate (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("truncate: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

ssize_t pos_getdirentries(int fd, char *buf, size_t  nbytes, off_t *basep)
{
	int ret;

	//log_error("getdirentries: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = getdirentries(fd, buf, nbytes, basep)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to getdirentries (fd = %d)", fd);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("getdirentries: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_link(const char *oldpath, const char *newpath)
{
	int ret;

	//log_error("link: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = link(oldpath, newpath)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to create link (oldpath = %s newpath = %s)", oldpath, newpath);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("link: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_lstat(const char *file_name, struct stat *buf)
{
	int ret;

	//log_error("lstat: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = lstat(file_name, buf)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to lstat (file_name = %s)", file_name);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("lstat: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_mkdir(const char *pathname, mode_t mode)
{
	int ret;

	//log_error("mkdir: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = mkdir(pathname, mode)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to mkdir (pathname = %s)", pathname);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("mkdir: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_mount(const char *source, const char *target, const char *filesystemtype, unsigned long mountflags, const void *data)
{
	int ret_val;

	//log_error("mount: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret_val = mount(source, target, filesystemtype, mountflags, data)) != 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to mount %s in %s as %s", 
		source, target, filesystemtype);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("mount: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret_val;
}

int pos_creat_open(const char *pathname, int flags, mode_t mode)
{
	int ret;

	//log_error("creat-open: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = open(pathname, flags, mode)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to create-open file (path = %s flags = %d mode = %d)", 
		pathname, flags, mode);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("creat-open: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_open(const char *pathname, int flags)
{
	int ret;
	char err_msg[4096];

	//log_error("open: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = open(pathname, flags)) < 0) {
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to open file (path = %s flags = %d)", 
		pathname, flags);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("open: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_read(int fd, void *buf, size_t count)
{
	int ret;

	//log_error("read: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = read(fd, buf, count)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		//sprintf(err_msg, "Error: Unable to read file (fd = %d buf = %x count = %d)", \
        fd, (int )buf, count);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}
	else {
		printf("%d bytes returned in pos_read\n", ret);
	}
	//log_error("read: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_readlink(const char *path, char *buf, size_t bufsiz)
{
	int ret;

	//log_error("readlink: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = readlink(path, buf, bufsiz)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to readlink (path = %s)", path);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("readlink: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_rename(const char *oldpath, const char *newpath)
{
	int ret;

	//log_error("rename: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = rename(oldpath, newpath)) < 0) {
		char err_msg[4096];
		int err_code = errno;

	sprintf(err_msg, "Error: Unable to rename (oldpath = %s newpath = %s)", oldpath, newpath);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("rename: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_rmdir(const char *pathname)
{
	int ret;

	//log_error("rmdir: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = rmdir(pathname)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to rmdir (pathname = %s)", pathname);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("rmdir: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_symlink(const char *oldpath, const char *newpath)
{
	int ret;

	//log_error("symlink: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = symlink(oldpath, newpath)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to create symlink (oldpath = %s newpath = %s)", oldpath, newpath);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("symlink: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

void pos_sync(void)
{
	//log_error("sync: start", NO_ERROR, !(EXIT_ON_ERROR));

	sync();

	//log_error("sync: end", NO_ERROR, !(EXIT_ON_ERROR));
}

mode_t pos_umask(mode_t mask)
{
	int ret;

	//log_error("umask: start", NO_ERROR, !(EXIT_ON_ERROR));

	ret = umask(mask);

	//log_error("umask: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_unlink(const char *pathname)
{
	int ret;

	//log_error("unlink: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = unlink(pathname)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to unlink (pathname = %s)", pathname);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("unlink: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_umount(const char *target)
{
	int ret_val;

	//log_error("umount: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret_val = umount(target)) != 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to unmount %s", target);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("umount: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret_val;
}

int pos_utimes(char *filename, struct timeval *tvp)
{
	int ret;

	//log_error("utimes: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = utimes(filename, tvp)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to utimes (filename = %s)", filename);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}

	//log_error("utimes: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_write(int fd, const void *buf, size_t count)
{
	int ret;

	//log_error("write: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = write(fd, buf, count)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		//sprintf(err_msg, "Error: Unable to write file (fd = %d buf = %x count = %d)", \
        fd, (int)buf, count);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("write: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

int pos_close(int fd)
{
	int ret;

	//log_error("close: start", NO_ERROR, !(EXIT_ON_ERROR));

	if ((ret = close(fd)) < 0) {
		char err_msg[4096];
		int err_code = errno;

		sprintf(err_msg, "Error: Unable to close file (fd = %d)", fd);
		//log_error(err_msg, err_code, EXIT_ON_ERROR);
	}	

	//log_error("close: end", NO_ERROR, !(EXIT_ON_ERROR));

	return ret;
}

