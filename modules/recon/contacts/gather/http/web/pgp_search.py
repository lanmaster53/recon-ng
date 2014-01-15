import framework
import re

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', 'domain to search')
        self.info = {
                     'Name': 'RedIRIS PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches pgp.rediris for email addresses for the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']

        url = 'http://pgp.rediris.es/pks/lookup'
        payload= {'search' : self.options['domain'] }
        resp = self.request(url, payload=payload)

        results = []
        results.extend(re.findall('([^>]*?)(?:\s\(.+?\))?\s&lt;(.*?@%s)&gt;<' % (self.options['domain']), resp.text))
        results.extend(re.findall('[\s]{10,}(\w.*?)(?:\s\(.+?\))?\s&lt;(.*?@%s)&gt;' % (self.options['domain']), resp.text))
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
            if email.lower().endswith(domain.lower()):
                new += self.add_contact(first, last, 'PGP key association', email)
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
