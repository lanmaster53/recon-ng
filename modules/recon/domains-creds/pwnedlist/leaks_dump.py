import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for information associated with all known leaks. Updates the \'leaks\' table with the results.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def module_run(self):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')
        # delete leaks table
        self.output('Purging \'leaks\' table...')
        self.query('DELETE FROM leaks')
        self.output('Table data purged.')
        # setup API call
        self.output('Downloading leak data...')
        method = 'leaks.info'
        url = 'https://api.pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'daysAgo': 0}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json:
            jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return
        # populate leaks table
        self.output('Populating \'leaks\' table...')
        for leak in jsonobj['leaks']:
            normalized_leak = {}
            for item in leak:
                value = leak[item]
                if type(value) == list:
                    value = ', '.join(value)
                normalized_leak[item] = value
            self.add_leaks(**normalized_leak)
        self.output('Table populated with %d leaks.' % (len(jsonobj['leaks'])))
