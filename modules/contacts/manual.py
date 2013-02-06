# packages required for framework integration
import framework
# module specific packages

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        # register local options here
        # local option values can be accessed within the module via 
	#self.options['name']['value']
        # global options can be referenced via self.goptions['name']['value']
        # the register_option method expects 4 arguments:
        # 1. the name of the option
        # 2. the true value of the option (strings, integers and boolean values are allowed)
        # 3. "yes" or "no" for whether or not the option is mandatory
        # 4. a description of the option
        self.register_option('fname', '', 'yes', 'First name of contact')
        self.register_option('lname', '', 'yes', 'Last name of contact')
        self.register_option('title', '', 'yes', 'Title of contact')
        self.register_option('email', None, 'no', 'Email of contact')
        # global options can be imported by referencing the self.goptions dictionary when 
	#registering options
        #self.register_option('verbose', self.goptions['verbose']['value'], 'yes', 
	#self.goptions['verbose']['desc'])
        # set module information here
        # do not remove or modify the key names
        # leave comments as an empty list to omit
        self.info = {
                     'Name': 'Manual Add',
                     'Author': 'Drumm',
                     'Description': 'Manually adds a contact.',
                     'Comments':[ ]
                     }
    # do not remove or rename
    def do_run(self, params):
        # do not remove or modify
        if not self.validate_options(): return
        # === begin module code here ===
        # call the main method which will handle module logic
	self.add_contact( self.options['fname']['value'], self.options['lname']['value'], self.options['title']['value'], self.options['email']['value'] )
