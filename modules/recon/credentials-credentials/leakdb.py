from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'leakdb Hash Lookup',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the leakdb hash database to perform a reverse hash lookup. Updates the \'credentials\' table with the positive results.',
        'comments': (
            'Hash types supported: MD4, MD5, MD5x2, MYSQL 3, MYSQL 4, MYSQL 5, RIPEMD160, NTLM, GOST, SHA1, SHA1x2, SHA224, SHA256, SHA384, SHA512, WHIRLPOOL',
        ),
        'query': 'SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL AND password IS NULL AND type IS NOT \'Adobe\'',
    }

    def module_run(self, hashes):
        # lookup each hash
        url = 'http://api.leakdb.abusix.com'
        for hashstr in hashes:
            payload = {'j': hashstr}
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if jsonobj['found'] == "true":
                plaintext = jsonobj['hashes'][0]["plaintext"]
                if hashstr != plaintext:
                    hashtype = jsonobj['type'].upper()
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE credentials SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                    continue
            self.verbose('Value not found for hash: %s' % (hashstr))
