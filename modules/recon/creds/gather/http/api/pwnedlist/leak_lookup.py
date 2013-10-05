import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of leak ids for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'PwnedList - Leak Details Fetcher',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the local database for information associated with the given leak ID(s). The \'leaks_dump\' module must be used to populate the local database before this module will execute successfully.',
                     'Comments': [
                                  'Source options: [ db | <leak_id> | ./path/to/file | query <sql> ]'
                                  ]
                     }

    def module_run(self):
        leak_ids = self.get_source(self.options['source']['value'], 'SELECT DISTINCT leak FROM creds WHERE leak IS NOT NULL')

        columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
        if not columns:
            self.output('Please run the \'leaks_dump\' module to populate the database and try again.')
            return
        print self.ruler*50
        for leak_id in leak_ids:
            values = self.query('SELECT "%s" FROM leaks WHERE leak_id = \'%s\'' % ('", "'.join(columns), leak_id))[0]
            for i in range(0,len(columns)):
                title = ' '.join(columns[i].split('_')).title()
                self.output('%s: %s' % (title, values[i]))
            print self.ruler*50
