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
                     'Comments': []
                     }

    def module_run(self):
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
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        # handle output
        total = jsonobj['num_queries_allotted']
        left = jsonobj['num_queries_left']
        tdata = []
        tdata.append(('Queries allotted', str(total)))
        tdata.append(('Queries remaining', str(left)))
        tdata.append(('Queries used', str(total-left)))
        self.table(tdata)
