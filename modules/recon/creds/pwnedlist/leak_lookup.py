import framework
# unique to module
import pwnedlist

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'pwnedlist leak id')
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the local database for information associated with the given leak ID/s.',
                     'Comments': [
                                  'Source options: [ db | <leak_id> | ./path/to/file | query <sql> ]'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.leak_lookup()

    def leak_lookup(self):
        leak_ids = self.get_source(self.options['source']['value'], 'SELECT DISTINCT leak FROM creds WHERE leak IS NOT NULL')
        if not leak_ids: return

        print self.ruler*50
        for leak_id in leak_ids:
            columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
            if not columns:
                self.output('Please run the \'leaks_dump\' module to populate the database and try again.')
                return
            values = self.query('SELECT %s FROM leaks WHERE leak_id = \'%s\'' % (', '.join(columns), leak_id))[0]
            for i in range(0,len(columns)):
                title = ' '.join(columns[i].split('_')).title()
                self.output('%s: %s' % (title, values[i]))
            print self.ruler*50
