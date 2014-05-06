import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')
        self.info = {
                     'Name': 'Noisette MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the Noisette.ch hash database to perform a reverse hash lookup. Updates the \'creds\' table with the positive results.',
                     'Comments': [
                                  'Hash types supported: MD5'
                                  ]
                     }

    def module_run(self, hashes):
        # lookup each hash
        url = 'http://md5.noisette.ch/md5.php'
        for hashstr in hashes:
            payload = {'hash': hashstr}
            resp = self.request(url, payload=payload)
            tree = resp.xml
            elements = tree.findall('string')
            if len(elements) > 0:
                plaintext = elements[0].text
                if hashstr != plaintext:
                    hashtype = "MD5"
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                    continue
            self.verbose('Value not found for hash: %s' % (hashstr))
