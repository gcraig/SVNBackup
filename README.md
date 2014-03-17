# SVN Backup Script - svnbackup.py

Backup utility script to perform daily backups of:

SVN (via HotCopy, then compress)
UberSVN
Jenkins

- Hotcopy or backup the above to /tmp
- Zip the contents of /tmp with datetime stamp
- Copy the contents to backup (another) server for remote backup
- Uses Gmail to send status (completion/error) email

Eventually, an in place Grandfather-Father-Son incremental/full backup scheme, would be ideal.

## How to Use:

Update the values in svnbackup.py to:

```
TEMP_DIR = r'tmp'
REPO_PATH = r'n:\svn'
REPO_NAME = r'repo_name'
DEPLOY_DIR = r'\\10.0.0.1\backups\svn'
EMAIL_FROM = r'svnbackup@yourcompany.com'
EMAIL_SUB = r'SVN Backup Report'
BACKUPS = 7 # of daily backups to keep, purges older versions
```

## Run 'svnbackup.py' via a scheduler, i.e., cron.

## Enhancements:

- Separate svnbackup configuration
- Checksum verification
- Transfer/resume for remote backups. I.e., rsync.
- GUI/web interface
