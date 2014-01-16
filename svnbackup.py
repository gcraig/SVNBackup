#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Subversion Backup Script
# python is bundled with uberSVN
# georgeacraig@gmail.com
#

from datetime import date, timedelta, datetime
from subprocess import call
from time import localtime
import argparse
import ctypes
import platform
import shutil
import smtplib
import socket
import sys
import os
import re
import zipfile

####################################################

TEMP_DIR = r'tmp'
REPO_PATH = r'n:\svn'
REPO_NAME = r'repo_name'
DEPLOY_DIR = r'\\10.0.0.1\backups\svn'
EMAIL_FROM = r'svnbackup@yourcompany.com'
EMAIL_SUB = r'SVN Backup Report'
BACKUPS = 7 #Number of daily backups to keep 

####################################################

def on_error(func, path, exc_info):
    '''
    Error handler for ``shutil.rmtree``.
        If the error is due to an access error (read only file)
        it attempts to add write permission and then retries.
        If the error is for another reason it re-raises the error.
        Usage : ``shutil.rmtree(path, on_error=on_error)``
    '''
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def purge_archives():
    '''
    Remove old archives from disk, only purge oldest files if the current backup succeeded
    '''
    files = os.listdir(DEPLOY_DIR)
    # List all subversion backup files following 
    # naming convention: svn-backup-2012.02.21-15.55.33.zip
    files = [f for f in files if re.search('^svn-backup', f, re.I)]
    d = datetime.now() - timedelta(days=BACKUPS,minutes=10)
    d = d.timetuple()
    purgedfiles = 0
    newfiles = 0

    for file in files:
        filetimesecs = os.path.getmtime(DEPLOY_DIR + '/' + file)
        filetime = localtime(filetimesecs)
        # if archive is older than x days
        if filetime < d:
            purgedfiles += 1
            log_message("Purging file: %s" % file)

            try:
                os.remove(DEPLOY_DIR + '/' + file)
            except (WindowsError, OSError):
                log_message('Error removing "%s"' % file)
                log_message(str(sys.exc_info()[1]))

    log_message("Purged # of old backups: %s" % purgedfiles)
    log_message("Backups remaining: %s" % int(len(files) - purgedfiles))
    
def make_archive(fileList, archive):
    '''
    Creates a zip file (archive) of all the files in fileList.
        fileList is a list of file names - full path each name
        archive is the file name for the archive with a full path
    '''
    try:
        a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED)
        for f in fileList:
            a.write(f)
        a.close()
        return True
    except Exception, e:
        #log_message('MSG: %s\n' % str(e))
        return False
 
def dir_entries(dir_name, subdir, *args):
    '''
    Return a list of file names found in directory 'dir_name'
    If 'subdir' is True, recursively access subdirectories under 'dir_name'.
    Additional arguments, if any, are file extensions to match filenames. Matched
        file names are added to the list.
    If there are no additional arguments, all files found in the directory are
        added to the list.
    Example usage: fileList = dir_entries(r'H:\TEMP', False, 'txt', 'py')
        Only files with 'txt' and 'py' extensions will be added to the list.
    Example usage: fileList = dir_entries(r'H:\TEMP', True)
        All files and all the files in subdirectories under H:\TEMP will be added
        to the list.
    '''
    fileList = []
    for file in os.listdir(dir_name):
        dirfile = os.path.join(dir_name, file)
        if os.path.isfile(dirfile):
            if not args:
                fileList.append(dirfile)
            else:
                if os.path.splitext(dirfile)[1][1:] in args:
                    fileList.append(dirfile)
        # recursively access file names in subdirectories
        elif os.path.isdir(dirfile) and subdir:
            #print "Accessing directory:", dirfile
            fileList.extend(dir_entries(dirfile, subdir, *args))
    return fileList

def backup_repo():
    '''
    Run subversion's hotcopy backup and zip archive the repository results.
    '''
    try:
        src = REPO_PATH + '\\' + REPO_NAME
        dst = TEMP_DIR + '\\' + REPO_NAME

        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        if os.path.exists(dst):
            shutil.rmtree(dst, onerror=on_error)

        log_message('Running SVN backup on %s' % socket.gethostname())
        log_message('Local directory free space: (%s)' % get_readable(get_free_space('.')))

        #svnadmin hotcopy REPOS_PATH NEW_REPOS_PATH
        call(['svnadmin', 'hotcopy', src, dst])
        log_message('Backed-up SVN repository (via hotcopy): %s' % src)

        if os.path.exists(dst):
            now = datetime.now()
            date = '%d.%02d.%02d-%02d.%02d.%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
            zipf = 'svn-%s-backup-%s.zip' % (REPO_NAME, date)
            result = make_archive(dir_entries(dst, True), zipf)
            zipfinfo = os.stat(zipf)
            zipsize = get_readable(long(zipfinfo.st_size))
            log_message('Compressed archive: %s (%s)' % (zipf, zipsize))
			
            #if result == True: # and zipfile.is_zipfile(zipf):
            #    log_message('Compressed archive created: %s (%s)' % (zipf, zipsize))
            #else:
            #    log_message('ERROR creating archive file: %s (%s)' % (zipf, zipsize))
            
            log_message('Remote directory free space: (%s)' % get_readable(get_free_space(DEPLOY_DIR)))
            shutil.copy2(zipf, DEPLOY_DIR + "\\" + zipf)
            log_message('Archive copied to remote directory: %s' % DEPLOY_DIR)

            #cleanup
            os.remove(zipf)

            if os.path.exists(dst):
                shutil.rmtree(dst, onerror=on_error)

            log_message('Success')

    except Exception, e:
        log_message("*** ERROR backing up Subversion ***" + os.linesep + str(e))

def get_readable(size, precision=2):
    '''
    Convert long value to human readable byte string
    '''
    suffixes = ['B','KB','MB','GB','TB']
    suffixIndex = 0
    while size > 1024:
        suffixIndex += 1 #increment the index of the suffix
        size = size/1024.0 #apply the division
    return "%.2f %s"%(size,suffixes[suffixIndex])

def get_free_space(folder):
    '''
    Return folder/drive free space (in bytes)
    '''
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        return os.statvfs(folder).f_bfree

def send_email():
    '''
    Send status email of backup via gmail
    '''
    server = smtplib.SMTP('smtp.gmail.com', 587) #port 465 or 587
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('Autobuild@yourcompany.com', 'password')
    server.sendmail(EMAIL_FROM, EMAIL_TO, mailMessage)
    server.close()

def log_message(s):
    '''
    Capture output and send via email
    '''
    now = datetime.now()
    timestamp = '%02d:%02d:%02d - ' % (now.hour, now.minute, now.second)
    s = timestamp + s
    print s + os.linesep
    global mailMessage
    mailMessage = mailMessage + s + os.linesep + os.linesep

def load_config(config_file):
    global cfg
    cfg = __import__(config_file, fromlist='*')
    #todo: scrub data

if __name__ == '__main__':

    global mailMessage
    global EMAIL_TO

    f = open('svnbackup.cfg')
    EMAIL_TO = f.readlines()
    f.close()

    mailMessage = 'Subject: ' + EMAIL_SUB + os.linesep + os.linesep

    '''
    mailMessage = 'From: ' + EMAIL_FROM + os.linesep + \
    'To: ' + EMAIL_TO + os.linesep + \
    'Subject: ' + EMAIL_SUB + os.linesep + os.linesep
    '''

    if str(len(sys.argv)>1 and sys.argv[1]) == "test":
        log_message("This is a test email")
        send_email()
        sys.exit(0)

    #load_config("config.py")
    backup_repo()
    purge_archives()
    send_email()
