from recon.core.module import BaseModule
import textwrap

class Module(BaseModule):

    meta = {
        'name': 'BuiltWith Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the BuiltWith API to identify hosts, technologies, and contacts associated with a domain.',
        'required_keys': ['builtwith_api'],
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'options': (
            ('show_all', True, True, 'display technologies'),
        ),
    }

    def module_run(self, domains):
        key = self.keys.get('builtwith_api')
        url = ' http://api.builtwith.com/v5/api.json'
        title = 'BuiltWith contact'
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'key': key, 'lookup': domain}
            resp = self.request(url, payload=payload)
            if 'error' in resp.json:
                self.error(resp.json['error'])
                continue
            for result in resp.json['Results']:
                # extract and add emails to contacts
                emails = result['Meta']['Emails']
                if emails is None: emails = []
                for email in emails:
                    self.add_contacts(first_name=None, last_name=None, title=title, email=email)
                # extract and add names to contacts
                names = result['Meta']['Names']
                if names is None: names = []
                for name in names:
                    fname, mname, lname = self.parse_name(name['Name'])
                    self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title)
                # extract and consolidate hosts and associated technology data
                data = {}
                for path in result['Result']['Paths']:
                    domain = path['Domain']
                    subdomain = path['SubDomain']
                    host = subdomain if domain in subdomain else '.'.join(filter(len, [subdomain, domain]))
                    if not host in data: data[host] = []
                    data[host] += path['Technologies']
                for host in data:
                    # add host to hosts
                    # *** might domain integrity issues here ***
                    domain = '.'.join(host.split('.')[-2:])
                    if domain != host:
                        self.add_hosts(host)
                # process hosts and technology data
                if self.options['show_all']:
                    for host in data:
                        self.heading(host, level=0)
                        # display technologies
                        if data[host]:
                            self.output(self.ruler*50)
                        for item in data[host]:
                            for tag in item:
                                self.output('%s: %s' % (tag, textwrap.fill(self.to_unicode_str(item[tag]), 100, initial_indent='', subsequent_indent=self.spacer*2)))
                            self.output(self.ruler*50)
