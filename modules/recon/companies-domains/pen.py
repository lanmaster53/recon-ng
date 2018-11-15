from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'IANA Private Enterprise Number Domain Getter',
        'author': 'Jonathan M. Wilbur <jonathan@wilbur.space>',
        'description': 'Given a company name, gathers a domain from the email address of the registered IANA Private Enterprise Number (PEN) contact from the PEN registry. The domain is added to the \'domains\' table.',
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
                domain = match.groups()[2].split('&')[1]
                self.add_domains(domain)
                matchfound = True
            if not matchfound:
                self.alert('No matches found for company \'' + company + '\'')
