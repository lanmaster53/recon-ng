from recon.core.module import BaseModule
import os
import re
import json

class Module(BaseModule):

    meta = {
        'name': 'Adobe Hash Cracker',
        'author': 'Ethan Robish (@EthanRobish) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Decrypts hashes leaked from the 2013 Adobe breach. First, the module cross references the leak ID to identify Adobe hashes in the \'password\' column of the \'creds\' table, moves the Adobe hashes to the \'hash\' column, and changes the \'type\' to \'Adobe\'. Second, the module attempts to crack the hashes by comparing the ciphertext\'s decoded cipher blocks to a local block lookup table (BLOCK_DB) of known cipher block values. Finally, the module updates the \'creds\' table with the results based on the level of success.',
        'comments': (
            'Hash types supported: Adobe\'s base64 format',
            'Hash database from: http://stricture-group.com/files/adobe-top100.txt',
            'A completely padded password indicates that the exact length is known.',
        ),
        'query': 'SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL AND password IS NULL AND type IS \'Adobe\'',
        'options': (
            ('block_db', os.path.join(BaseModule.data_path, 'adobe_blocks.json'), True, 'JSON file containing known Adobe cipher blocks and plaintext'),
        ),
    }
                     
    def module_pre(self):
        adobe_leak_ids = ['26830509422781c65919cba69f45d889', 'bfc06ec52282cafa657d46b424f7e5fa']
        # move Adobe leaked hashes from the passwords column to the hashes column and set the hashtype to Adobe
        if self.options['source'] == 'default':
            self.verbose('Checking for Adobe hashes and updating the database accordingly...')
            for adobe_leak_id in adobe_leak_ids:
                self.query('UPDATE credentials SET hash=password, password=NULL, type=? WHERE hash IS NULL AND leak IS ?', ('Adobe', adobe_leak_id))

    def module_run(self, hashes):
        # create block lookup table
        with open(self.options['block_db']) as db_file:
            block_db = json.load(db_file)
        # decrypt the hashes
        for hashstr in hashes:
            # attempt to decrypt the hash using the block lookup table
            # decode the hash into a string of hex, ciphertext
            hexstr = ''.join([hex(ord(c))[2:].zfill(2) for c in hashstr.decode('base64')])
            # break up the ciphertext into 8 byte blocks
            blocks = [hexstr[i:i+16] for i in range(0, len(hexstr), 16)]
            plaintext = ''
            partial = False
            padded = False
            # reverse known cipher blocks
            for block in blocks:
                # check the block lookup table
                if block in block_db:
                    plaintext += block_db[block]
                    # flag as a partial crack
                    partial = True
                # pad the plaintext for unknown blocks
                else:
                    plaintext += '*'*8
                    # flag as padded plaintext
                    padded = True
            # output the result based on the level of success
            # partial crack
            if partial and padded:
                self.output('%s => %s' % (hashstr, plaintext))
            # full crack
            elif partial and not padded:
                self.alert('%s => %s' % (hashstr, plaintext))
            # failed crack
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))
                continue
            # add the cracked/partially cracked hash to the database
            # must reset the hashtype in order to compensate for all sources of input
            self.query('UPDATE credentials SET password=?, type=? WHERE hash=?', (plaintext, 'Adobe', hashstr))
