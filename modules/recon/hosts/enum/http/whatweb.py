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
                     'Author': 'thrapt (thrapt@gmail.com) and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages WhatWeb.net to recognise web technologies being used.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                 ]
                     }

    def module_run(self):
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
                host, site = re.split(' \[\d\d\d\] ', site)
                tdata = [['Field', 'Value'], ['Host', host]]
                items = re.split(',\s*', site)
                flag = 0
                for item in items:
                    item = item.replace('][', ', ')
                    if '[' in item:
                        name, value = re.split('\s*\[', item)
                        if ']' in item:
                            value = value[:-1]
                        else:
                            flag = 1
                            continue
                    elif flag:
                        value = '%s, %s' % (value, item) if value else item
                        if ']' in item:
                            flag = 0
                            value = value[:-1]
                        else:
                            continue
                    else:
                        name = 'Unknown'
                        value = item
                    tdata.append([name.strip(), value.strip()])
                self.table(tdata, True)
