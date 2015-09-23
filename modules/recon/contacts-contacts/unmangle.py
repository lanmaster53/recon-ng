from recon.core.module import BaseModule
import re
from string import capwords
from sre_constants import error as RegexError

class Module(BaseModule):

    patterns = {
        '<fi><ln>': '(?P<first_name>.)(?P<last_name>.*)',
        '<ln><fi>': '(?P<last_name>.*)(?P<first_name>.)',
        '<ln><fi><mi>': '(?P<last_name>.*)(?P<first_name>.)(?P<middle_name>.)',
        '<fn>.<ln>': '(?P<first_name>.*)\.(?P<last_name>.*)',
        '<fn>-<ln>': '(?P<first_name>.*)-(?P<last_name>.*)',
        '<fn>_<ln>': '(?P<first_name>.*)_(?P<last_name>.*)',
        '<fn>': '(?P<first_name>.*)',
        '<ln>': '(?P<last_name>.*)',
    }

    meta = {
        'name': 'Contact Name Unmangler',
        'author': 'Ethan Robish (@EthanRobish)',
        'description': 'Applies a regex or unmangle pattern to all of the contacts stored in the database, pulling out the individual name components. Updates the \'contacts\' table with the results.',
        'comments': (
            'Pattern can be either a regex or a pattern.',
            'The available patterns are:',
            '\t' + ', '.join(patterns.keys()),
            'A regex must capture the values using these named capture groups:',
            '\t(?P<first_name>) (?P<middle_name>) (?P<last_name>)',
            'A regex syntax cheatsheet and troubleshooter can be found here:',
            '\thttp://pythex.org/ or http://www.pyregex.com/',
        ),
        'query': 'SELECT rowid, first_name, middle_name, last_name, email FROM contacts WHERE email IS NOT NULL',
        'options': (
            ('pattern', '<fn>.<ln>', True, 'pattern applied to email'),
            ('overwrite', False, True, 'if set to true will update existing contact entry, otherwise it will create a new entry'),
        ),
    }

    def module_run(self, contacts):
        try:
            regex = self.patterns[self.options['pattern']]
        except KeyError:
            self.verbose('Pre-defined pattern not found. Switching to raw regex mode.')
            regex = self.options['pattern']
        
        try:
            pattern = re.compile(regex)
        except RegexError:
            self.error('Invalid regex specified. Please check your syntax and the resources listed in "show info"')
            return
        
        for contact in contacts:
            rowid = contact[0]
            email = contact[4]
            names = ('first_name', 'middle_name', 'last_name')
            contact = dict(zip(names, contact[1:4]))
            contact_changed = False
            
            username = email.split('@')[0]
            result = pattern.search(username)
            if result is None:
                self.verbose('%s did not match the pattern. Skipping.' % email)
                continue
            
            for name in contact:
                # Update the existing contact only when the current name value is empty or the user specifies to overwrite
                # Possibly consider changing the merge strategy here to whichever data is longer
                if not contact[name] or self.options['overwrite']:
                    try:
                        contact[name] = capwords(result.group(name))
                        contact_changed = True
                    except IndexError:
                        # The name was not captured by the regex
                        pass
            
            # Only do a database query if the contact was actually updated
            if contact_changed:
                values = [contact[name] for name in names] + [rowid]
                self.query('UPDATE contacts SET %s=?,%s=?,%s=? WHERE rowid=?' % names, values)
