import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('leak_id', '0b35c0ba48a899baeea2021e245d6da8', 'yes', 'pwnedlist leak id')
        self.classify = 'passive'
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Classification': '%s Reconnaissance' % (self.classify.title()),
                     'Description': 'Queries the PwnedList API for information associated with leak IDs.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.leak_lookup()

    def leak_lookup(self):
        # api key management
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # API query guard
        if not pwnedlist.guard(1): return

        # setup API call
        method = 'leaks.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'leakId': self.options['leak_id']['value']}
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
        leak = jsonobj['leaks'][0]
        for key in leak.keys():
            header = ' '.join(key.split('_')).title()
            self.output('%s: %s' % (header, leak[key]))