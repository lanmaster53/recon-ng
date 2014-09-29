import module
# unique to module
import textwrap

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL')
        self.info = {
                     'Name': 'BuiltWith Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the BuiltWith API to identify hosts, technologies, and contacts associated with a domain.',
                     }

    def module_run(self, domains):
        key = self.get_key('builtwith_api')
        url = ' http://api.builtwith.com/v5/api.json'
        title = 'BuiltWith contact'
        for domain in domains:
            payload = {'key': key, 'lookup': domain}
            resp = self.request(url, payload=payload)
            if 'error' in resp.json:
                self.error(resp.json['error'])
                continue
            for result in resp.json['Results']:
                # extract and consolidate hosts and associated technology data
                data = {}
                for path in result['Result']['Paths']:
                    domain = path['Domain']
                    subdomain = path['SubDomain']
                    host = subdomain if domain in subdomain else '.'.join(filter(len, [subdomain, domain]))
                    if not host in data: data[host] = []
                    data[host] += path['Technologies']
                # process hosts and technology data
                for host in data:
                    # add host to hosts
                    self.heading(host, level=0)
                    domain = '.'.join(host.split('.')[-2:])
                    if domain != host: self.add_hosts(host)
                    # display technologies
                    for item in data[host]:
                        for tag in item:
                            self.output('%s: %s' % (tag, textwrap.fill(str(item[tag]), 100, initial_indent='', subsequent_indent=self.spacer*2)))
                        print(self.ruler*50)
                self.heading('Contacts', level=0)
                # extract and add emails to contacts
                emails = result['Meta']['Emails']
                if emails is None: emails = []
                for email in emails:
                    self.output(email)
                    self.add_contacts(first_name=None, last_name=None, title=title, email=email)
                # extract and add names to contacts
                names = result['Meta']['Names']
                if names is None: names = []
                for name in names:
                    self.output(name['Name'])
                    fname, mname, lname = self.parse_name(name['Name'])
                    self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title)
