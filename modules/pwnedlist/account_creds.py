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
        # api key management
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
            results = self.query('SELECT DISTINCT username FROM creds WHERE username != "" and (password IS NULL or password = "") ORDER BY username')
            accounts = [x[0] for x in results]
            if len(accounts) == 0:
                self.error('No unresolved pwned accounts in the database.')
                return
        elif '@' in source: accounts = [source]
        elif os.path.exists(source): accounts = open(source).read().split()
        else:
            self.error('Invalid source: %s' % (source))
            return

        # API query guard
        ans = raw_input('This operation will use %d API queries. Do you want to continue? [Y/N]: ' % (len(accounts)))
        if ans.upper() != 'Y': return

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
                username = cred['plain']
                password = repr(pwnedlist.decrypt(cred['password'], decrypt_key, iv))[1:-1]
                breach = cred['leak_id']
                self.output('%s:%s' % (username, password))
                self.add_cred(username, password, breach)
            self.query('DELETE FROM creds WHERE username = "%s" and (password IS NULL or password = "")' % (account))