import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('fname', None, 'yes', 'first name')
        self.register_option('lname', None, 'yes', 'last name')
        self.register_option('title', None, 'yes', 'job title')
        self.register_option('email', None, 'no', 'email address')
        self.classify = 'support'
        self.info = {
                     'Name': 'Contact Adder',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a contact.',
                     'Comments':[]
                     }

    # do not remove or rename
    def do_run(self, params):
        # do not remove or modify
        if not self.validate_options(): return
        # === begin module code here ===
        if self.add_contact(self.options['fname']['value'], self.options['lname']['value'], self.options['title']['value'], self.options['email']['value']):
            self.output('Contact successfully added.')
