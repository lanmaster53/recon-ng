import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for a domain to determine if any credentials from that domain have been compromised. This module does NOT return any credentials, only a total number of compromised credentials.',
                     'Comments': [
                                  'Source options: [ <domain> | ./path/to/file ]',
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.domain_ispwned()

    def domain_ispwned(self):
        domains = self.get_source(self.options['source']['value'])
        if not domains: return

        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # API query guard
        if not pwnedlist.guard(1*len(domains)): return

        # setup API call
        method = 'domains.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        for domain in domains:
            payload = {'domain_identifier': domain}
            payload = pwnedlist.build_payload(payload, method, key, secret)
            # make request
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON returned from the API.')
                continue

            # handle output
            if not jsonobj['domain']:
                self.output('Domain \'%s\' has no publicly compromised accounts.' % (domain))
                continue
            tdata = []
            tdata.append(('Domain', jsonobj['domain']))
            tdata.append(('First seen', jsonobj['first_seen']))
            tdata.append(('Last seen', jsonobj['last_seen']))
            tdata.append(('Pwned Accounts', str(jsonobj['num_entries'])))
            self.table(tdata)
