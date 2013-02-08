import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'WhatWeb Web Technologies scan',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Leverages WhatWeb.net to recognise web technologies being used.',
                     'Comments': [
                                  'Source options: db, <hostname>, <path/to/infile>',
                                 ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.whatweb()

    def whatweb(self):
        verbose = self.options['verbose']['value']

        # handle sources
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return
        
        for host in hosts:
            url = 'http://whatweb.net/whatweb.php'
            payload = {'target': host }
            if verbose: self.output('URL: %s' % url)
            
            try: resp = self.request(url, method='POST', payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            
            if not resp: break
            
            # The output from the server is a little messy.
            # If we have a redirect, entries will be separated by line breaks. We want the last entry.
            # After that we have the name of the host and the http code, we don't need that, so we split it.
            # Then it's a comma separated list with items that may or not have values inside brackets.
            # We separate everything with a regexp and print in a table

            content = resp.text
            if '\n' in content: content = content.strip().split('\n')[-1]
            content = content.split('] ', 1)[1]

            contents = content.split(', ')
            
            values = []
            for item in contents:
                if '[' in item:
                    split = item.split('[')
                    key = split[0]
                    value = split[1][:-1]
                    values.append([key, value])
                else:
                    values.append([item, ''])

            self.table(values, False)