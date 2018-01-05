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
            'Hashes.org is a free service. Please consider a small donation to keep the service running. Thanks. - @s3inlc'
        ),
        'query': 'SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL AND password IS NULL AND type IS NOT \'Adobe\'',
    }

    def module_run(self, hashes):
        api_key = self.keys.get('hashes_api')
        url = 'https://hashes.org/api.php'
        payload = {'key':api_key}
        for hashstr in hashes:
            payload['query'] = hashstr
            # 20 requests per minute
            time.sleep(3)
            resp = self.request(url, payload=payload)
            if resp.status_code != 200:
                self.error('Unexpected service response: %d' % resp.status_code)
                break
            elif resp.json['status'] == 'error':
                self.error(resp.json['errorMessage'])
                break
            for result in resp.json['result']:
                if resp.json['result'][result]:
                    plaintext = resp.json['result'][result]['plain']
                    hashtype = resp.json['result'][result]['algorithm']
                    self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                    self.query('UPDATE credentials SET password=?, type=? WHERE hash=?', (plaintext, hashtype, hashstr))
                else:
                    self.verbose('%s => %s' % (hashstr, 'Not found.'))
