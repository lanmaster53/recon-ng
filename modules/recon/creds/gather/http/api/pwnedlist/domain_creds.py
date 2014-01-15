import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
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

        domain = self.options['domain']

        # API query guard
        if not self.api_guard(10000): return

        # setup API call
        method = 'domains.query'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'domain_identifier': domain, 'daysAgo': 0}

        cnt = 0
        new = 0
        while True:
            # build payload
            pwnedlist_payload = self.build_pwnedlist_payload(payload, method, key, secret)
            # make request
            resp = self.request(url, payload=pwnedlist_payload)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                return
            if len(jsonobj['accounts']) == 0:
                self.output('No results returned for \'%s\'.' % (domain))
                return
            # extract creds
            for cred in jsonobj['accounts']:
                username = cred['plain']
                password = self.aes_decrypt(cred['password'], decrypt_key, iv) if cred['password'] else cred['password']
                leak = cred['leak_id']
                cnt += 1
                new += self.add_cred(username, password, None, leak)
                # clean up the password for output
                if not password: password = ''
                self.output('%s:%s' % (username, password))
            # paginate
            if jsonobj['token']:
                payload['token'] = jsonobj['token']
                continue
            break
        self.output('%d total credentials found.' % (cnt))
        if new: self.alert('%d NEW credentials found!' % (new))
