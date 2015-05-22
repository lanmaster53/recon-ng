from recon.core.module import BaseModule
from urlparse import urlparse

class Module(BaseModule):

    meta = {
        'name': 'SalesMaple Contact Harvester',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests contacts from the SalesMaple API using domains as input. Updates the \'contacts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        # https://salesmaple.com/api/contactDomain/lanmaster53.com/0
        base_url = 'https://salesmaple.com/api/contactDomain/%s/%s'
        start = '0'
        for domain in domains:
            self.heading(domain, level=0)
            while start:
                url = base_url % (domain.lower(), start.lower())
                self.verbose('URL: %s' % url)
                resp = self.request(url)
                if resp.json['Count'] == 0:
                    self.output('No contacts found.')
                    break
                for contact in resp.json['Items']:
                    fname = contact['firstName'].title() if 'firstName' in contact else None
                    lname = contact['lastName'].title() if 'lastName' in contact else None
                    name = ' '.join([x for x in [fname, lname] if x]) or None
                    # API documentation says this key will always be present
                    email = contact['contactEmail']
                    title = contact['contactTitle'].title() if 'contactTitle' in contact else None
                    self.output(', '.join([x for x in (name, email, title) if x]))
                    self.add_contacts(first_name=fname, last_name=lname, email=email, title=title)
                start = resp.json['LastEvaluatedKey']['contactEmail'] if 'LastEvaluatedKey' in resp.json else None
