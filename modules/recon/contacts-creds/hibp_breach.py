import module
# unique to module
import urllib

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
            'Name': 'Have I been pwned? Breach Search',
            'Author': 'Tim Tomes (@LaNMaSteR53) & Tyler Halfpop (@tylerhalfpop)',
            'Description': 'Leverages the haveibeenpwned.com API to determine if email addresses are associated with breached credentials. Adds compromised email addresses to the \'credentials\' table.',
            }

    def module_run(self, accounts):
        # retrieve status
        cnt = 0
        pwned = 0
        base_url = 'https://haveibeenpwned.com/api/v2/%s/%s'
        endpoint = 'breachedaccount'
        for account in accounts:
            resp = self.request(base_url % (endpoint, urllib.quote(account)))
            rcode = resp.status_code
            if rcode == 404:
                self.verbose('%s => Not Found.' % (account))
            elif rcode == 400:
                self.error('%s => Bad Request.' % (account))
                continue
            else:
                for breach in resp.json:
                    self.alert('%s => Breach found! Seen in the %s breach that occurred on %s.' % (account, breach['Title'], breach['BreachDate']))
                pwned += self.add_credentials(account)
            cnt += 1
        self.summarize(pwned, cnt)
