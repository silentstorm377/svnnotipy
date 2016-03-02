# Installation #

You can install your script anywhere, but it is suggested to store it in 'repository'\hooks\svnnotify.

This way the script and configuration is included in SVN backups created with svnadmin hotcopy.

# Details #

To use the script you have to change the post-commit.bat to something like this:

```
set REPOS=%1
set REV=%2
'path_to_repository'\hooks\svnnotify\svnnotify.py %REPOS% %REV%
```

Change the svnnotify/config/svnnotifyconfig.xml file to meet your requirements. In this file you can set the paths you want to monitor.

In svnnotify.py you need to set your basedir to the svnnotify folder (with a trailing slash):
```
svnNotify = SvnNotify(svnRepos, svnRevision, 'D:/Repositories/svnrepos/hooks/svnnotify/')
```