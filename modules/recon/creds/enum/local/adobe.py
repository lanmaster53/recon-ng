# packages required for framework integration
import framework
# module specific packages
import re
import json

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('adobe_db', './data/adobe_top_100.json', 'yes', 'JSON file containing the Adobe hashes and passwords')
        self.register_option('source', 'db', 'yes', 'source of hashes for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Adobe Hash Lookup',
                     'Author': 'Ethan Robish (@EthanRobish)',
                     'Description': 'This module identifies Adobe hashes based on the leak id, moves them to the hash column, and changes the hash type to \'Adobe\'. It then uses a local Adobe hash database to perform a reverse hash lookup and updates the \'creds\' table with any passwords it finds.',
                     'Comments': [
                                  'Source options: [ db | <hash> | ./path/to/file | query <sql> ]',
                                  'If the source is \'db\', hashes harvested from sources other than PwnedList must be stored as type = \'Adobe\' in the database.',
                                  'Hash types supported: Adobe\'s base64 format',
                                  'Hash database from: http://stricture-group.com/files/adobe-top100.txt'
                                  ]
                     }
                     
    def module_run(self):
        adobe_leak_id = '26830509422781c65919cba69f45d889'
        hashtype = 'Adobe'
        
        # move Adobe leaked hashes from the passwords column to the hashes column and set the hashtype to Adobe
        if self.options['source'] == 'db':
            self.verbose('Checking for Adobe hashes and updating the database accordingly...')
            self.query('UPDATE creds SET hash=password, password=NULL, type=? WHERE hash IS NULL AND leak IS ?', (hashtype, adobe_leak_id,))
        
        # find all hashes of the type 'Adobe'
        query = 'SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL AND password IS NULL AND type IS \'%s\'' % (hashtype)
        hashes = self.get_source(self.options['source'], query)
        
        with open(self.options['adobe_db']) as db_file:
            adobe_db = json.load(db_file)

        # lookup each hash
        for hashstr in hashes:
            if hashstr in adobe_db:
                plaintext = adobe_db[hashstr]
                self.alert('%s => %s' % (hashstr, plaintext))
                # must reset the hashtype in order to compensate for all sources of input
                self.query('UPDATE creds SET password=?, type=? WHERE hash=?', (plaintext, hashtype, hashstr))
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))
