import _cmd
import __builtin__
# unique to module

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'pattern': '<fn>.<ln>'
                        }
        self.info = {
                     'Name': 'Contact Name Mangler',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Applies a mangle pattern to all of the contacts stored in the database, creating email addresses for each harvested contact.',
                     'Comments': [
                                  'Pattern options: <fi>,<fn>,<li>,<ln>',
                                  'Example:         <fi>.<ln> => j.doe@domain.com'
                                  ]
                     }

    def do_run(self, params):
        self.mutate_contacts()

    def mutate_contacts(self):
        contacts = self.query('SELECT rowid, fname, lname FROM contacts ORDER BY fname')
        for contact in contacts:
            row = contact[0]
            fname = contact[1]
            lname = contact[2]
            fn = fname.lower()
            fi = fname[:1].lower()
            ln = lname.lower()
            li = lname[:1].lower()
            try:
                email = '%s@%s' % (self.options['pattern'], self.options['domain'])
                email = email.replace('<fn>', fn)
                email = email.replace('<fi>', fi)
                email = email.replace('<ln>', ln)
                email = email.replace('<li>', li)
            except:
                self.error('Invalid Mutation Pattern \'%s\'.' % (type))
                break
            self.output('%s %s => %s' % (fname, lname, email))
            self.query('UPDATE contacts SET email="%s" WHERE rowid="%s"' % (email, row))