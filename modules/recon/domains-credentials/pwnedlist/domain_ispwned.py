from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - Pwned Domain Statistics Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API for a domain to determine if any associated credentials have been compromised. This module does NOT return any credentials, only a total number of compromised credentials.',
        'required_keys': ['pwnedlist_api', 'pwnedlist_secret'],
        'comments': (
            'API Query Cost: 1 query per request.',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        key = self.keys.get('pwnedlist_api')
        secret = self.keys.get('pwnedlist_secret')
        tdata = []
        # setup the API call
        url = 'https://api.pwnedlist.com/api/1/domains/info'
        for domain in domains:
            payload = {'domain_identifier': domain}
            payload = self.build_pwnedlist_payload(payload, 'domains.info', key, secret)
            # make the request
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            # compare to None to confirm valid json as empty json is returned when domain not found
            if jsonobj is None:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                continue
            # check for a positive response
            if not jsonobj['num_entries']:
                self.verbose('Domain \'%s\' has no publicly compromised accounts.' % (domain))
                continue
            # handle the output
            self.alert('Domain \'%s\' has publicly compromised accounts!' % (domain))
            tdata.append([jsonobj['domain'], str(jsonobj['num_entries']), jsonobj['first_seen'], jsonobj['last_seen']])
        if tdata:
            header = ['Domain', 'Pwned_Accounts', 'First_Seen', 'Last_Seen']
            self.table(tdata, header=header, title='Compromised Domains')
