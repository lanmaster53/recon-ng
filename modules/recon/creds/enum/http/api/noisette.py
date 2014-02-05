import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hashes for module input (see \'show info\' for options)')
        self.info = {
                     'Name': 'Noisette MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the Noisette.ch hash database to perform a reverse hash lookup and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | <hash> | ./path/to/file | query <sql> ]',
                                  'Hash types supported: MD5'
                                  ]
                     }

    def module_run(self):
        hashes = self.get_source(self.options['source'], 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')

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
