import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of module input')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
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
            
            try: resp = self.request(url, method='POST', payload=payload)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            content = resp.text
            sites = content.strip().split('\n')
            for site in sites:
                host = site[:site.index(' [')]
                site = site.split('] ', 1)[1]
                items = site.split(', ')

                values = [['Field', 'Value'], ['Host', host]]
                for item in items:
                    if '[' in item:
                        split = item.split('[')
                        key = split[0]
                        value = split[1][:-1]
                        values.append([key, value])
                    else:
                        values.append(['', item])

                self.table(values, True)