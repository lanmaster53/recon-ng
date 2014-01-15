import framework
# unique to module
import json
import textwrap

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', self.global_options['domain'], 'yes', 'target host')
        self.info = {
                     'Name': 'BuiltWith Server-side Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the BuiltWith API to identify server-side technologies.',
                     'Comments': []
                     }

    def module_run(self):
        key = self.get_key('builtwith_api')
        host = self.options['host']
        url = ' http://api.builtwith.com/v2/api.json'
        payload = {'key': key, 'lookup': host}
        resp = self.request(url, payload=payload)
        if 'error' in resp.json:
            self.error(resp.json['error'])
            return
        for path in resp.json['Paths']:
            domain = path['Domain']
            subdomain = path['SubDomain']
            fqdn = '.'.join([x for x in [subdomain, domain] if x])
            self.alert(fqdn)
            if self.global_options['verbose']:
                for item in path['Technologies']:
                    print(self.ruler*50)
                    for tag in item:
                        self.output('%s: %s' % (tag, textwrap.fill(item[tag], 100, initial_indent='', subsequent_indent=self.spacer*2)))
                print(self.ruler*50)

            tags = ['web server', 'analytics', 'framework', 'server']
            tdata = []
            for item in path['Technologies']:
                tag = item['Tag']
                if tag.lower() in tags:
                    name = item['Name']
                    tdata.append([tag.title(), name])

            if len(tdata) > 0:
                header = ['Tag', 'Name']
                tdata.insert(0, ['Profile URL', fqdn])
                tdata.insert(0, header)
                self.table(tdata, True)
