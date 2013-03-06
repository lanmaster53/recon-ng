import framework
# unique to module
import json
import textwrap

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', 'www.google.com', 'yes', 'target host')
        self.info = {
                     'Name': 'BuiltWith Server-side Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the BuiltWith API to identify server-side technologies.',
                     'Comments': []
                     }

    def module_run(self):
        host = self.options['host']['value']
        key = self.manage_key('builtwith', 'BuiltWith API key')
        if not key: return
        url = ' http://api.builtwith.com/v1/api.json'
        payload = {'key': key, 'lookup': host}
        try: resp = self.request(url, payload=payload)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if resp.json == None:
            self.error('Not a valid JSON response.')
            return
        if 'error' in resp.json:
            self.error(resp.json['error'])
            return
        
        if self.goptions['verbose']['value']:
            for item in resp.json['Technologies']:
                print self.ruler*50
                for tag in item:
                    self.output('%s: %s' % (tag, textwrap.fill(item[tag], 100, initial_indent='', subsequent_indent=self.spacer*2)))
            print self.ruler*50

        tags = ['web server', 'analytics', 'framework', 'server']
        tdata = []
        for item in resp.json['Technologies']:
            tag = item['Tag']
            if tag.lower() in tags:
                name = item['Name']
                tdata.append([tag.title(), name])

        if len(tdata) > 0:
            header = ['Tag', 'Name']
            tdata.insert(0, ['Profile URL', resp.json['ProfileUrl']])
            tdata.insert(0, header)
            self.table(tdata, True)
        else:
            self.output('No results found')
