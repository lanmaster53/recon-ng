import framework
import __builtin__
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'pattern': '<fn>.<ln>',
                        'max-length': 30
                        }
        self.info = {
                     'Name': 'Contact Name Mangler',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses or usernames for each harvested contact.',
                     'Comments': [
                                  'Pattern options: <fi>,<fn>,<li>,<ln>',
                                  'Example:         <fi>.<ln> => j.doe@domain.com',
                                  'Note: Omit the \'domain\' option to create usernames'
                                  ]
                     }

    def do_run(self, params):
        self.mutate_contacts()

    def mutate_contacts(self):
        domain = self.options['domain']
        pattern = self.options['pattern']
        max = self.options['max-length']
        contacts = self.query('SELECT rowid, fname, lname FROM contacts ORDER BY fname')
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