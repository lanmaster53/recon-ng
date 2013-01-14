import framework
import __builtin__
# unique to module
import os
import re
from xml.dom.minidom import parseString

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': '21232f297a57a5a743894a0e4a801fc3'
                        }
        self.info = {
                     'Name': 'Noisette MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the Noisette.ch web based MD5 hash database to perform a lookup.',
                     'Comments': [
                                  'Source options: database, <hash>, <path/to/infile>',
                                  'Hash types supported: MD5'
                                  ]
                     }

    def do_run(self, params):
        self.noisette()
    
    def noisette(self):
        verbose = self.goptions['verbose']

        # handle sources
        source = self.options['source']
        if source == 'database':
            hashes = [x[0] for x in self.query('SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')]
            if len(hashes) == 0:
                self.error('No hashes in the database.')
                return
        elif os.path.exists(source): hashes = open(source).read().split()
        else: hashes = [source]

        # lookup each hash
        url = 'http://md5.noisette.ch/md5.php'
        for hashstr in hashes:
            payload = {'hash': hashstr}
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                continue
            dom = parseString(resp.text)
            plaintext = False
            hashtype = "MD5"
            nodes = dom.getElementsByTagName('string')
            if len(nodes) > 0:
                plaintext = nodes[0].firstChild.wholeText
            if plaintext:
                self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                self.query('UPDATE creds SET password="%s", type="%s" WHERE hash="%s"' % (plaintext, hashtype, hashstr))
            else:
                if verbose: self.output('Value not found for hash: %s' % (hashstr))