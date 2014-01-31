import module
# unique to module
import time

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('username', None, 'yes', 'jigsaw account username')
        self.register_option('password', None, 'yes', 'jigsaw account password')
        self.register_option('contact', None, 'yes', 'jigsaw contact id')
        self.info = {
                     'Name': 'Jigsaw - Single Contact Retriever',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Retrieves a single complete contact from the Jigsaw.com API using points from the given account.',
                     'Comments': [
                                  'Account Point Cost: 5 points per request.',
                                  'This module is typically used to validate email address naming conventions and gather alternative social engineering information.'
                                  ]
                     }

    def module_run(self):
        username = self.options['username']
        password = self.options['password']
        key = self.get_key('jigsaw_api')

        # point guard
        if not self.api_guard(5): return

        url = 'https://www.jigsaw.com/rest/contacts/%s.json' % (self.options['contact'])
        payload = {'token': key, 'username': username, 'password': password, 'purchaseFlag': 'true'}
        resp = self.request(url, payload=payload, redirect=False)
        if resp.json: jsonobj = resp.json
        else:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        # handle output
        contacts = jsonobj['contacts']
        for contact in contacts:
            tdata = []
            for key in contact:
                tdata.append((key.title(), contact[key]))
            self.table(tdata)
