import subprocess

class SvnNotifySVNLook(object):
    def __init__(self, svnRepos, svnRevision):
        self.svnRepos = svnRepos
        self.svnRevision = str(svnRevision)
                
    # This method finds the author of the commit for the given repository and revision
    def getSvnAuthor(self):
        p = subprocess.Popen(("svnlook", "author", self.svnRepos, "-r" + self.svnRevision),
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE,
                            close_fds = False)
        svnAuthor = p.stdout.readline().strip()
        
        return svnAuthor

    # This method finds the date of the commit for the given repository and revision
    def getSvnDate(self):
        p = subprocess.Popen(("svnlook", "date", self.svnRepos, "-r" + self.svnRevision),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds = False)
        svnDate = p.stdout.readline().strip()
        
        return svnDate

    # This method finds the commit log for the given repository and revision.
    # If 'forSubject' is set to 1 the method will return the first 100 characters
    # of the first svn log line. Otherwise it will return a string with <br>
    # separating individual log lines.
    def getSvnCommitLog(self, forSubject):
        svnLog = ''
        p = subprocess.Popen(("svnlook", "log", self.svnRepos, "-r" + self.svnRevision),
                         stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         close_fds = False)
        if forSubject == 1:
            line = p.stdout.readline()
            svnLog = line[0:100]
        else:
            while True:
                line = p.stdout.readline()
                if line == '' and p.poll() != None:
                    break
                if line != '':
                    svnLog += line

            svnLog = svnLog.strip()
            svnLog = svnLog.replace('\r\n', '<BR>')
        
        return svnLog

    # This method loads the unified diff for the given repository and revision.
    # Each line is added to the 'svnDiffList' list and in the end this list is returned.
    def getSvnDiffList(self):
        svnDiffList = []
        p = subprocess.Popen(("svnlook", "diff", self.svnRepos, "-r" + self.svnRevision),
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             close_fds = False)
        while True:
            line = p.stdout.readline()
            if line == '' and p.poll() != None:
                break
            if line != '':
                svnDiffList.append(line)
        return svnDiffList

    # This method loads the changed files for the given commit.
    # The changes are categorized in 'modified', 'deleted' and 'added' files.
    # A dictionary is returend with the category keys and a list of changed files per key.
    # A special 'rootdir' key is added which can be used in the subject of the email.
    def getSvnFilesChanged(self):
        svnModifiedList = []
        svnDeletedList = []
        svnAddedList = []

        filesChanged = dict()
        
        tmpRootDirLine = ''
        p = subprocess.Popen(("svnlook", "changed", self.svnRepos, "-r" + self.svnRevision),
                             stdin = subprocess.PIPE,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             close_fds = False)
        filesChanged['all'] = []
        while True:
            line = p.stdout.readline()
            if tmpRootDirLine == '':
                tmpRootDirLine = line[1:]
            
            if line == '' and p.poll() != None:
                break
            if line != '':
                filesChanged['all'].append(line[1:])
                if line.startswith('U'):
                    svnModifiedList.append(line[1:])
                if line.startswith('A'):
                    svnAddedList.append(line[1:])
                if line.startswith('D'):
                    svnDeletedList.append(line[1:])
                
        filesChanged['modified'] = svnModifiedList
        filesChanged['deleted'] = svnDeletedList
        filesChanged['added'] = svnAddedList

        idx = tmpRootDirLine.index('/')
        filesChanged['rootdir'] = tmpRootDirLine[0:idx].strip()
        
        return filesChanged
