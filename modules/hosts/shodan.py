import framework
import __builtin__
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'restrict': False,
                        'requests': 1
                        }
        self.info = {
                     'Name': 'Shodan Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'restrict\' option limits the number of API requests to \'requests\' in order to prevent API query exhaustion.'
                                  ]
                     }

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        subs = []
        key = self.manage_key('shodan', 'Shodan API key')
        if not key: return
        url = 'http://www.shodanhq.com/api/search'
        query = 'hostname:%s' % (domain)
        payload = {'q': query, 'key': key}
        cnt = 0
        page = 1
        # loop until no results are returned
        while True:
            new = False
            resp = None
            try: resp = self.request(url, payload=payload)
            except KeyboardInterrupt:
                print ''
            except Exception as e:
                self.error(e.__str__())
            if not resp: break
            # resp.json will not work here
            jsonstr = resp.text
            try: jsonobj = json.loads(jsonstr)
            except ValueError as e:
                self.error(e.__str__())
                break
            try: results = jsonobj['matches']
            except KeyError: break
            for result in results:
                if not 'hostnames' in result.keys(): continue
                hostnames = result['hostnames']
                for hostname in hostnames:
                    site = '.'.join(hostname.split('.')[:-2])
                    if site and site not in subs:
                        subs.append(site)
                        new = True
                        host = '%s.%s' % (site, domain)
                        self.output('%s' % (host))
                        cnt += self.add_host(host)
            if self.options['restrict']:
                if page == self.options['requests']: break
            if not new: break
            page += 1
            payload['page'] = str(page)
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))