from recon.core.module import BaseModule
from cookielib import CookieJar
import StringIO
import time
import xml.etree.ElementTree

class Module(BaseModule):

    meta = {
        'name': 'Hashes.org Hash Lookup',
        'author': 'Tim Tomes (@LaNMaSteR53) and Mike Lisi (@MikeCodesThings)',
        'description': 'Uses the Hashes.org API to perform a reverse hash lookup. Updates the \'credentials\' table with the positive results.',
        'comments': (
            'Hash types supported: MD5, MD4, NTLM, LM, DOUBLEMD5, TRIPLEMD5, MD5SHA1, SHA1, MYSQL5, SHA1MD5, DOUBLESHA1, RIPEMD160',
        ),
        'query': 'SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL AND password IS NULL AND type IS NOT \'Adobe\'',
    }

    cookiejar = CookieJar()

    def login(self, username, password):
        url = 'https://hashes.org/login.php'
        payload = { 'username': username, 'password': password, 'action':'action' }
        resp = self.request(url, method='POST', payload=payload, cookiejar=self.cookiejar, redirect=False)
        if resp.headers['location'] == 'index.php':
            return True
        return False

    def module_run(self, hashes):
        if not self.login(self.get_key('hashes_username'), self.get_key('hashes_password')):
            self.error('Error authenticating to hashes.org.')
            return
        url = 'https://hashes.org/api.php'
        hash_groups = map(None, *(iter(hashes),) * 20)
        for group in hash_groups:
            # 20 requests per minute
            time.sleep(3)
            # rate limit error has "data" tags
            # rate limit error does not have a "hash" element
            # rate limit error response for bulk requests consist of one request element
            # build the payload
            payload = {'do': 'check'}
            group = [x for x in group if x is not None]
            for i in range(0, len(group)):
                payload['hash'+str(i+1)] = group[i]
            resp = self.request(url, payload=payload, cookiejar=self.cookiejar)
            tree = resp.xml
            requests = tree.findall('request')
            for request in requests:
                # check for and report error conditions
                # conduct check within loop to support bulk request errors
                # None condition check required as tree elements with no children return False
                if request.find('error') is not None:
                    error = request.find('error').text
                    # continue processing valid hashes
                    if 'invalid' in error:
                        self.verbose('Unsupported type for hash: %s' % (request.find('hash').text))
                        continue
                    # any other error results in termination
                    else:
                        self.error(error)
                        return
                # analyze valid response
                hashstr = request.find('hash').text
                if request.find('found').text == 'true':
                    plaintext = request.find('plain').text
                    if hashstr != plaintext:
                        hashtype = request.find('type').text
                        self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                        self.query('UPDATE credentials SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                else:
                    self.verbose('Value not found for hash: %s' % (hashstr))
