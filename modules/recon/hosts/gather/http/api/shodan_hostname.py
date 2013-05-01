import framework
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('restrict', False, 'yes', 'limit number of api requests to \'requests\'')
        self.register_option('requests', 1, 'yes', 'maximum number of api requets to make')
        self.info = {
                     'Name': 'Shodan Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'restrict\' option limits the number of API requests to \'requests\' in order to prevent API query exhaustion.'
                                  ]
                     }

    def module_run(self):
        key = self.get_key('shodan_api')
        domain = self.options['domain']['value']
        subs = []
        url = 'http://www.shodanhq.com/api/search'
        query = 'hostname:%s' % (domain)
        payload = {'q': query, 'key': key}
        cnt = 0
        page = 1
        # loop until no results are returned
        while True:
            new = False
            resp = None
            resp = self.request(url, payload=payload)
            if resp.json == None:
                self.error('Invalid JSON response.\n%s' % (resp.text))
                break
            if 'error' in resp.json:
                self.error(resp.json['error'])
                break
            # returns an empty json when no matches are found
            if not 'matches' in resp.json:
                break
            for result in resp.json['matches']:
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
            if self.options['restrict']['value']:
                if page == self.options['requests']['value']: break
            if not new: break
            page += 1
            payload['page'] = str(page)
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
