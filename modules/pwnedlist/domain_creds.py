import framework
import __builtin__
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain']
                        }
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Credentials Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API to fetch the credentials for the given domain.',
                     'Comments': []
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

        # API query guard
        ans = raw_input('This operation will use 10,000 API queries, +1 query for each account. Do you want to continue? [Y/N]: ')
        if ans.upper() != 'Y': return

        # setup API call
        method = 'domains.query'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'domain_identifier': self.options['domain']}
        payload = pwnedlist.build_payload(payload, method, key, secret)
        # make request
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON returned from the API.')
            return
        if len(jsonobj['accounts']) == 0:
            self.output('No results returned for \'%s\'.' % (self.options['domain']))
        else:
            for cred in jsonobj['accounts']:
                username = cred['plain']
                password = pwnedlist.decrypt(cred['password'], decrypt_key, iv)
                password = "".join([i for i in password if ord(i) in range(32, 126)])
                breach = cred['leak_id']
                self.output('%s:%s' % (username, password))
                self.add_cred(username, password, breach)