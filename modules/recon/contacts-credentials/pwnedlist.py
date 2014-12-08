import module
# unique to module
import hashlib
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
            'Name': 'PwnedList Validator',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Leverages PwnedList.com to determine if email addresses are associated with leaked credentials. Adds compromised email addresses to the \'credentials\' table.'
        }

    def module_run(self, accounts):
        for account in accounts:
            status = None
            url = 'https://www.pwnedlist.com/query'
            # hashlib will only work with ascii encoded strings
            account = account.encode('utf-8')
            payload = {'inputEmail': hashlib.sha512(account).hexdigest(), 'form.submitted': ''}
            resp = self.request(url, payload=payload, method='POST', redirect=False)
            content = resp.text
            if '<h3>Nope,' in content:
                status = 'Safe'
                self.verbose('%s => %s.' % (account, status))
            elif '<h3>Yes.</h3>' in content:
                status = 'Pwned'
                qty  = re.search('<li>We have found this account ([\w\s]*\d+) times since', content).group(1)
                last = re.search('ago, on (.+?).</li>', content).group(1)
                self.alert('%s => %s! Seen %s times, as recent as %s.' % (account, status, qty, last))
                self.add_credentials(account)
            elif '<h4>Error!</h4>' in content:
                self.error('Too many requests have been made.')
                break
            else:
                self.error('%s => Response not understood.' % (account))
                continue
