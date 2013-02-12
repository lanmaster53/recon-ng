import framework
# unique to module
import re
from xml.dom.minidom import parseString

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', '21232f297a57a5a743894a0e4a801fc3', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'support'
        self.info = {
                     'Name': 'Noisette MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the Noisette.ch hash database to perform a reverse hash lookup. This module updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: db, <hash>, <path/to/infile>',
                                  'Hash types supported: MD5'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.noisette()
    
    def noisette(self):
        verbose = self.options['verbose']['value']
        
        hashes = self.get_source(self.options['source']['value'], 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')
        if not hashes: return

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