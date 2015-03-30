from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - Leak Details Fetcher',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the local database for information associated with a leak ID. The \'leaks_dump\' module must be used to populate the local database before this module will execute successfully.',
        'query': 'SELECT DISTINCT leak FROM credentials WHERE leak IS NOT NULL',
    }

    def module_run(self, leak_ids):
        if not self.query('SELECT COUNT(*) FROM leaks')[0][0]:
            self.output('Please run the \'leaks_dump\' module to populate the database and try again.')
            return
        print(self.ruler*50)
        columns = [x[1] for x in self.query('PRAGMA table_info(leaks)')]
        for leak_id in leak_ids:
            values = self.query('SELECT "%s" FROM leaks WHERE leak_id = \'%s\'' % ('", "'.join(columns), leak_id))[0]
            for i in range(0,len(columns)):
                title = ' '.join(columns[i].split('_')).title()
                self.output('%s: %s' % (title, values[i]))
            print(self.ruler*50)
