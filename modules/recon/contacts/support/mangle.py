import framework
# unique to module
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'no', 'target email domain')
        self.register_option('pattern', '<fn>.<ln>', 'yes', 'pattern applied to mangle first and last name')
        self.register_option('substitute', '-', 'yes', 'character to substitute for invalid email address characters')
        self.register_option('max-length', 30, 'yes', 'maximum length of email address prefix or username')
        self.register_option('overwrite', False, 'yes', 'overwrite existing email addresses')
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
        contacts = self.query('SELECT rowid, fname, lname FROM contacts ORDER BY fname' if self.options['overwrite'] else 'SELECT rowid, fname, lname FROM contacts WHERE email IS NULL ORDER BY fname')
        if len(contacts) == 0:
            self.error('No contacts to mangle.')
            return
        for contact in contacts:
            row = contact[0]
            fname = contact[1]
            lname = contact[2]
            email = self.options['pattern']
            sub_pattern = '[\s]'
            substitute = self.options['substitute']
            items = {'<fn>': '', '<fi>': '', '<ln>': '', '<li>': ''}
            if fname:
                items['<fn>'] = re.sub(sub_pattern, substitute, fname.lower())
                items['<fi>'] = fname[:1].lower()
            if lname:
                items['<ln>'] = re.sub(sub_pattern, substitute, lname.lower())
                items['<li>'] = lname[:1].lower()
            for item in items:
                email = email.replace(item, items[item])
            email = email[:self.options['max-length']]
            domain = self.options['domain']
            if domain: email = '%s@%s' % (email, domain)
            self.output('%s %s => %s' % (fname, lname, email))
            self.query('UPDATE contacts SET email=? WHERE rowid=?', (email, row))
