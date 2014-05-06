import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')
        self.info = {
                     'Name': 'Hashes.org Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and Mike Lisi (@MikeCodesThings)',
                     'Description': 'Uses the Hashes.org API to perform a reverse hash lookup. Updates the \'creds\' table with the positive results.',
                     'Comments': [
                                  'Hash types supported: MD5, MD4, NTLM, LM, DOUBLEMD5, TRIPLEMD5, MD5SHA1, SHA1, MYSQL5, SHA1MD5, DOUBLESHA1, RIPEMD160'
                                  ]
                     }

    def module_run(self, hashes):
        # lookup each hash
        url = 'https://hashes.org/api.php'
        for hashstr in hashes:
            payload = {'do': 'check', 'hash1': hashstr}
            resp = self.request(url, payload=payload)
            tree = resp.xml
            if tree.find('found') is None:
                self.error(tree.find('error').text)
                return
            if tree.find('found').text == 'true':
                plaintext = tree.find('plain').text
                if hashstr != plaintext:
                    hashtype = tree.find('type').text
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                    continue
            self.verbose('Value not found for hash: %s' % (hashstr))
