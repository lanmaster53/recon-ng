from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - API Usage Statistics Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API for account usage statistics.',
        'required_keys': ['pwnedlist_api', 'pwnedlist_secret'],
    }

    def module_run(self):
        key = self.keys.get('pwnedlist_api')
        secret = self.keys.get('pwnedlist_secret')
        # setup the API call
        url = 'https://api.pwnedlist.com/api/1/usage/info'
        payload = {}
        payload = self.build_pwnedlist_payload(payload, 'usage.info', key, secret)
        # make the request
        resp = self.request(url, payload=payload)
        if resp.json:
            jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        # handle the output
        total = jsonobj['num_queries_allotted']
        left = jsonobj['num_queries_left']
        self.output('Queries allotted:  %s' % (str(total)))
        self.output('Queries remaining: %s' % (str(left)))
        self.output('Queries used:      %s' % (str(total-left)))
