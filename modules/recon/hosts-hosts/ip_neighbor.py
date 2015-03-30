from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'My-IP-Neighbors.com Lookup',
        'author': 'Micah Hoffman (@WebBreacher)',
        'description': 'Checks My-IP-Neighbors.com for virtual hosts on the same server. Updates the \'hosts\' table with the results.',
        'comments': (
            'This module only stores hosts whose domain matches an entry in the domains table.',
            'Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.',
        ),
        'query': 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL',
        'options': (
            ('restrict', True, True, 'restrict added hosts to current domains'),
        ),
    }
   
    def module_run(self, hosts):
        # build a regex that matches any of the stored domains
        domains = [x[0] for x in self.query('SELECT DISTINCT domain from domains WHERE domain IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join(['\.'+re.escape(x)+'$' for x in domains]))
        for host in hosts:
            self.heading(host, level=0)
            url = 'http://www.my-ip-neighbors.com/?domain=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            results = re.findall(r'a href="http://whois.domaintools.com/(.+?)"', resp.text)
            if not results:
                self.verbose('No additional hosts discovered at the same IP address.')
            for result in results:
                self.output(result)
                # apply restriction
                if self.options['restrict'] and not re.search(regex, result):
                    continue
                # add hosts to the database
                self.add_hosts(result)
