import framework
import __builtin__
# unique to module
import pwnedlist
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {}
        self.info = {
                     'Name': 'PwnedList - API Statistics Viewer',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for account usage statistics.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.check_usage()

    def check_usage(self):
        # required for all PwnedList modules
        key = self.manage_key('pwned_key', 'PwnedList API Key')
        if not key: return
        secret = self.manage_key('pwned_secret', 'PwnedList API Secret')
        if not secret: return

        # setup API call
        method = 'usage.info'
        payload = {}

        # make request
        payload = pwnedlist.build_payload(payload, method, key, secret)
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        jsonstr = resp.text
        try: jsonobj = json.loads(jsonstr)
        except ValueError as e:
            self.error(e.__str__())
            return

        # handle output
        total = jsonobj['num_queries_allotted']
        left = jsonobj['num_queries_left']
        self.output('Queries allotted: %d' % (total))
        self.output('Queries remaining: %d' % (left))
        self.output('Queries used: %d' % (total - left))