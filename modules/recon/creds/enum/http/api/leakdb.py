from framework import *
# unique to module

class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hashes for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'leakdb Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the leakdb hash database to perform a reverse hash lookup and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | <hash> | ./path/to/file | query <sql> ]',
                                  'Hash types supported: MD4, MD5, MD5x2, MYSQL 3, MYSQL 4, MYSQL 5, RIPEMD160, NTLM, GOST, SHA1, SHA1x2, SHA224, SHA256, SHA384, SHA512, WHIRLPOOL'
                                  ]
                     }

    def module_run(self):
        hashes = self.get_source(self.options['source'], 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')

        # lookup each hash
        url = 'http://api.leakdb.abusix.com'
        for hashstr in hashes:
            payload = {'j': hashstr}
            resp = self.request(url, payload=payload)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (account, resp.text))
                continue
            if jsonobj['found'] == "true":
                plaintext = jsonobj['hashes'][0]["plaintext"]
                hashtype = jsonobj['type'].upper()
                self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))
