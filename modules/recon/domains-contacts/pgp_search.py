import module
import re

class Module(module.Module):
    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'PGP Key Owner Lookup',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches the MIT public PGP key server for email addresses of the given domain. Updates the \'contacts\' table with the results.',
                     'Comments': [
                                  'Inspiration from theHarvester.py by Christan Martorella: cmarorella[at]edge-seecurity.com'
                                  ]
                     }

    def module_run(self, domains):
        url = 'http://pgp.mit.edu/pks/lookup'
        cnt = 0
        new = 0
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
                self.output('%s (%s)' % (name, email))
                cnt += 1
                if email.lower().endswith(domain.lower()):
                    new += self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, email=email, title='PGP key association')
        self.summarize(new, cnt)
