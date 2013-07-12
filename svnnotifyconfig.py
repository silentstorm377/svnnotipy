import xml.etree.ElementTree as ET
from svnnotifyldap import SvnNotifyLDAP

class SvnNotifyConfig(object):
    def __init__(self, baseDir):
        self.baseDir = baseDir
        self.tree = ET.parse(self.baseDir + 'config/svnnotifyconfig.xml')
        self.root = self.tree.getroot()
        
    def readAllConfigs(self):
        configs = []

        for conf in self.root.findall('RepoPathConfig'):
            config = dict()
            config['controlledPaths'] = conf.attrib.get('ControlledPaths').split(';')
            config['type'] = conf.attrib.get('Type')
            config['authorInLdapGroup'] = conf.attrib.get('AuthorInLDAPGroup')
            config['mailTo'] = conf.find('MailTo').text.split(';')
            configs.append(config)

        return configs

    def getApplicableConfigs(self, changedFiles, svnAuthor):
        configs = self.readAllConfigs()
        applicableConfigs = []

        svnNotifyLdap = SvnNotifyLDAP(self.getLdapConfig())
        for config in configs:
            # First check if the author is in the configured ldap group.
            # If this attribute is not set then skip the check.
            if config['authorInLdapGroup'] is not None:
                if svnNotifyLdap.isAuthorInGroup(svnAuthor, config['authorInLdapGroup']) == 0:
                    continue

            for path in config['controlledPaths']:
                for changedFile in changedFiles:
                    changedFile = '/' + changedFile
                    if (config['type'] == 'StartsWith' and changedFile.startswith(path)) or (config['type'] == 'Contains' and path in changedFile):
                        if applicableConfigs.count(config) == 0:
                            applicableConfigs.append(config)

        return applicableConfigs

    def getLdapConfig(self):
        ldapConfXml = self.root.find('ldap')

        ldapConfig = dict()

        ldapConfig['ldap_server'] = ldapConfXml.attrib.get('ldap_server')
        ldapConfig['bind_dn'] = ldapConfXml.attrib.get('bind_dn')
        ldapConfig['bind_pass'] = ldapConfXml.attrib.get('bind_pass')
        ldapConfig['user_base'] = ldapConfXml.attrib.get('user_base')

        return ldapConfig

    def getMailConfig(self):
        mailConfXml = self.root.find('mail')

        mailConf = dict()
        mailConf['mail_server'] = mailConfXml.attrib.get('mail_server')
        mailConf['domain_suffix'] = mailConfXml.attrib.get('domain_suffix');

        return mailConf
