import framework
# unique to module

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('host', None, 'no', 'fully qualified domain name')
        self.register_option('address', None, 'no', 'ip address')
        self.register_option('region', None, 'no', 'city, state or region')
        self.register_option('country', None, 'no', 'country name or code')
        self.register_option('latitude', None, 'no', 'latitude')
        self.register_option('longitude', None, 'no', 'longitude')
        self.info = {
                     'Name': 'Host Adder',
                     'Author': 'Drumm, Zach Grace (@ztgrace)',
                     'Description': 'Manually adds a host.',
                     'Comments':[]
                     }

    def module_run(self):
        host = self.options['host']
        ip = self.options['address']

        if not any((host, ip)):
            self.error("Host or IP required")
            return

        if self.add_host(host, ip, self.options['region'], self.options['country'], self.options['latitude'], self.options['longitude']):
            self.output('Host successfully added.')
