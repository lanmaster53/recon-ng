from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - API Usage Statistics Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API for account usage statistics.',
    }

    def module_run(self):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        # setup API call
        method = 'usage.info'
        url = 'https://api.pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json:
            jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        # handle output
        total = jsonobj['num_queries_allotted']
        left = jsonobj['num_queries_left']
        self.output('Queries allotted:  %s' % (str(total)))
        self.output('Queries remaining: %s' % (str(left)))
        self.output('Queries used:      %s' % (str(total-left)))
