import subprocess
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from svnnotipyldap import SvnNotipyLDAP
from svnnotipysvnlook import SvnNotipySVNLook
from svnnotipyconfig import SvnNotipyConfig
from string import Template

class SvnNotipy(object):
    def __init__(self, svnRepos, svnRevision, baseDir):
        self.svnRepos = svnRepos
        self.svnRevision = str(svnRevision)
        self.baseDir = baseDir
        self.initConfig()

    # This method builds the list of files that are changed
    # in the given revision. It loops over the svnFilesChanged
    # result and Per type (added, modified, deleted) a
    # separate list (<ul><li>) is created. A simple template
    # is used to minimize HTML code in this script.
    def buildHTMLChanged(self):
        svnModifiedList = self.svnFilesChanged['modified']
        svnAddedList = self.svnFilesChanged['added']
        svnDeletedList = self.svnFilesChanged['deleted']

        templateRaw = open(self.baseDir + 'template/fileschangedlist.html', 'r').read()
        template = Template(templateRaw)
        mapping = dict()

        if len(svnAddedList) > 0:
            mapping['changedType'] = 'Added'

            changedItems = ''
            for mod in svnAddedList:
                changedItems += '<li>%s</li>\r\n' %mod.strip()
            mapping['changedItems'] = changedItems
            self.svnAddedHtml = template.substitute(mapping)
            
        if len(svnModifiedList) > 0:
            mapping['changedType'] = 'Modified'
            changedItems = ''
            for mod in svnModifiedList:
                changedItems += '<li>%s</li>\r\n' %mod.strip()
            mapping['changedItems'] = changedItems
            self.svnModifiedHtml = template.substitute(mapping)

        if len(svnDeletedList) > 0:
            mapping['changedType'] = 'Deleted'
            changedItems = ''
            for mod in svnDeletedList:
                changedItems += '<li>%s</li>\r\n' %mod.strip()
            mapping['changedItems'] = changedItems
            self.svnDeletedHtml = template.substitute(mapping)   

    # This method builds a block which shows the unified diff for a
    # changed file. The given 'index' is the start of the diff. The
    # method detects if a line has been deleted or added and depending
    # on this different formatting is used to make the diff more user
    # friendly.
    #
    # When the end of a unified diff is detected the 'leaveIndex' is
    # set. This is used by the caller to determine where to continue
    # to look for the unified diff of the next modified file.
    def buildHTMLDiffBlock(self, index):
        diffBlock = {}
        diffBlock['leaveIndex'] = -1
        diffBlockHtml = '<div class=modfile>\r\n'
        diffBlockHtml += '<h4>%s</h4>\r\n' %self.svnDiffList[index].strip()
        
        i = index + 1
        
        diffLines = []
        
        while i < len(self.svnDiffList):
            diffLine = self.svnDiffList[i]
            if diffLine.startswith('---'):
                diffBlockHtml += '<pre class=diff>'
                diffBlockHtml += '<span class=info>%s<br/>%s</span>' %(diffLine.strip(), self.svnDiffList[i + 1].strip())
                i += 1
            elif diffLine.startswith('@@'):
                diffLines.append('\r\n<span class=lines>%s</span>\r\n' %diffLine.strip())
            elif diffLine.startswith('+'):
                diffLines.append('<ins>%s</ins>\r\n' %diffLine.strip())
            elif diffLine.startswith('-'):
                diffLines.append('<del>%s</del>\r\n' %diffLine.strip())
            elif diffLine.startswith(' ') or len(diffLine.strip()) == 0:
                None
            elif 'No newline at end' in diffLine:
                None
            elif diffLine.startswith('=='):
                i += 1
                continue
            else:
                # Set the leave index, this is the index where the main loop will continue to process
                diffBlock['leaveIndex'] = i
                break
            i += 1
        # If the leaveindex is not yet set, set it now to the last value of i
        if diffBlock['leaveIndex'] == -1:
            diffBlock['leaveIndex'] = i
        
        diffBlockHtml += '<span>'
        
        for tmpDiffLine in diffLines:
            diffBlockHtml += tmpDiffLine
        
        diffBlockHtml += '</span></pre></div><a href=#pagetop class=toplink>Return to Top</a>'
            
        diffBlockHtml = diffBlockHtml.replace('</del><del>', '\r\n')
        diffBlockHtml = diffBlockHtml.replace('</ins><ins>', '\r\n')
        diffBlockHtml = diffBlockHtml.replace('<span class=cx><span>', '')
        
        diffBlock['html'] = diffBlockHtml
        
        return diffBlock

    # This method is the starting point for building the unified diff output.
    # It loops over all lines of the svnlook diff output (stored in svnDiffList).
    # If it detects a line starting with 'Modified', 'Added', or 'Deleted' it
    # passes the control to the buildHTMLDiffBlock method which will format
    # all the details of that block. A block represents the unified diff for a
    # specific file.
    #
    # The buildHTMLDiffBlock returns a dictionary with two fields: 'html' and
    # 'leaveIndex'. The 'html' field contains the user-friendly formatted
    # unified diff for the modified file. The 'leaveIndex' indicates at what
    # line the unified diff ended for the previous modified file. At this index
    # the method will continue to look for other files included in the diff.
    def buildHTMLDiff(self):
        diffHtml = ''
        
        i = 0
        while i < len(self.svnDiffList):
            diffLine = self.svnDiffList[i]
            
            if diffLine.startswith('Modified') or diffLine.startswith('Added') or diffLine.startswith('Deleted'):
                diffBlock = self.buildHTMLDiffBlock(i)
                diffHtml += diffBlock['html']
                i = diffBlock['leaveIndex']
            else:
                i += 1
        
        return diffHtml

    # Builds the HTML output using a template and some css
    def buildHTML(self):
        mapping = dict()
        mapping['svnAuthor'] = self.svnAuthor
        mapping['svnAuthorRealName'] = self.svnAuthorRealName
        mapping['svnDate'] = self.svnDate
        mapping['svnRevision'] = self.svnRevision
        css = open(self.baseDir + 'template/svnnotipy.css', 'r').read()
        mapping['css'] = css
        mapping['svnLog'] = self.svnLog

        self.buildHTMLChanged()
        mapping['svnAddedHtml'] = self.svnAddedHtml
        mapping['svnModifiedHtml'] = self.svnModifiedHtml
        mapping['svnDeletedHtml'] = self.svnDeletedHtml

        mapping['svnDiff'] = self.buildHTMLDiff()
        
        templateRaw = open(self.baseDir + 'template/general.html', 'r').read()
        template = Template(templateRaw)
        html = template.substitute(mapping)
        
        return html
        
    # This method sends an HTML formatted email containing the details of
    # the svn commit.
    def sendMail(self, mailTo):
        html = self.buildHTML()

        mailConfig = self.svnNotipyConfig.getMailConfig()
        svnAuthorEmail = self.svnAuthor + mailConfig['domain_suffix']
        
        msg = MIMEMultipart()
        msg['From'] = '%s <%s>' %(self.svnAuthorRealName, svnAuthorEmail)
        msg['To'] = ', '.join(mailTo)
        msg['Subject'] = '[SVN] /%s %s' %(self.svnRootDir, self.svnLogForSubject)
        
        body = MIMEText(html, 'html')
        msg.attach(body)
        
        s = smtplib.SMTP(mailConfig['mail_server'])
        s.sendmail(msg['From'], mailTo, msg.as_string())
        s.quit()

    def initConfig(self):
        svnNotipySvnLook = SvnNotipySVNLook(self.svnRepos, self.svnRevision)
        self.svnNotipyConfig = SvnNotipyConfig(self.baseDir)
        svnNotipyLdap = SvnNotipyLDAP(self.svnNotipyConfig.getLdapConfig())
        
        self.svnAuthor = svnNotipySvnLook.getSvnAuthor()
        self.svnDate = svnNotipySvnLook.getSvnDate()
        self.svnLog = svnNotipySvnLook.getSvnCommitLog(0)
        self.svnLogForSubject = svnNotipySvnLook.getSvnCommitLog(1)
        self.svnDiffList = svnNotipySvnLook.getSvnDiffList()
        self.svnFilesChanged = svnNotipySvnLook.getSvnFilesChanged()
        self.svnRootDir = self.svnFilesChanged['rootdir']
        self.svnAuthorRealName = svnNotipyLdap.getAuthorRealName(self.svnAuthor)

        self.svnAddedHtml = ''
        self.svnModifiedHtml = ''
        self.svnDeletedHtml = ''
        
    def doNotipy(self):
        # load the configurations and determine if an email should be sent and to who
        mailTo = []
        for config in self.svnNotipyConfig.getApplicableConfigs(self.svnFilesChanged['all'], self.svnAuthor):
            # Create a list of unique emailaddresses. This avoids sending multiple emails to the same recipient
            mailTo = list(set(mailTo + config['mailTo']))

        if(len(mailTo) > 0):
                self.sendMail(mailTo)
#########################################
svnRepos = sys.argv[1]
svnRevision = sys.argv[2]

svnNotipy = SvnNotipy(svnRepos, svnRevision, 'D:/Repositories/svnrepos/hooks/svnnotipy/')
svnNotipy.doNotipy()


