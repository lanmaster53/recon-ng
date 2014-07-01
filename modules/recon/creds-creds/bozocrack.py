import module
# unique to module
import hashlib
import random
import time

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT hash FROM credentials WHERE hash IS NOT NULL and password IS NULL')
        self.info = {
                     'Name': 'PyBozoCrack Hash Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Google for the value of a hash and tests for a match by hashing every word in the resulting page using all hashing algorithms supported by the \'hashlib\' library. Updates the \'credentials\' table with the positive results.',
                     'Comments': [
                                  'Inspired by the PyBozoCrack script: https://github.com/ikkebr/PyBozoCrack'
                                  ]
                     }

    def module_run(self, hashes):
        url = 'http://www.google.com/search'
        for hashstr in hashes:
            payload = {'q': hashstr}
            resp = self.request(url, payload=payload, redirect=False)
            if resp.status_code != 200:
                if resp.status_code == 302:
                    self.error('You\'ve been temporarily banned by Google for violating the terms of service.')
                else:
                    self.error('Google has encountered an error.')
                break
            #re.sub('[\.:?]', ' ', resp.text).split()
            wordlist = set(resp.raw.replace('.', ' ').replace(':', ' ').replace('?', '').split(' '))
            plaintext, hashtype = crack(hashstr, wordlist)
            if plaintext:
                self.alert('%s (%s) => %s' % (hashstr, hashtype, plaintext))
                self.query('UPDATE credentials SET password=\'%s\', type=\'%s\' WHERE hash=\'%s\'' % (plaintext, hashtype, hashstr))
            else:
                self.verbose('Value not found for hash: %s' % (hashstr))
            # sleep to avoid lock-out
            time.sleep(random.randint(3,5))

def crack(hashstr, wordlist):
    for word in wordlist:
        for hashtype in hashlib.algorithms:
            func = getattr(hashlib, hashtype)
            if func(word).hexdigest() == hashstr:
                return word, hashtype
    return None, None
