SVN Backup Scripts
==============

Backup utility scripts to perform daily backups of:

SVN
UberSVN
Jenkins

- Hotcopy or backup the above to /tmp
- Zip the contents of /tmp with datetime stamp
- Copy the contents to backup (another) server for remote backup

Eventually, an in place Grandfather-Father-Son incremental/full backup scheme, would be ideal.