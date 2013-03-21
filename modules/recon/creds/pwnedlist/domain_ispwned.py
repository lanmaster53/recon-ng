import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', self.goptions['domain']['value'], 'yes', 'source of domains for module input (see \'info\' for options)')
        self.register_option('store', None, 'no', 'name of database table to store the results or data will not be stored.')
        self.info = {
                     'Name': 'PwnedList - Pwned Domain Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for the given domain(s) to determine if any credentials from the domain(s) have been compromised. This module does NOT return any credentials, only a total number of compromised credentials.',
                     'Comments': [
                                  'Source options: [ <domain> | ./path/to/file ]',
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def module_run(self):
        domains = self.get_source(self.options['source']['value'])
        if not domains: return

        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # API query guard
        if not pwnedlist.guard(1*len(domains)): return

        tdata = []
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
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            jsonobj = resp.json
            # compare to None to confirm valid json as empty json is returned when domain not found
            if jsonobj is None:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (domain, resp.text))
                continue
            # check for positive response
            if not 'domain' in jsonobj:
                self.verbose('Domain \'%s\' has no publicly compromised accounts.' % (domain))
                continue
            # handle output
            self.alert('Domain \'%s\' has publicly compromised accounts!' % (domain))
            tdata.append([jsonobj['domain'], str(jsonobj['num_entries']), jsonobj['first_seen'], jsonobj['last_seen']])
        if tdata:
            tdata.insert(0, ['Domain', 'Pwned_Accounts', 'First_Seen', 'Last_Seen'])
            self.table(tdata, header=True, table=self.options['store']['value'])
