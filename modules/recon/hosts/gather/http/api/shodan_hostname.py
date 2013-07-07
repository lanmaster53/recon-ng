import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('restrict', True, 'yes', 'limit number of api requests to \'REQUESTS\'')
        self.register_option('requests', 1, 'yes', 'maximum number of api requets to make')
        self.info = {
                     'Name': 'Shodan Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'restrict\' option limits the number of API requests to \'requests\' in order to prevent API query exhaustion.'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        subs = []
        cnt = 0
        query = 'hostname:%s' % (domain)
        limit = self.options['requests']['value'] if self.options['restrict']['value'] else 0
        results = self.search_shodan_api(query, limit)
        for host in results:
            if not 'hostnames' in host.keys():
                continue
            for hostname in host['hostnames']:
                site = '.'.join(hostname.split('.')[:-2])
                if site and site not in subs:
                    subs.append(site)
                    new = True
                    host = '%s.%s' % (site, domain)
                    self.output('%s' % (host))
                    cnt += self.add_host(host)
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
