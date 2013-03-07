import framework
import re

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': '',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches pgp.rediris for email addresses for the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }
        self.register_option('domain', 'placeholder.com', 'yes', 'Domain to search.')

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin module code here ===
        data = self.query()
        if not data:
            self.error('No useful data found.')
            return
        
        emails = self.parse(data)
        if not emails:
            return

        for contact in emails:
            self.add_to_db(contact)

    def query(self):
        url = 'http://pgp.rediris.es:11371/pks/lookup'
        payload= {'search' : self.options['domain']['value'] }

        try: 
            return self.request(url, method = 'GET', payload = payload).text
        except KeyboardInterrupt:
            self.error('Interrupted during search...')
            return False
        except Exception as e:
            self.error( str(e) )
            return False
    
    def parse(self, data):
        email_expression = re.compile('">(\w* \w*) .*?&lt;(.*?@.*?)&gt;')
        results = email_expression.findall(data)

        try:
            if self.options['verbose']['value']:
                self.output('Found %i results.' % len(results))
                for item in results:
                    self.output('Found result: %s' % (str(item)))

            return list( set(results) )
        
        except Exception as e:
            self.error( str(e) )
            return False

    def add_to_db(self, contact):
        self.alert('Adding %s, %s to /contacts/ database.' %(contact[0], contact[1]))
        
        try:
            names = contact[0].split(' ')
            self.add_contact(names[0], names[1], contact[1])
        except:
            self.add_contact('', contact[0], contact[1])
