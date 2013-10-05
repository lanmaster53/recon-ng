import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'no', 'target email domain')
        self.register_option('pattern', '<fn>.<ln>', 'yes', 'pattern applied to mangle first and last name')
        self.register_option('max-length', 30, 'yes', 'maximum length of email address prefix or username')
        self.register_option('overwrite', False, 'yes', 'overwrite exisitng email addresses')
        self.info = {
                     'Name': 'Contact Name Mangler',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses or usernames for each harvested contact and updating the \'contacts\' table of the database with the results.',
                     'Comments': [
                                  'Pattern options: <fi>,<fn>,<li>,<ln>',
                                  'Example:         <fi>.<ln> => j.doe@domain.com',
                                  'Note: Omit the \'domain\' option to create usernames'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        pattern = self.options['pattern']['value']
        max_len = self.options['max-length']['value']
        overwrite = self.options['overwrite']['value']
        contacts = self.query('SELECT rowid, fname, lname FROM contacts ORDER BY fname' if overwrite else 'SELECT rowid, fname, lname FROM contacts WHERE email IS NULL ORDER BY fname')
        if len(contacts) == 0:
            self.error('No contacts to mangle.')
            return
        for contact in contacts:
            row = contact[0]
            fname = contact[1]
            lname = contact[2]
            email = pattern
            items = {'<fn>': '', '<fi>': '', '<ln>': '', '<li>': ''}
            if fname:
                items['<fn>'] = fname.lower()
                items['<fi>'] = fname[:1].lower()
            if lname:
                items['<ln>'] = lname.lower()
                items['<li>'] = lname[:1].lower()
            for item in items:
                email = email.replace(item, items[item])
            email = email[:max_len]
            if domain: email = '%s@%s' % (email, domain)
            self.output('%s %s => %s' % (fname, lname, email))
            self.query('UPDATE contacts SET email=? WHERE rowid=?', (email, row))
