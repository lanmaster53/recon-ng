# packages required for framework integration
import framework

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)

        self.register_option('fname', '', 'yes', 'First name of contact')
        self.register_option('lname', '', 'yes', 'Last name of contact')
        self.register_option('title', '', 'yes', 'Title of contact')
        self.register_option('email', None, 'no', 'Email of contact')


        self.info = {
                     'Name': 'Contact manual add',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a contact.',
                     'Comments':[ ]
                     }

    # do not remove or rename
    def do_run(self, params):
        # do not remove or modify
        if not self.validate_options(): return
        # === begin module code here ===
	self.add_contact( self.options['fname']['value'], self.options['lname']['value'], self.options['title']['value'], self.options['email']['value'] )
