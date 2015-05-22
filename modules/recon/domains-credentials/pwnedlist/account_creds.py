from recon.core.module import BaseModule
from recon.utils.crypto import aes_decrypt

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - Account Credentials Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API for credentials associated with the given usernames. Updates the \'credentials\' table with the results.',
        'comments': (
            'API Query Cost: 1 query per request.',
        ),
        'query': 'SELECT DISTINCT username FROM credentials WHERE username IS NOT NULL and password IS NULL ORDER BY username',
    }

    def module_run(self, accounts):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        decrypt_key = secret[:16]
        iv = self.get_key('pwnedlist_iv')
        # setup API call
        method = 'accounts.query'
        url = 'https://api.pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        # build the payload
        payload = {'account_identifier': ','.join(accounts), 'daysAgo': 0}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        if len(jsonobj['results']) == 0:
            self.output('No results returned.')
        else:
            for cred in jsonobj['results']:
                username = cred['plain']
                password = aes_decrypt(cred['password'], decrypt_key, iv)
                leak = cred['leak_id']
                self.output('%s:%s' % (username, password))
                self.add_credentials(username=username, password=password, leak=leak)
                self.query('DELETE FROM credentials WHERE username = \'%s\' and password IS NULL and hash IS NULL' % (username))
