import framework
# unique to module
import hashlib
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'PwnedList Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages PwnedList.com to determine if email addresses are associated with leaked credentials and updates the \'creds\' table of the database with the positive results.',
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
            status = None
            url = 'https://www.pwnedlist.com/query'
            # hashlib will only work with ascii encoded strings
            account = account.encode('utf-8')
            payload = {'inputEmail': hashlib.sha512(account).hexdigest(), 'form.submitted': ''}
            resp = self.request(url, payload=payload, method='POST', redirect=False)
            content = resp.text
            if '<h3>Nope,' in content:
                status = 'safe'
                self.verbose('%s => %s.' % (account, status))
            elif '<h3>Yes.</h3>' in content:
                status = 'pwned'
                qty  = re.search('<li>We have found this account (\d+?) times since', content).group(1)
                last = re.search('ago, on (.+?).</li>', content).group(1)
                self.alert('%s => %s! Seen %s times as recent as %s.' % (account, status, qty, last))
                pwned += self.add_cred(account)
            else:
                self.error('%s => Response not understood.' % (account))
                continue
            cnt += 1
        self.output('%d/%d targets pwned.' % (pwned, cnt))
