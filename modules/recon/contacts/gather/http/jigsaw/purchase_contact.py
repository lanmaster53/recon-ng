import framework
# unique to module
import urllib
import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
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
        username = self.options['username']['value']
        password = self.options['password']['value']
        key = self.manage_key('jigsaw_key', 'Jigsaw API Key')
        if not key: return

        # point guard
        if not self.api_guard(5): return

        url = 'https://www.jigsaw.com/rest/contacts/%s.json' % (self.options['contact']['value'])
        payload = {'token': key, 'username': username, 'password': password, 'purchaseFlag': 'true'}
        try: resp = self.request(url, payload=payload, redirect=False)
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
        contacts = jsonobj['contacts']
        for contact in contacts:
            tdata = []
            for key in contact:
                tdata.append((key.title(), contact[key]))
            self.table(tdata)
