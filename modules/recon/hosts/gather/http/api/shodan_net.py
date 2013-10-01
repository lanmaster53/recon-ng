import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('subnet', None, 'yes', 'CIDR block of the target network (X.X.X.X/Y)')
        self.register_option('restrict', 1, 'yes', 'limit number of api requests (0 = unrestricted)')
        self.info = {
                     'Name': 'Shodan Network Enumerator',
                     'Author': 'Mike Siegel and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'net\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'RESTRICT\' option limits the number of API requests in order to prevent API query exhaustion.'
                                  ]
                     }

    def module_run(self):
        cidr = self.options['subnet']['value']
        subs = []
        cnt = 0
        query = 'net:%s' % (cidr)
        limit = self.options['restrict']['value']
        results = self.search_shodan_api(query, limit)
        for host in results:
            if not 'hostnames' in host.keys():
                continue
            for hostname in host['hostnames']:
                if hostname not in subs:
                    subs.append(hostname)
                    self.output('%s' % (hostname))
                    cnt += self.add_host(hostname)
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
