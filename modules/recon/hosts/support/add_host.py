import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', None, 'yes', 'fully qualified domain name')
        self.register_option('address', None, 'no', 'ip address')
        self.info = {
                     'Name': 'Host Adder',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a host.',
                     'Comments':[]
                     }

    # do not remove or rename
    def do_run(self, params):
        # do not remove or modify
        if not self.validate_options(): return
        # === begin module code here ===
        if self.add_host(self.options['host']['value'], self.options['address']['value']):
            self.output('Host successfully added.')
