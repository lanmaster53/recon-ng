import module
# unique to module
from urlparse import urlparse
import netblock
import urllib

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT company FROM companies WHERE company IS NOT NULL')
        #self.register_option('search', None, True, 'company search string')
        self.info = {
            'Name': 'Whois Data Miner',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Uses the ARIN Whois RWS to harvest companies, locations, netblocks, and contacts associated the given company search string. Updates the respective tables with the results.',
            'Comments': [
                'Wildcard searches are allowed using the "*" character.',
                'Validate results of the SEARCH string with this URL: http://whois.arin.net/rest/orgs;name=<SEARCH>',
            ]
        }

    def module_run(self, searches):
        #search = self.options['search']
        headers = {'Accept': 'application/json'}
        for search in searches:
            url = 'http://whois.arin.net/rest/orgs;name=%s' % (urllib.quote(search))
            orgs = self._request(url, headers, 'orgs', 'orgRef')
            for org in orgs:
                self.heading(org['@name'], level=0)
                url = org['$']
                resp = self.request(url, headers=headers)
                # add company
                self.add_companies(company=org['@name'])
                # add location
                address = ', '.join((
                    # street address
                    self._enum_ref(resp.json['org']['streetAddress']['line'])[-1]['$'].title(),
                    # city
                    resp.json['org']['city']['$'].title(),
                    # state, postal code or country
                    '%s %s' % (resp.json['org']['iso3166-2']['$'].upper(), resp.json['org']['postalCode']['$']) if 'iso3166-2' in resp.json['org'] else resp.json['org']['iso3166-1']['name']['$'].title(),
                )).strip()
                self.output('Location: %s' % (address))
                self.add_locations(street_address=address)
                # add netblocks
                url = 'http://whois.arin.net/rest/org/%s/nets' % (org['@handle'])
                nets = self._request(url, headers, 'nets', 'netRef')
                for net in nets:
                    try:
                        begin = netblock.strtoip(net['@startAddress'])
                        end = netblock.strtoip(net['@endAddress'])
                        blocks = netblock.lhcidrs(begin, end)
                    except ValueError:
                        self.alert('IPv6 ranges not supported: %s-%s' % (net['@startAddress'], net['@endAddress']))
                        continue
                    for block in blocks:
                        ip = netblock.iptostr(block[0])
                        cidr = '%s/%s' % (ip, str(block[1]))
                        self.output('Netblock: %s' % (cidr))
                        self.add_netblocks(netblock=cidr)
                # add contacts
                url = 'http://whois.arin.net/rest/org/%s/pocs' % (org['@handle'])
                pocLinks = self._request(url, headers, 'pocs', 'pocLinkRef')
                for pocLink in pocLinks:
                    url = pocLink['$']
                    resp = self.request(url, headers=headers)
                    poc = resp.json['poc']
                    emails = self._enum_ref(poc['emails']['email'])
                    for email in emails:
                        fname = poc['firstName']['$'] if 'firstName' in poc else None
                        lname = poc['lastName']['$']
                        name = ' '.join([x for x in [fname, lname] if x])
                        email = email['$']
                        title = 'Whois contact (%s)' % (pocLink['@description'])
                        city = poc['city']['$'].title()
                        state = poc['iso3166-2']['$'].upper() if 'iso3166-2' in poc else None
                        region = ', '.join([x for x in [city, state] if x])
                        country = poc['iso3166-1']['name']['$'].title()
                        self.output('Contact: %s (%s) - %s (%s - %s)' % (name, email, title, region, country))
                        self.add_contacts(first_name=fname, last_name=lname, email=email, title=title, region=region, country=country)

    def _request(self, url, headers, grp, ref):
        self.verbose('URL: %s' % url)
        resp = self.request(url, headers=headers)
        strs = [
            'No related resources were found for the handle provided.',
            'Your search did not yield any results.'
        ]
        if any(x in resp.text for x in strs):
            self.output('No %s found.' % (grp.upper()))
            return []
        return self._enum_ref(resp.json[grp][ref])

    def _enum_ref(self, ref):
        if type(ref) == list:
            objs = [x for x in ref]
        else:
            objs = [ref]
        return objs
