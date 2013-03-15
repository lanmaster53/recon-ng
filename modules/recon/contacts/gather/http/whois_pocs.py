import framework
# unique to module
from urlparse import urlparse

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'Whois POC Harvester',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the ARIN Whois RWS to harvest POC data from whois queries for the given IP addresses.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        addresses = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not addresses: return
        store = self.options['store']['value']

        cnt = 0
        new = 0
        for address in addresses:
            url = 'http://whois.arin.net/rest/ip/%s/pft.json' % (address)
            self.verbose('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (address, resp.text))
                continue
            for poc in jsonobj['ns4:pft']['poc']:
                title = 'Whois contact for \'%s\'' % (poc['@relatedDescription'])
                city = poc['city']['$'].title()
                country = poc['iso3166-1']['name']['$'].title()
                fname = poc['firstName']['$']
                lname = poc['lastName']['$']
                email = poc['emails']['email']['$']
                state = poc['iso3166-2']['$'].title()
                region = '%s, %s' % (city, state)
                self.output('%s %s (%s) - %s (%s - %s)' % (fname, lname, email, title, region, country))
                if store: new += self.add_contact(fname=fname, lname=lname, email=email, title=title, region=region, country=country)
                cnt += 1
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
