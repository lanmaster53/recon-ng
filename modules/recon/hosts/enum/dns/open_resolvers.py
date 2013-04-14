import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Open Recursive DNS Resolvers Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages the Open DNS Resolver Project data at openresolverproject.org to check the class C subnets of \'hosts'\ table entries for open recursive DNS resolvers.',
                     'Comments': [
                                  'Source options: [ db | ip_addr | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        ips = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        if not ips: return
        
