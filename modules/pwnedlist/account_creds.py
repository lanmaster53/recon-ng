import framework
import __builtin__
# unique to module
import pwnedlist
import os
import json
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'PwnedList - Account Credentials Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for the credentials of the usernames in the given source, updating the database with the results.',
                     'Comments': [
                                  'Source options: database, <email@address>, <path/to/infile>'
                                  ]
                     }

    def do_run(self, params):
        self.get_creds()

    def get_creds(self):
        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret')
        if not secret: return
        decrypt_key = secret[:16]
        iv = self.manage_key('pwned_iv', 'PwnedList Decryption IV')
        if not iv: return

        # handle sources
        source = self.options['source']
        if source == 'database':
            accounts = [x[0] for x in self.query('SELECT DISTINCT username FROM creds WHERE (username IS NOT NULL or username != "") and (password IS NULL or password = "") ORDER BY username')]
            if len(accounts) == 0:
                self.error('No unresolved pwned accounts in the database.')
                return
        elif os.path.exists(source): accounts = open(source).read().split()
        else: accounts = [source]

        # API query guard
        ans = raw_input('This operation will use %d API queries. Do you want to continue? [Y/N]: ' % (len(accounts)))
        if ans.upper() != 'Y': return

        # setup API call
        method = 'accounts.query'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))

        for account in accounts:
            # build the payload for each account
            payload = {'account_identifier': account}
            payload = pwnedlist.build_payload(payload, method, key, secret)
            # make request
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON returned from the API for \'%s\'.' % (account))
                continue
            if len(jsonobj['results']) == 0:
                self.output('No results returned for \'%s\'.' % (account))
            else:
                for cred in jsonobj['results']:
                    username = cred['plain']
                    password = pwnedlist.decrypt(cred['password'], decrypt_key, iv)
                    password = "".join([i for i in password if ord(i) in range(32, 126)])
                    #password = re.sub(r'[^\x20-\x7e]', '', password)
                    breach = cred['leak_id']
                    self.output('%s:%s' % (username, password))
                    self.add_cred(username, password, breach)
            self.query('DELETE FROM creds WHERE username = "%s" and (password IS NULL or password = "")' % (account))