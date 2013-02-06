# packages required for framework integration
import framework
# module specific packages

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)

        self.register_option('host', '', 'yes', 'The FQDN of the host as a string')
        self.register_option('address', None, 'no', 'The IP address of the host')

        self.info = {
                     'Name': 'Manual add host',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a host.',
                     'Comments':[ ]
                     }

    # do not remove or rename
    def do_run(self, params):
        # do not remove or modify
        if not self.validate_options(): return
        # === begin module code here ===
        # call the main method which will handle module logic
	self.add_host( self.options['host']['value'], self.options['address']['value'] )
