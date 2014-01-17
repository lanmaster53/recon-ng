# packages required for framework integration
import framework
# module specific packages
import csv

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('filename', None, 'yes', 'path and filename for csv input')
        self.register_option('column_separator', ',', 'yes', 'character that separates each column value')
        self.register_option('quote_character', '', 'no', 'character that surrounds each column value')
        self.register_option('has_header', True, 'yes', 'whether or not the first row in the csv file should be interpreted as column names')
        self.register_option('table', None, 'yes', 'table to import the csv values')
        self.info = {
                     'Name': 'Advanced CSV File Importer',
                     'Author': 'Ethan Robish (@EthanRobish)',
                     'Description': 'Imports values from a csv file to a database table.',
                     'Comments': [
                                  'Only a few options are available until a valid filename is set. Then, the file is analyzed and more options become available for configuring where each column is imported.',
                                  'This module is very powerful and can seriously pollute a database. Backing up the database before importing is encouraged.',
                                  ]
                     }
        
        self.values = []
        # account for the fact that module options are stored and preloaded from a config file
        self._validate_options()
            
    def _validate_options(self):
        filename = self.options['filename']
        sep = self.options['column_separator']
        quote = self.options['quote_character']
        
        if not filename:
            # there is currently no valid file so remove all the options file-specific options
            self.values = []
            self.register_options()
            return False
        if not sep or len(sep) != 1:
            self.error('COLUMN_SEPARATOR is required and must only contain one character.')
            # there is currently no valid separator so remove all the options file-specific options
            self.values = []
            self.register_options()
            return False
        if quote and len(quote) > 1:
            self.error('QUOTE_CHARACTER is optional but must not contain more than one character.')
            # there is currently no valid quote so remove all the options file-specific options
            self.values = []
            self.register_options()
            return False
            
        return True

    def do_set(self, params):
        framework.Framework.do_set(self, params)
        
        if not self._validate_options():
            return
            
        # repopulate the module's options
        try:
            self.values = self.parse_file()
        except IOError:
            self.error('%s could not be opened. The file may not exist.' % self.options['filename'])
        except AssertionError:
            self.error('The number of columns in each row is inconsistent. Try checking the input file, changing the column separator, or changing the quote character.')
        else:
            self.register_options()
    
    def module_run(self):
        if not self.values or len(self.values) == 0:
            return

        has_header = self.options['has_header']

        all_column_names = [None] * len(self.values[0])
        for option in self.options:
            if option.startswith('csv_'):
                name = option[4:].replace('_', ' ').lower()
                try:
                    index = int(name)
                except ValueError:
                    index = self.values[0].index(name)

                all_column_names[index] = self.options[option]

        # e.g. all_column_names = [None, 'fname', 'lname', None, 'title']

        # ensure that at least one column name is populated
        if not any(all_column_names):
            self.error('You must set at least one column name to import.')
            return

        # build the query based on which column options have been set
        table = self.options['table']
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
            self.verbose('Inserting %s' % ' '.join([data[col] for col in used_column_names]))
            if not self.insert(table, data):
                self.error('There was a problem inserting the previous row into the database. Please check your settings.')
                return

    def parse_file(self):
        filename = self.options['filename']
        if not filename:
            raise IOError
        sep = self.options['column_separator']
        quote = self.options['quote_character']
        has_header = self.options['has_header']
        values = []

        with open(filename, 'rb') as infile:
            # if sep is not a one character string, csv.reader will raise a TypeError
            if not quote:
                csvreader = csv.reader(infile, delimiter=str(sep), quoting=csv.QUOTE_NONE)
            else:
                csvreader = csv.reader(infile, delimiter=str(sep), quotechar=str(quote))

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
        # remove any old file-specific options
        options = self.options.keys()
        for option in options:
            if option.startswith('csv_'):
                del self.options[option]
        
        # if there are no values, then there is nothing left to do
        if not self.values or len(self.values) == 0:
            return

        # add the new options
        has_header = self.options['has_header']
        if has_header:
            for header in self.values[0]:
                self.register_option('csv_%s' % header.replace(' ', '_'), None, 'no', 'database column name where this csv column will be imported')
        else:
            for i in range(len(self.values[0])):
                self.register_option('csv_%d' % i, None, 'no', 'database column name where this csv column will be imported')
