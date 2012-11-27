import framework
import __builtin__
# unique to module
import pwnedlist
import os
import json
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain']
                        }
        self.info = {
                     'Name': 'PwnedList - General Domain Query',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for the given domain to determine if any credentials from that domain have been compromised. This module does NOT return any credentials, only a total number of compromised credentials belonging to the given domain.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.domain_ispwned()

    def domain_ispwned(self):
        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret')
        if not secret: return

        # API query guard
        ans = raw_input('This operation will use 1 API queries. Do you want to continue? [Y/N]: ')
        if ans.upper() != 'Y': return

        # setup API call
        method = 'domains.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'domain_identifier': self.options['domain']}
        payload = pwnedlist.build_payload(payload, method, key, secret)
        # make request
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON returned from the API.')
            return

        # handle output
        domain = jsonobj['domain']
        if not domain:
            self.output('Domain \'%s\' has no publicly compromised accounts.' % (self.options['domain']))
            return
        first_seen = jsonobj['first_seen']
        last_seen = jsonobj['last_seen']
        num_entries = jsonobj['num_entries']
        self.output('Domain: %s' % (domain))
        self.output('First seen: %s' % (first_seen))
        self.output('Last seen: %s' % (last_seen))
        self.alert('Pwned Accounts: %d' % (num_entries))