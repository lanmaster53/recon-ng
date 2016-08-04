from recon.core.module import BaseModule
import time
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Have I been pwned? Breach Search',
        'author': 'Tim Tomes (@LaNMaSteR53) & Tyler Halfpop (@tylerhalfpop)',
        'description': 'Leverages the haveibeenpwned.com API to determine if email addresses are associated with breached credentials. Adds compromised email addresses to the \'credentials\' table.',
        'comments': (
            'The API is rate limited to 1 request per 1.5 seconds.',
        ),
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL',
    }

    def module_run(self, accounts):
        # retrieve status
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
                self.add_credentials(account)
            time.sleep(1.6)
