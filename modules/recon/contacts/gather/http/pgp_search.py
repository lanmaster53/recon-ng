import framework
import re

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('domain', self.goptions['domain']['value'], 'yes', 'Domain to search.')
        self.info = {
                     'Name': 'RedIRIS PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches pgp.rediris for email addresses for the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def do_run(self, params):
        data = self.search_rediris()
        if not data:
            self.error('No useful data found.')
            return
        
        emails = self.parse(data)
        if not emails:
            return

        for contact in emails:
            self.add_to_db(contact)

    def search_rediris(self):
        url = 'http://pgp.rediris.es:11371/pks/lookup'
        payload= {'search' : self.options['domain']['value'] }

        try: 
            return self.request(url, payload = payload).text
        except KeyboardInterrupt:
            print ''
            return 
        except Exception as e:
            self.error( str(e) )
            return False
    
    def parse(self, data):
        email_expression = r'([^>]*?)\s&lt;(.*?@%s)&gt;' % (self.options['domain']['value']
        results = email_expression.findall(data)
        
        self.verbose('Found %i results.' % len(results))
        for item in results:
            self.verbose('Found results: %s' % ( str(item) )

        return list( set(results) )
        
    def add_to_db(self, contact):
        try:
            names = contact[0].split(' ')
            self.add_contact(names[0], names[1], contact[1])
        except:
            self.add_contact('', contact[0], contact[1])
