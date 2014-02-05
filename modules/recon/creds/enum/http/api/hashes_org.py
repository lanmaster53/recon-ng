import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hashes for module input (see \'show info\' for options)')
        self.info = {
                     'Name': 'Hashes.org Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and Mike Lisi (@MikeCodesThings)',
                     'Description': 'Uses the Hashes.org API to perform a reverse hash lookup and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | <hash> | ./path/to/file | query <sql> ]',
                                  'Hash types supported: MD5, MD4, NTLM, LM, DOUBLEMD5, TRIPLEMD5, MD5SHA1, SHA1, MYSQL5, SHA1MD5, DOUBLESHA1, RIPEMD160'
                                  ]
                     }

    def module_run(self):
        hashes = self.get_source(self.options['source'], 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')

        # lookup each hash
        url = 'https://hashes.org/api.php'
        for hashstr in hashes:
            payload = {'do': 'check', 'hash1': hashstr}
            resp = self.request(url, payload=payload)
            dom = resp.xml
            if dom.getElementsByTagName('found')[0].firstChild.data == 'true':
                plaintext = dom.getElementsByTagName('plain')[0].firstChild.data
                if hashstr != plaintext:
                    hashtype = dom.getElementsByTagName('type')[0].firstChild.data
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                    continue
            self.verbose('Value not found for hash: %s' % (hashstr))
