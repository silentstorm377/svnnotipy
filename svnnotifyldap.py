import ldap

class SvnNotifyLDAP(object):
    def __init__(self, ldapConfig):
        self.ldapConfig = ldapConfig

    # This method sets up a connection to the ldap server
    def ldapBind(self):
        ldap.set_option(ldap.OPT_REFERRALS, 0)
        ldap.protocol_version = 3
        ldapConn = ldap.initialize(self.ldapConfig['ldap_server'])
        ldapConn.simple_bind_s(self.ldapConfig['bind_dn'], self.ldapConfig['bind_pass'])
        self.USER_BASE = self.ldapConfig['user_base']
        return ldapConn

    # Gets the LDAP distinguishedName needed in the LDAP query
    def getLdapGroupDistinguishedName(self, ldapGroup):
        retval = None
        ldapConn = self.ldapBind()
        
        filter = '(CN=%s)' %ldapGroup
        attrs = ['distinguishedName']
        resultList = ldapConn.search_s(self.USER_BASE, ldap.SCOPE_SUBTREE, str(filter), attrs)

        if resultList[0][0] is not None:
            retval = resultList[0][1]['distinguishedName'][0]

        return retval

    # This method determines if the author of the SVN commit is member of the
    # given LDAP group. An LDAP query is created using the LDAP distinguishedName of
    # the given group.
    #
    # This method returns 1 of the user is in the group, 0
    # if not. If there is any LDAP exception 0 is returned.
    def isAuthorInGroup(self, svnAuthor, ldapGroup):
        try:
            ldapConn = self.ldapBind()

            ldapGroupDistinguishedName = self.getLdapGroupDistinguishedName(ldapGroup)

            if ldapGroupDistinguishedName is None:
                return 0
            else:
                filter = '(&(sAMAccountName=%s)(memberof=%s))' %(svnAuthor, ldapGroupDistinguishedName)
                attrs = ['sn', 'SAMAccountName']

                resultList = ldapConn.search_s(self.USER_BASE, ldap.SCOPE_SUBTREE, str(filter), attrs)
                found = 0
                for dn,entry in resultList:
                    if dn is not None:
                        entry = str(entry)
                        if svnAuthor in entry:
                            found = 1

                if found == 1:
                    return 1
                else:
                    return 0
        except ldap.LDAPError, e:
                print e
                return 0

    # This method gets the full name of the author of the SVN commit.
    # If there is any LDAP exception the provided svnAuthor name is returned.
    def getAuthorRealName(self, svnAuthor):
        try:
            retval = svnAuthor
            ldapConn = self.ldapBind()

            filter = '(sAMAccountName=%s)' % svnAuthor
            attrs = ['cn', 'SAMAccountName']

            resultList = ldapConn.search_s(self.USER_BASE, ldap.SCOPE_SUBTREE, str(filter), attrs)

            for dn,entry in resultList:
                if dn is not None:
                    retval = entry['cn'][0]
                
        except ldap.LDAPError, e:
                print e
        
        return retval
    
