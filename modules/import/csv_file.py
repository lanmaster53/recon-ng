# packages required for framework integration
import module
# module specific packages
import csv

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', None, True, 'path and filename for csv input')
        self.register_option('column_separator', ',', True, 'character that separates each column value')
        self.register_option('quote_character', '', False, 'character that surrounds each column value')
        self.register_option('has_header', True, True, 'whether or not the first row in the csv file should be interpreted as column names')
        self.register_option('table', None, True, 'table to import the csv values')
        self.info = {
            'Name': 'Advanced CSV File Importer',
            'Author': 'Ethan Robish (@EthanRobish)',
            'Description': 'Imports values from a CSV file into a database table.',
            'Comments': [
                'Only a few options are available until a valid filename is set. Then, the file is analyzed and more options become available for configuring where each CSV entry is imported.',
                'This module is very powerful and can seriously pollute a database. Backing up the database before importing is encouraged.',
            ]
        }
        
        # stores the values read from the CSV file
        self.__values = []
        # keeps track of which module options correspond to which CSV column index
        self.__csv_indices = {}
        # account for the fact that module options are stored and preloaded from a config file
        self.__init_options()
            
    def do_set(self, params):
        module.Module.do_set(self, params)
        self.__init_options()
    
    def module_run(self):
        if not self.__values or len(self.__values) == 0:
            return

        has_header = self.options['has_header']

        # stores the database column names to be imported
        # initialize it to a list the size of a row
        all_column_names = [None] * len(self.__values[0])
        for option in self.options:
            if option.startswith('csv_'):
                index = self.__csv_indices[option]
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

        for row in self.__values[(1 if has_header else 0):]:
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

    def __init_options(self):
        if not self.__validate_options():
            return
            
        # repopulate the module's options
        try:
            self.__values = self.__parse_file()
        except IOError:
            self.error('\'%s\' could not be opened. The file may not exist.' % self.options['filename'])
        except AssertionError:
            self.error('The number of columns in each row is inconsistent. Try checking the input file, changing the column separator, or changing the quote character.')
        else:
            self.__register_options()
            
    def __validate_options(self):    # begins with an underscore so as not to conflict with the parent class's validate_options method
        filename = self.options['filename']
        sep = self.options['column_separator']
        quote = self.options['quote_character']
        
        if not filename:
            # there is currently no valid file so remove all the options file-specific options
            self.__values = []
            self.__register_options()
            return False
        if not sep or len(sep) != 1:
            self.error('COLUMN_SEPARATOR is required and must only contain one character.')
            # there is currently no valid separator so remove all the options file-specific options
            self.__values = []
            self.__register_options()
            return False
        if quote and len(quote) > 1:
            self.error('QUOTE_CHARACTER is optional but must not contain more than one character.')
            # there is currently no valid quote so remove all the options file-specific options
            self.__values = []
            self.__register_options()
            return False
            
        return True
        
    def __parse_file(self):
        filename = self.options['filename']
        if not filename:
            raise IOError
        sep = self.options['column_separator']
        quote = self.options['quote_character']
        values = []

        with open(filename, 'rb') as infile:
            # if sep is not a one character string, csv.reader will raise a TypeError
            if not quote:
                csvreader = csv.reader(infile, delimiter=str(sep), quoting=csv.QUOTE_NONE)
            else:
                csvreader = csv.reader(infile, delimiter=str(sep), quotechar=str(quote))

            # get each line from the file and separate it into columns based on sep
            for row in csvreader:
                # append all lines as-is case-wise
                # unicode(str, errors='ignore') causes all invalid characters to be stripped out
                values.append([unicode(value.strip(), errors='ignore') for value in row])
                # ensure the number of columns in each row is the same as the previous row
                if len(values) > 1:
                    assert len(values[-1]) == len(values[-2])

        return values

    def __register_options(self):
        # remove any old csv-file options
        options = self.options.keys()
        for option in options:
            if option.startswith('csv_'):
                del self.options[option]
        
        # if there are no values, then there is nothing left to do
        if not self.__values or len(self.__values) == 0:
            return

        # add the new options
        has_header = self.options['has_header']
        
        for i, header in enumerate(self.__values[0]):
            prefix = 'csv_'
            if has_header:
                # TODO: use translate to map any bad characters to _
                option_name = prefix + header.replace(' ', '_').lower()
            else:
                option_name = prefix + str(i)

            # save the mapping of option name to column index
            self.__csv_indices[option_name] = i
            self.register_option(option_name, None, False, 'database column name where this csv column will be imported')
