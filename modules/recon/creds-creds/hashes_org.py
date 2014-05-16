import module
# unique to module
import xml.etree.ElementTree
import StringIO

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
        hash_groups = map(None, *(iter(hashes),) * 20)
        for group in hash_groups:
            payload = {'do': 'check'}
            group = [x for x in group if x is not None]
            for i in range(0, len(group)):
                payload['hash'+str(i+1)] = group[i]
            resp = self.request(url, payload=payload)
            tree = resp.xml
            if tree is None:
                tree = xml.etree.ElementTree.parse(StringIO.StringIO('<root>\n%s</root>\n' % (resp.raw)))
            if tree.find('request') is None:
                self.error(tree.find('error').text)
                return
            requests = tree.findall('request')
            for request in requests:
                hashstr = request.find('hash').text
                if request.find('found').text == 'true':
                    plaintext = request.find('plain').text
                    if hashstr != plaintext:
                        hashtype = request.find('type').text
                        self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                        self.query('UPDATE creds SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
                else:
                    self.verbose('Value not found for hash: %s' % (hashstr))
