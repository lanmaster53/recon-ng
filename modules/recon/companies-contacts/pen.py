from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'IANA Private Enterprise Number Contact Getter',
        'author': 'Jonathan M. Wilbur <jonathan@wilbur.space>',
        'description': 'Given a company name, gathers the registered IANA Private Enterprise Number (PEN) contact from the PEN registry. The contacts\'s full name and email address are then added to the \'contacts\' table.',
        'required_keys': [],
        'comments': (),
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
        'options': (),
    }

    def module_run(self, companies):
        url = 'https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers'
        resp = self.request(url, method='GET')
        if resp.status_code != 200:
            self.alert('When retrieving IANA PEN Registry, got HTTP status code ' + str(resp.status_code) + '!')
        for company in companies:
            comp = re.escape(company)
            regex = '(\d+)\\s*\\n\\s{2}.*' + comp + '.*\\s*\\n\\s{4}(.*)\\s*\\n\\s{6}(.*)\\s*\\n'
            matchfound = False
            for match in re.finditer(regex, resp.text, re.IGNORECASE):
                fullname = match.groups()[1]
                fname, mname, lname = self.parse_name(fullname)
                email = match.groups()[2].replace('&', '@')
                self.add_contacts(
                    first_name=fname,
                    middle_name=mname,
                    last_name=lname,
                    email=email
                )
                matchfound = True
            if not matchfound:
                self.alert('No matches found for company \'' + company + '\'')
