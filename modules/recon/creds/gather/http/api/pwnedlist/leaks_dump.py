from framework import *
# unique to module

class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the PwnedList API for information associated with all known leaks and stores them in the database.',
                     'Comments': [
                                  'API Query Cost: 1 query per request.'
                                  ]
                     }

    def module_run(self):
        key = self.get_key('pwnedlist_api')
        secret = self.get_key('pwnedlist_secret')

        # API query guard
        if not self.api_guard(1): return

        # delete leaks table
        self.query('DROP TABLE IF EXISTS leaks')
        self.output('Old \'leaks\' table removed from the database.')

        # setup API call
        method = 'leaks.info'
        url = 'https://pwnedlist.com/api/1/%s' % (method.replace('.','/'))
        payload = {'daysAgo': 0}
        payload = self.build_pwnedlist_payload(payload, method, key, secret)
        # make request
        resp = self.request(url, payload=payload)
        if resp.json:
            jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        # add leaks table
        columns = []
        values = []
        for key in jsonobj['leaks'][0].keys():
            columns.append('\'%s\' TEXT' % (key))
        self.query('CREATE TABLE IF NOT EXISTS leaks (%s)' % (', '.join(columns)))
        self.output('New \'leaks\' table created.')

        # populate leaks table
        for leak in jsonobj['leaks']:
            self.insert('leaks', leak, leak.keys())
        self.output('%d leaks added to the \'leaks\' table.' % (len(jsonobj['leaks'])))
