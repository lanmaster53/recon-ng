import module
# unique to module
import re


class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
            'Name': 'SSL SAN Lookup',
            'Author': 'Zach Grace (@ztgrace) zgrace@403labs.com',
            'Description': 'Uses the ssltools.com site to obtain the Subject Alternative Names for a domain. Updates the \'hosts\' table with the results.',
            'Comments': [
                'For an alternative version see https://github.com/403labs/recon-ng_modules.'
            ]
        }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            url = 'http://www.ssltools.com/certificate_lookup/%s' % domain
            html = self.request(url).text
            match = re.search('<br>Subject Alternative Names :(.*?)<br>', html)
            if match is None:
                self.output('No Subject Alternative Names found for \'%s\'' % domain)
                continue
            names = match.group(1)
            hosts = [x.strip() for x in names.split(',') if '*' not in x]
            for host in hosts:
                self.output(host)
                self.add_hosts(host)
