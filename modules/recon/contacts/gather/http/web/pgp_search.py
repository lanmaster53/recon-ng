import module
import re

class Module(module.Module):
    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', 'domain to search')
        self.info = {
                     'Name': 'PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches the MIT public PGP key server for email addresses of the given domain.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']

        url = 'http://pgp.mit.edu/pks/lookup'
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
            first, middle, last = self.parse_name(name)
            email = contact[1]
            self.output('%s (%s)' % (name, email))
            cnt += 1
            if email.lower().endswith(domain.lower()):
                new += self.add_contact(first, last, 'PGP key association', email)
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
