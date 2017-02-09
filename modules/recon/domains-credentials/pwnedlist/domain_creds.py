from recon.core.module import BaseModule
from recon.utils.crypto import aes_decrypt

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - Pwned Domain Credentials Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API to fetch all credentials for a domain. Updates the \'credentials\' table with the results.',
        'required_keys': ['pwnedlist_api', 'pwnedlist_secret', 'pwnedlist_iv'],
        'comments': (
            'API Query Cost: 10,000 queries per request, 1 query for each account returned, and 1 query per unique leak.',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        key = self.keys.get('pwnedlist_api')
        secret = self.keys.get('pwnedlist_secret')
        decrypt_key = secret[:16]
        iv = self.keys.get('pwnedlist_iv')
        # setup the API call
        url = 'https://api.pwnedlist.com/api/1/domains/query'
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'domain_identifier': domain, 'daysAgo': 0}
            while True:
                # build the payload
                pwnedlist_payload = self.build_pwnedlist_payload(payload, 'domains.query', key, secret)
                # make the request
                resp = self.request(url, payload=pwnedlist_payload)
                if resp.json: jsonobj = resp.json
                else:
                    self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                    break
                if len(jsonobj['accounts']) == 0:
                    self.output('No results returned for \'%s\'.' % (domain))
                    break
                # extract the credentials
                for cred in jsonobj['accounts']:
                    username = cred['plain']
                    password = aes_decrypt(cred['password'], decrypt_key, iv)
                    leak = cred['leak_id']
                    self.add_credentials(username=username, password=password, leak=leak)
                    self.add_leaks(mute=True, **self.get_pwnedlist_leak(leak))
                # paginate
                if jsonobj['token']:
                    payload['token'] = jsonobj['token']
                    continue
                break
