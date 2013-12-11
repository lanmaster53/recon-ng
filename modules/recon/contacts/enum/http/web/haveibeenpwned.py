import framework
# unique to module
import hashlib
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'HaveIBeenPwned Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) & Tyler Halfpop (@tylerhalfpop)',
                     'Description': 'Leverages HaveIBeenPwned.com to determine if email addresses are associated with leaked credentials and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | email.address@domain.com | ./path/to/file | query <sql> ]'
                                  ]
                     }

    def module_run(self):
        accounts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')

        # retrieve status
        cnt = 0
        pwned = 0
        for account in accounts:
            status = None
            account = account.encode('utf-8')
            url = 'http://haveibeenpwned.com/api/breachedaccount/' + account
            resp = self.request(url, method='GET')
            content = resp.text
            rcode = resp.status_code
            if rcode == 404:
                status = 'safe'
                self.verbose('%s => Not Found' % (account))
            elif rcode == 400:
                self.error('%s => Bad Request' % (account))
                continue
            else:
                status = 'pwned'
                self.alert('%s => Found in %s' % (account, content))
                pwned += 1
            cnt += 1
        self.output('%d/%d targets pwned.' % (pwned, cnt))