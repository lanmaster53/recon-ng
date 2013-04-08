import framework
import re

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', 'Domain to search.')
        self.info = {
                     'Name': 'RedIRIS PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches pgp.rediris for email addresses for the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def module_run(self):
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
            return 

    def parse(self, data):
        email_expression = re.compile('([^>]*?)\s&lt;(.*?@%s)&gt;' % (self.options['domain']['value']) )
        results = email_expression.findall(data)

        self.verbose('Found %i results.' % len(results))
        for item in results:
            self.verbose('Found results: %s' % ( str(item) ) )

        return list( set(results) )
        
    def add_to_db(self, contact):
        name = contact[0]
        email = contact[1]
        try:
            names = contact[0].split(' ')
            first = names[0]
            #Check for a middle initial
            if '.' in names[1] or len(names[1]) == 1 and len(names) > 2: 
                last = names[2]
            else:
                last = names[1]
            self.add_contact(first, last, email)
        except:
            self.add_contact('', name, email)
