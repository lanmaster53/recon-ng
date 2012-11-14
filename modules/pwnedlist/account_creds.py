import framework
import __builtin__
# unique to module
import pwnedlist
import os
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'database'
                        }
        self.info = {
                     'Name': 'PwnedList - Single Account Credentials Retriever',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for the credentials of the given username.',
                     'Comments': [
                                  'Source options: database, email@address, path/to/infile'
                                  ]
                     }

    def do_run(self, params):
        self.get_creds()

    def get_creds(self):
        # required for all PwnedList modules
        api_key = self.manage_key('pwned_key', 'PwnedList API Key')
        if not api_key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret')
        if not secret: return
        decrypt_key = secret[:16]
        iv = self.manage_key('pwned_iv', 'PwnedList Decryption IV')
        if not iv: return

        # handle sources
        source = self.options['source']
        if source == 'database':
            accounts = [x[0] for x in self.query('SELECT DISTINCT email FROM contacts WHERE email != "" and status = "pwned" ORDER BY email')]
            if len(accounts) == 0:
                self.error('No pwned accounts in the database.')
                return
        elif '@' in source: accounts = [source]
        elif os.path.exists(source): accounts = open(source).read().split()
        else:
            self.error('Invalid source: %s' % (source))
            return

        for account in accounts:
            # setup API call
            method = 'accounts.query'
            payload = {'account_identifier': account}
    
            # make request
            payload = pwnedlist.build_payload(payload, method, api_key, secret)
            url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            jsonstr = resp.text
            try: jsonobj = json.loads(jsonstr)
            except ValueError as e:
                self.error(e.__str__())
                return
            if len(jsonobj['results']) == 0:
                self.alert('No results returned for \'%s\'.' % (account))
                return

            # handle output
            for cred in jsonobj['results']:
                account = cred['plain']
                password = pwnedlist.decrypt(cred['password'], decrypt_key, iv)
                self.output('%s:%s' % (account, password))
                self.add_cred(account, password)