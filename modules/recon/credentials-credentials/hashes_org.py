from recon.core.module import BaseModule
import StringIO
import time
import xml.etree.ElementTree

class Module(BaseModule):

    meta = {
        'name': 'Hashes.org Hash Lookup',
        'author': 'Tim Tomes (@LaNMaSteR53) and Mike Lisi (@MikeCodesThings)',
        'description': 'Uses the Hashes.org API to perform a reverse hash lookup. Updates the \'credentials\' table with the positive results.',
        'required_keys': ['hashes_api'],
        'comments': (
            'Hash types supported: MD5, MD4, NTLM, LM, DOUBLEMD5, TRIPLEMD5, MD5SHA1, SHA1, MYSQL5, SHA1MD5, DOUBLESHA1, RIPEMD160',
        ),
        'query': 'SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL AND password IS NULL AND type IS NOT \'Adobe\'',
    }

    def module_run(self, hashes):
        api_key = self.keys.get('hashes_api')
        url = 'https://hashes.org/api.php'
        payload = {'act':'REQUEST', 'key':api_key}
        for hashstr in hashes:
            payload['hash'] = hashstr
            # 20 requests per minute
            time.sleep(3)
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if 'ERROR' in jsonobj:
                self.verbose('%s => %s' % (hashstr, jsonobj['ERROR'].lower()))
            elif jsonobj['REQUEST'] != 'FOUND':
                self.verbose('%s => %s' % (hashstr, jsonobj['REQUEST'].lower()))
            else:
                # hashes.org converts the hash to lowercase
                plaintext = jsonobj[hashstr.lower()]['plain']
                hashtype = jsonobj[hashstr.lower()]['algorithm']
                self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                self.query('UPDATE credentials SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
