import framework
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'WhatWeb Web Technologies scan',
                     'Author': 'thrapt (thrapt@gmail.com) and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages WhatWeb.net to determine the web technologies in use on the given host(s).',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                 ]
                     }

    def module_run(self):
        # handle sources
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        
        url = 'http://whatweb.net/whatweb.php'
        for host in hosts:
            payload = {'target': host, 'format': 'json' }
            resp = self.request(url, method='POST', payload=payload)

            # parse returned json objects
            jsonobj = resp.json
            if jsonobj == None and resp.text:
                jsonobjs = [json.loads(x) for x in resp.text.strip().split('\n')]
            else:
                jsonobjs = [jsonobj]

            # output data
            for jsonobj in jsonobjs:
                tdata = [['Plugin', 'String'],['Target', jsonobj['target']]]
                for plugin in jsonobj['plugins']:
                    if 'string' in jsonobj['plugins'][plugin]:
                        value = ', '.join(jsonobj['plugins'][plugin]['string'])
                        tdata.append([plugin, value])
                if tdata: self.table(tdata, header=True)
