import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('restrict', 1, 'yes', 'limit number of api requests (0 = unrestricted)')
        self.info = {
                     'Name': 'Shodan Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'RESTRICT\' option limits the number of API requests in order to prevent API query exhaustion.'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        subs = []
        cnt = 0
        query = 'hostname:%s' % (domain)
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
