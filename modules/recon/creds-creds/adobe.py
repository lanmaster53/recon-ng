import module
# module specific packages
import re
import json

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT hash FROM creds WHERE hash IS NOT NULL AND password IS NULL AND type IS \'Adobe\'')
        self.register_option('adobe_db', self.data_path+'adobe_top_100.json', 'yes', 'JSON file containing the Adobe hashes and passwords')
        self.info = {
                     'Name': 'Adobe Hash Lookup',
                     'Author': 'Ethan Robish (@EthanRobish)',
                     'Description': 'Identifies Adobe hashes in the \'creds\' table by cross referencing the leak ID, moves the Adobe hashes to the hash column, changes the hash type to \'Adobe\', and uses a local Adobe hash database to perform a reverse hash lookup. Updates the \'creds\' table with the positive results.',
                     'Comments': [
                                  'Hash types supported: Adobe\'s base64 format',
                                  'Hash database from: http://stricture-group.com/files/adobe-top100.txt'
                                  ]
                     }
                     
    def module_pre(self):
        adobe_leak_id = '26830509422781c65919cba69f45d889'
        hashtype = 'Adobe'
        # move Adobe leaked hashes from the passwords column to the hashes column and set the hashtype to Adobe
        if self.options['source'] == 'default':
            self.verbose('Checking for Adobe hashes and updating the database accordingly...')
            self.query('UPDATE creds SET hash=password, password=NULL, type=? WHERE hash IS NULL AND leak IS ?', (hashtype, adobe_leak_id,))
        return hashtype

    def module_run(self, hashes, hashtype):
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
