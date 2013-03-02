import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('fname', None, 'yes', 'first name')
        self.register_option('lname', None, 'yes', 'last name')
        self.register_option('title', None, 'yes', 'job title')
        self.register_option('email', None, 'no', 'email address')
        self.info = {
                     'Name': 'Contact Adder',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a contact.',
                     'Comments':[]
                     }

    def module_run(self):
        if self.add_contact(self.options['fname']['value'], self.options['lname']['value'], self.options['title']['value'], self.options['email']['value']):
            self.output('Contact successfully added.')
