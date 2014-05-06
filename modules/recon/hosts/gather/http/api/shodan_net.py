import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL ORDER BY netblock')
        self.register_option('limit', 1, 'yes', 'limit number of api requests per input source (0 = unlimited)')
        self.info = {
                     'Name': 'Shodan Network Enumerator',
                     'Author': 'Mike Siegel and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'net\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, netblocks):
        # build a regex that matches any of the stored domains
        domains = [x[0] for x in self.query('SELECT DISTINCT domain from domains WHERE domain IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join(['\.' + x.replace('.', r'\.') for x in domains]))
        limit = self.options['limit']
        cnt = 0
        new = 0
        for netblock in netblocks:
            self.heading(netblock, level=0)
            query = 'net:%s' % (netblock)
            results = self.search_shodan_api(query, limit)
            for host in results:
                if not 'hostnames' in host.keys():
                    continue
                for hostname in host['hostnames']:
                    cnt += 1
                    self.output(hostname)
                    if re.search(regex, hostname):
                        new += self.add_hosts(hostname)
        self.summarize(new, cnt)
