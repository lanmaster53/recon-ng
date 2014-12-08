import module
# module specific packages

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', None, True, 'path and filename for list input')
        self.register_option('table', None, True, 'table to import the list values')
        self.register_option('column', None, True, 'column to import the list values')
        self.info = {
            'Name': 'List File Importer',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Imports values from a list file into a database table and column.',
        }
    
    def module_run(self):
        cnt = 0
        with open(self.options['filename']) as fh:
            lines = fh.read().split()
        method = 'add_'+self.options['table'].lower()
        if not hasattr(self, method):
            self.error('No such table: %s' % (options['table']))
            return
        func = getattr(self, method)
        for line in lines:
            self.output(line)
            kwargs = {self.options['column']: line}
            cnt += func(**kwargs)
        self.output('%d new records added.' % cnt)
