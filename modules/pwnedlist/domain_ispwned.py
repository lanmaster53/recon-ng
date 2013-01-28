import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for a domain to determine if any credentials from that domain have been compromised. This module does NOT return any credentials, only a total number of compromised credentials.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.domain_ispwned()

    def domain_ispwned(self):
        domain = self.options['domain']['value']

        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # API query guard
        if not pwnedlist.guard(1): return

        # setup API call
        method = 'domains.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'domain_identifier': domain}
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
            self.output('Domain \'%s\' has no publicly compromised accounts.' % (domain))
            return
        first_seen = jsonobj['first_seen']
        last_seen = jsonobj['last_seen']
        num_entries = jsonobj['num_entries']
        self.output('Domain: %s' % (domain))
        self.output('First seen: %s' % (first_seen))
        self.output('Last seen: %s' % (last_seen))
        self.alert('Pwned Accounts: %d' % (num_entries))