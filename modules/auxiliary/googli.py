import framework
# unique to module
import os

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option(self.options, 'source', '21232f297a57a5a743894a0e4a801fc3', 'yes', 'source of module input')
        self.register_option(self.options, 'verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Goog.li Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the Goog.li hash database to perform a reverse hash lookup. This module updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: database, <hash>, <path/to/infile>',
                                  'Hash types supported: MD4, MD5, MD5x2, MYSQL 3, MYSQL 4, MYSQL 5, RIPEMD160, NTLM, GOST, SHA1, SHA1x2, SHA224, SHA256, SHA384, SHA512, WHIRLPOOL'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.googli()
    
    def googli(self):
        verbose = self.options['verbose']['value']
        
        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            hashes = [x[0] for x in self.query('SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL and password IS NULL')]
            if len(hashes) == 0:
                self.error('No hashes in the database.')
                return
        elif os.path.exists(source): hashes = open(source).read().split()
        else: hashes = [source]

        # lookup each hash
        url = 'https://goog.li'
        for hashstr in hashes:
            payload = {'j': hashstr}
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON returned from the API for \'%s\'.' % (account))
                continue
            plaintext = False
            if jsonobj['found'] == "true":
                plaintext = jsonobj['hashes'][0]["plaintext"]
                hashtype = jsonobj['type'].upper()
            if plaintext:
                self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                self.query('UPDATE creds SET password="%s", type="%s" WHERE hash="%s"' % (plaintext, hashtype, hashstr))
            else:
                if verbose: self.output('Value not found for hash: %s' % (hashstr))