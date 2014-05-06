import module
# unique to module
import json
import textwrap

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'BuiltWith Server-side Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the BuiltWith API to identify contacts associated with a domain.',
                     }

    def module_run(self, domains):
        key = self.get_key('builtwith_api')
        url = ' http://api.builtwith.com/v3/api.json'
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'key': key, 'lookup': domain, 'hidetext': 'yes'}
            resp = self.request(url, payload=payload)
            if 'error' in resp.json:
                self.error(resp.json['error'])
                continue
            title = 'BuiltWith contact'
            # extract and add emails to contacts
            emails = resp.json['Meta']['Emails']
            if emails is None: emails = []
            for email in emails:
                self.output(email)
                new += self.add_contacts(first_name=None, last_name=None, title=title, email=email)
                cnt += 1
            # extract and add names to contacts
            names = resp.json['Meta']['Names']
            if names is None: names = []
            for name in names:
                self.output(name['Name'])
                fname, mname, lname = self.parse_name(name['Name'])
                new += self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title)
                cnt += 1
            if not any(emails + names):
                self.output('No contacts found.')
        self.summarize(new, cnt)
