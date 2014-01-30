import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.info = {
                     'Name': 'PwnedList - API Usage Statistics Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for account usage statistics.',
                     'Comments': []
                     }

    def module_run(self):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')

        # setup API call
        method = 'usage.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
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
