import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', None, 'yes', 'fully qualified domain name')
        self.register_option('address', None, 'no', 'ip address')
        self.register_option('region', None, 'no', 'city, state or region')
        self.register_option('country', None, 'no', 'country name or code')
        self.register_option('latitude', None, 'no', 'latitude')
        self.register_option('longitude', None, 'no', 'longitude')
        self.info = {
                     'Name': 'Host Adder',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a host.',
                     'Comments':[]
                     }

    def module_run(self):
        if self.add_host(self.options['host']['value'], self.options['address']['value'], self.options['region']['value'], self.options['country']['value'], self.options['latitude']['value'], self.options['longitude']['value']):
            self.output('Host successfully added.')
