from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'PGP Key Owner Lookup',
        'author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
        'description': 'Searches the MIT public PGP key server for email addresses of the given domain. Updates the \'contacts\' table with the results.',
        'comments': (
            'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        url = 'http://pgp.mit.edu/pks/lookup'
        for domain in domains:
            self.heading(domain, level=0)
            payload= {'search' : domain}
            resp = self.request(url, payload=payload)
            # split the response into the relevant lines
            lines = [x.strip() for x in re.split('[\n<>]', resp.text) if domain in x]
            results = []
            for line in lines:
                # remove parenthesized items
                line = re.sub('\s*\(.*\)\s*', '', line)
                # parse out name and email address
                match = re.search('^(.*)&lt;(.*)&gt;$', line)
                if match:
                    # clean up and append the parsed elements
                    results.append(tuple([x.strip() for x in match.group(1, 2)]))
            results = list(set(results))
            if not results:
                self.output('No results found.')
                continue
            for contact in results:
                name = contact[0].strip()
                fname, mname, lname = self.parse_name(name)
                email = contact[1]
                if email.lower().endswith(domain.lower()):
                    self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, email=email, title='PGP key association')
