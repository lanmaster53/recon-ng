import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.info = {
                     'Name': 'PwnedList - API Usage Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for account usage statistics.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_usage()

    def check_usage(self):
        # required for all PwnedList modules
        key = self.manage_key('pwned_key', 'PwnedList API Key').encode('ascii')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret').encode('ascii')
        if not secret: return

        # setup API call
        method = 'usage.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {}
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
        total = jsonobj['num_queries_allotted']
        left = jsonobj['num_queries_left']
        self.output('Queries allotted: %d' % (total))
        self.output('Queries remaining: %d' % (left))
        self.output('Queries used: %d' % (total - left))