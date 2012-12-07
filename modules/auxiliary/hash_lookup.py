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
                     'Name': 'MD5 Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Attempts to identify the type of hash, then uses web based databases to perform a lookup.',
                     'Comments': [
                                  'Source options: database, <hash>, <path/to/infile>'
                                  ]
                     }

    def do_run(self, params):
        self.lookup_hash()
    
    def lookup_hash(self):
        verbose = self.goptions['verbose']

        # handle sources
        source = self.options['source']
        if source == 'database':
            hashes = [x[0] for x in self.query('SELECT DISTINCT password FROM creds WHERE password != "" or password IS NOT NULL ORDER BY password')]
            if len(hashes) == 0:
                self.error('No hashes in the database.')
                return
        elif os.path.exists(source): hashes = open(source).read().split()
        else: hashes = [source]

        # build list of valid hashes with type
        hash_sets = []
        for hash in hashes:
            type = self.hash_type(hash)
            if type:
                hash_sets.append((type, hash))
            else:
                if verbose: self.output('Type not recognized for this hash: %s' % (hash))

        # lookup each hash according to type
        for hash_set in hash_sets:
            type = hash_set[0]
            hash = hash_set[1]
            try:
                cleartext = getattr(self, type)(hash)
            except AttributeError:
                if verbose: self.output('%s (%s): No lookup available' % (hash, type))
            else:
                if cleartext:
                    self.alert('%s (%s) => %s' % (hash, type, cleartext))
                    self.query('UPDATE creds SET password="%s" WHERE password="%s"' % (cleartext, hash))
                else:
                    if verbose: self.output('Value not found for this hash: %s' % (hash))

    def hash_type(self, hash):
        algorithms = {
                      'MD5':[32],
                      'SHA1':[40],
                      'SHA224':[56],
                      'SHA256':[64],
                      'SHA384':[96],
                      'SHA512':[128]
                      }
        # will result in ValueError if not hex digits
        try: int(hash, 16)
        except ValueError: pass
        else:
            hash_len = len(hash)
            for algorithm in algorithms.keys():
                if algorithms[algorithm][0] == hash_len:
                    return algorithm
        return None

    def MD5(self, hash):
        url = 'http://md5.noisette.ch/md5.php'
        payload = {'hash': hash}
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        dom = parseString(resp.text)
        cleartext = None
        nodes = dom.getElementsByTagName('string')
        if len(nodes) > 0:
            cleartext = nodes[0].firstChild.wholeText
        return cleartext