import framework
import re

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', 'Domain to search.')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'RedIRIS PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches pgp.rediris for email addresses for the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def module_run(self):
        store = self.options['store']['value']
        url = 'http://pgp.rediris.es:11371/pks/lookup'
        payload= {'search' : self.options['domain']['value'] }

        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return 
        except Exception as e:
            self.error(str(e))
            return 

        results = []
        results.extend(re.findall('([^>]*?)(?:\s\(.+?\))?\s&lt;(.*?@%s)&gt;<' % (self.options['domain']['value']), resp.text))
        results.extend(re.findall('[\s]{10,}(\w.*?)(?:\s\(.+?\))?\s&lt;(.*?@%s)&gt;' % (self.options['domain']['value']), resp.text))
        results = list(set(results))
        if not results:
            self.output('No results found.')
            return

        cnt = 0
        new = 0
        for contact in results:
            name = contact[0].strip()
            names = name.split(' ')
            if len(names) == 2:
                first = names[0]
                last = names[1]
            elif len(names) > 2:
                if '.' in names[1] or len(names[1]) == 1:
                    first = names[0]
                    last = names[2]
                else:
                    first = names[0]
                    last = ' '.join(names[1:])
            else:
                first = None
                last = names[0]
            email = contact[1]
            self.output('%s (%s)' % (name, email))
            cnt += 1
            if store: new += self.add_contact(first, last, 'PGP key association', email)
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
