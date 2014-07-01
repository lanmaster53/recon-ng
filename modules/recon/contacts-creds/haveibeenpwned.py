import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
                     'Name': 'HaveIBeenPwned Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) & Tyler Halfpop (@tylerhalfpop)',
                     'Description': 'Leverages HaveIBeenPwned.com to determine if email addresses are associated with leaked credentials. Adds compromised email addresses to the \'credentials\' table.'
                     }

    def module_run(self, accounts):
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
                pwned += self.add_credentials(account)
            cnt += 1
        self.summarize(pwned, cnt)
