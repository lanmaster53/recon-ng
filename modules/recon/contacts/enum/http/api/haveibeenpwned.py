import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'HaveIBeenPwned Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) & Tyler Halfpop (@tylerhalfpop)',
                     'Description': 'Leverages HaveIBeenPwned.com to determine if email addresses are associated with leaked credentials',
                     'Comments': [
                                  'Source options: [ db | email.address@domain.com | ./path/to/file | query <sql> ]'
                                  ]
                     }

    def module_run(self):
        accounts = self.get_source(self.options['source'], 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')

        # retrieve status
        cnt = 0
        pwned = 0
        for account in accounts:
            account = account.encode('utf-8')
            url = 'https://haveibeenpwned.com/api/breachedaccount/' + account
            resp = self.request(url)
            rcode = resp.status_code
            if rcode == 404:
                self.verbose('%s => Not Found.' % (account))
            elif rcode == 400:
                self.error('%s => Bad Request.' % (account))
                continue
            else:
                self.alert('%s => Found! Seen in the %s data dump.' % (account, resp.json[0]))
                pwned += 1
            cnt += 1
        self.output('%d/%d targets pwned.' % (pwned, cnt))
