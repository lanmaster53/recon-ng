import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.register_option('store_table', False, 'no', 'store the results in a database table')
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for a domain to determine if any associated credentials have been compromised. This module does NOT return any credentials, only a total number of compromised credentials.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def module_run(self, domains):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        table = self.options['store_table']
        tdata = []

        # setup API call
        method = 'domains.info'
        url = 'https://api.pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        for domain in domains:
            payload = {'domain_identifier': domain}
            payload = self.build_pwnedlist_payload(payload, method, key, secret)
            # make request
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            # compare to None to confirm valid json as empty json is returned when domain not found
            if jsonobj is None:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                continue
            # check for positive response
            if not 'domain' in jsonobj:
                self.verbose('Domain \'%s\' has no publicly compromised accounts.' % (domain))
                continue
            # handle output
            self.alert('Domain \'%s\' has publicly compromised accounts!' % (domain))
            tdata.append([jsonobj['domain'], str(jsonobj['num_entries']), jsonobj['first_seen'], jsonobj['last_seen']])
        if tdata:
            header = ['Domain', 'Pwned_Accounts', 'First_Seen', 'Last_Seen']
            self.table(tdata, header=header, title='Compromised Domains', store=self.options['store_table'])
