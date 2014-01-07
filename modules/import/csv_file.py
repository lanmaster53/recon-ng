# packages required for framework integration
import framework
# module specific packages
import csv

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('filename', None, 'yes', 'path and filename for csv input')
        self.register_option('column_separator', ',', 'yes', 'character that separates each column value')
        self.register_option('quote_character', '', 'no', 'character that surrounds each column value')
        self.register_option('has_header', True, 'yes', 'whether or not the first row in the csv file should be interpreted as column names')
        self.register_option('table', None, 'yes', 'table to import the csv values')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Advanced CSV File Importer',
                     'Author': 'Ethan Robish (@EthanRobish)',
                     'Description': 'Imports values from a csv file to a database table.',
                     'Comments': [
                                  'At first you will see only a few options. Once you set a valid filename, you will be able to see more options for configuring where each column is imported.',
                                  'This module is very powerful, but if you aren\'t careful it could seriously pollute your database.',
                                  ]
                     }
        self.values = []

    def do_set(self, params):
        orig_filename = self.options['filename']['value']
        orig_sep = self.options['column_separator']['value']
        orig_quote = self.options['quote_character']['value']
        orig_has_header = self.options['has_header']['value']
        
        framework.module.do_set(self, params)

        filename = self.options['filename']['value']
        sep = self.options['column_separator']['value']
        quote = self.options['quote_character']['value']
        has_header = self.options['has_header']['value']

        # if anything has changed, repopulate the modules options
        if filename != orig_filename 
            or sep != orig_sep 
            or quote != orig_quote 
            or has_header != orig_has_header:
            try:
                self.values = self.parse_file(filename, sep, quote)
            except IOError:
                self.error('%s could not be opened. Does it exist?' % filename)
            except AssertionError:
                self.error('The number of columns in each row is inconsistent. \
                Try checking the input file, changing the column separator, or changing the quote character.')
            else:
                self.register_options()
    
    def module_run(self):
        if not self.values or len(self.values) == 0:
            return

        has_header = self.options['has_header']['value']
        verbose = self.options['verbose']['value']

        all_column_names = [None] * len(self.values[0])
        for option in self.options:
            if option.startswith('csv_'):
                name = option[4:].replace('_', ' ').lower()
                try:
                    index = int(name)
                except ValueError:
                    index = self.values[0].index(name)

                all_column_names[index] = self.options[option]['value']

        # e.g. all_column_names = [None, 'fname', 'lname', None, 'title']

        # ensure that at least one column name is populated
        if not any(all_column_names):
            self.error('You must set at least one column name to import')
            return

        # build the query based on which column options have been set
        table = self.options['table']['value']
        used_column_names = []
        used_column_indices = []
        for index, name in enumerate(all_column_names):
            if name:
                used_column_names.append(name)
                used_column_indices.append(index)

        # e.g. used_column_names = ['fname', 'lname', 'title']
        # e.g. used_column_indices = [1, 2, 4]

        for row in self.values[(1 if has_header else 0):]:
            # creates a dictionary where the keys are the column names and the values are the column values from row
            data = dict(
                zip(
                    used_column_names,
                    map(row.__getitem__, used_column_indices)
                )
            )
            # e.g. data = {'fname':'John', 'lname':'Doe', 'title':'CEO'}
            if verbose: self.output('Inserting %s' % ' '.join([data[col] for col in used_column_names]))
            if not self.insert(table, data):
                self.error('There was a problem inserting the previous row into the database. Please check your settings.')
                return


    def parse_file(self, filename=None, sep=None, quote=None):
        if filename is None:
            filename = self.options['filename']['value']
        if sep is None:
            sep = self.options['column_separator']['value']
        if filename is None or sep is None:
            raise IOError

        has_header = self.options['has_header']['value']
        values = []

        with open(filename, 'rb') as infile:
            if not quote:
                csvreader = csv.reader(infile, delimiter=sep, quoting=csv.QUOTE_NONE)
            else:
                csvreader = csv.reader(infile, delimiter=sep, quotechar=quote)

            # get each line from the file and separate it into columns based on sep
            for row in csvreader:
                # if a header line exists, make it lower case
                if len(values) == 0 and has_header:
                    values.append([value.strip().lower() for value in row])
                    continue
            
                # append all lines after header as-is case-wise
                values.append([value.strip() for value in row])
                # ensure the number of columns in each row is the same as the previous row
                if len(values) > 1:
                    assert len(values[-1]) == len(values[-2])

        return values

    def register_options(self):
        if not self.values or len(self.values) == 0:
            return

        # remove any old options
        options = self.options.keys()
        for option in options:
            if option.startswith('csv_'):
                del self.options[option]

        # add the new options
        has_header = self.options['has_header']['value']
        if has_header:
            for header in self.values[0]:
                self.register_option('csv_%s' % header.replace(' ', '_'), None, 'no', 'database column name where this csv column will be imported')
        else:
            for i in range(len(self.values[0])):
                self.register_option('csv_%d' % i, None, 'no', 'database column name where this csv column will be imported')
