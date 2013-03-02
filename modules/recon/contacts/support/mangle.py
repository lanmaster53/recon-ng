import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'no', 'target email domain')
        self.register_option('pattern', '<fn>.<ln>', 'yes', 'pattern applied to mangle first and last name')
        self.register_option('max-length', 30, 'yes', 'maximum length of email address prefix or username')
        self.info = {
                     'Name': 'Contact Name Mangler',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses or usernames for each harvested contact. This module updates the \'contacts\' table of the database with the results.',
                     'Comments': [
                                  'Pattern options: <fi>,<fn>,<li>,<ln>',
                                  'Example:         <fi>.<ln> => j.doe@domain.com',
                                  'Note: Omit the \'domain\' option to create usernames'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        pattern = self.options['pattern']['value']
        max = self.options['max-length']['value']
        contacts = self.query('SELECT rowid, fname, lname FROM contacts ORDER BY fname')
        if len(contacts) == 0:
            self.error('No contacts in the database.')
            return
        for contact in contacts:
            row = contact[0]
            fname = contact[1]
            lname = contact[2]
            fn = fname.lower()
            fi = fname[:1].lower()
            ln = lname.lower()
            li = lname[:1].lower()
            email = pattern
            try:
                email = email.replace('<fn>', fn)
                email = email.replace('<fi>', fi)
                email = email.replace('<ln>', ln)
                email = email.replace('<li>', li)
            except:
                self.error('Invalid Mutation Pattern \'%s\'.' % (type))
                break
            email = email[:max]
            if domain: email = '%s@%s' % (email, domain)
            self.output('%s %s => %s' % (fname, lname, email))
            self.query('UPDATE contacts SET email="%s" WHERE rowid="%s"' % (email, row))
