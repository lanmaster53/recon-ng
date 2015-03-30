from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Contact Name Mangler',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses or usernames for each harvested contact. Updates the \'contacts\' table with the results.',
        'comments': (
            'Pattern options: <fi>,<fn>,<mi>,<mn>,<li>,<ln>',
            'Example:         <fi>.<ln> => j.doe@domain.com',
            'Note: Omit the \'domain\' option to create usernames',
        ),
        'query': 'SELECT rowid, first_name, middle_name, last_name, email FROM contacts ORDER BY first_name',
        'options': (
            ('domain', None, False, 'target email domain'),
            ('pattern', '<fn>.<ln>', True, 'pattern applied to mangle first and last name'),
            ('substitute', '-', True, 'character to substitute for invalid email address characters'),
            ('max-length', 30, True, 'maximum length of email address prefix or username'),
            ('overwrite', False, True, 'overwrite existing email addresses'),
        ),
    }

    def module_run(self, contacts):
        for contact in contacts:
            if not self.options['overwrite'] and contact[4] is not None:
                continue
            row = contact[0]
            fname = contact[1]
            mname = contact[2]
            lname = contact[3]
            email = self.options['pattern']
            sub_pattern = '[\s]'
            substitute = self.options['substitute']
            items = {'<fn>': '', '<fi>': '', '<mn>': '', '<mi>': '', '<ln>': '', '<li>': ''}
            if fname:
                items['<fn>'] = re.sub(sub_pattern, substitute, fname.lower())
                items['<fi>'] = fname[:1].lower()
            if mname:
                items['<mn>'] = re.sub(sub_pattern, substitute, mname.lower())
                items['<mi>'] = mname[:1].lower()
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
