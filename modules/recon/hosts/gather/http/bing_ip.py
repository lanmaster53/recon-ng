import framework
# unique to module
from urlparse import urlparse

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'Bing IP Neighbor Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Bing API and "ip:" advanced search operator to enumerate other virtual hosts sharing the same IP address.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        addresses = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not addresses: return
        store = self.options['store']['value']

        new = 0
        hosts = []
        for address in addresses:
            query = '\'ip:%s\'' % (address)
            try: results = self.search_bing_api(query)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            if type(results) != list: break
            if not results: self.verbose('No additional hosts discovered at the same IP address.')
            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts:
                    hosts.append(host)
                    self.output(host)
                    # add each host to the database
                    if store: new += self.add_host(host)

        self.output('%d total hosts found.' % (len(hosts)))
        if store and new: self.alert('%d NEW hosts found!' % (new))
