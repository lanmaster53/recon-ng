import framework
# unique to module

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('fname', None, 'yes', 'first name')
        self.register_option('lname', None, 'yes', 'last name')
        self.register_option('title', None, 'yes', 'job title')
        self.register_option('email', None, 'no', 'email address')
        self.register_option('region', None, 'no', 'city, state or region')
        self.register_option('country', None, 'no', 'country name or code')
        self.info = {
                     'Name': 'Contact Adder',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a contact.',
                     'Comments':[]
                     }

    def module_run(self):
        if self.add_contact(self.options['fname'], self.options['lname'], self.options['title'], self.options['email'], self.options['region'], self.options['country']):
            self.output('Contact successfully added.')
