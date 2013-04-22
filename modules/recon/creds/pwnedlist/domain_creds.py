import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Credentials Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API to fetch all credentials for a domain.',
                     'Comments': [
                                  'API Query Cost: 10,000 queries per request plus 1 query for each account returned.'
                                  ]
                     }

    def module_run(self):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        decrypt_key = secret[:16]
        iv = self.get_key('pwnedlist_iv')

        domain = self.options['domain']['value']

        # API query guard
        if not self.api_guard(10000): return

        # setup API call
        method = 'domains.query'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'domain_identifier': domain, 'daysAgo': 0}
        payload = pwnedlist.build_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
            return
        if len(jsonobj['accounts']) == 0:
            self.output('No results returned for \'%s\'.' % (domain))
        else:
            for cred in jsonobj['accounts']:
                username = cred['plain']
                password = pwnedlist.decrypt(cred['password'], decrypt_key, iv)
                password = "".join([i for i in password if ord(i) in range(32, 126)])
                leak = cred['leak_id']
                self.output('%s:%s' % (username, password))
                self.add_cred(username, password, None, leak)
