from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'IANA Private Enterprise Number Company-by-Domain Lookup',
        'author': 'Jonathan M. Wilbur <jonathan@wilbur.space>',
        'description': 'Given a domain, finds a contact in the IANA Private Enterprise Number (PEN) registry whose email address ends with that domain. The domain is then added to the \'domains\' table.',
        'required_keys': [],
        'comments': (),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'options': (),
    }

    def module_run(self, domains):
        url = 'https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers'
        resp = self.request(url, method='GET')
        if resp.status_code != 200:
            self.alert('When retrieving IANA PEN Registry, got HTTP status code ' + str(resp.status_code) + '!')
        for domain in domains:
            dom = re.escape(domain)
            regex = '(\d+)\\s*\\n\\s{2}(.*)\\s*\\n\\s{4}(.*)\\s*\\n\\s{6}(.*)&' + dom + '\\s*\\n'
            matchfound = False
            for match in re.finditer(regex, resp.text, re.IGNORECASE):
                fullname = match.groups()[2]
                fname, mname, lname = self.parse_name(fullname)
                email = match.groups()[3] + '@' + domain
                self.add_contacts(
                    first_name=fname,
                    middle_name=mname,
                    last_name=lname,
                    email=email
                )
                matchfound = True
            if not matchfound:
                self.alert('No matches found for domain \'' + domain + '\'')
