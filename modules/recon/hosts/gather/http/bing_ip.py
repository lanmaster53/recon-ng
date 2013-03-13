import framework
# unique to module
import urllib
import json
from urlparse import urlparse

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'Bing IP Neighbor Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Bing API and "ip:" advanced search operator to enumerate other virtual hosts sharing the same IP address.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def query_api(self, query):
        key = self.manage_key('bing', 'Bing API key')
        if not key: return
        url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/v1/Web'
        payload = {'Query': query, '$format': 'json'}
        results = []
        while True:
            resp = None
            self.verbose('URL: %s?%s' % (url, urllib.urlencode(payload)))
            try: resp = self.request(url, payload=payload, auth=(key, key))
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json == None:
                self.error('Invalid JSON response.\n%s' % (resp.text))
                continue
            results.extend(resp.json['d']['results'])
            if '__next' in resp.json['d']:
                payload['$skip'] = resp.json['d']['__next'].split('=')[-1]
            else:
                return results

    def module_run(self):
        addresses = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not addresses: return
        store = self.options['store']['value']

        cnt = 0
        hosts = []
        for address in addresses:
            query = '\'ip:%s\'' % (address)
            results = self.query_api(query)
            if type(results) != list: break
            if not results: self.verbose('No additional hosts discovered at the same IP address.')
            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts:
                    hosts.append(host)
                    self.output(host)
                    # add each host to the database
                    if store: cnt += self.add_host(host)

        self.output('%d total hosts found.' % (len(hosts)))
        if store and cnt: self.alert('%d NEW hosts found!' % (cnt))
