from recon.core.module import BaseModule
from recon.utils import netblock
from urlparse import urlparse
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Whois Data Miner',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the ARIN Whois RWS to harvest companies, locations, netblocks, and contacts associated with the given company search string. Updates the respective tables with the results.',
        'comments': (
            'Wildcard searches are allowed using the "*" character.',
            'Validate results of the SEARCH string with these URLs:',
            '\thttp://whois.arin.net/rest/orgs;name=<SEARCH>',
            '\thttp://whois.arin.net/rest/customers;name=<SEARCH>',
        ),
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
    }

    def module_run(self, searches):
        headers = {'Accept': 'application/json'}
        for search in searches:
            for rtype in ('org', 'customer'):
                url = 'http://whois.arin.net/rest/%ss;name=%s' % (rtype, urllib.quote(search))
                entities = self._request(url, headers, rtype+'s', rtype+'Ref')
                for entity in entities:
                    self.heading(entity['@name'], level=0)
                    url = entity['$']
                    resp = self.request(url, headers=headers)
                    # add company
                    self.add_companies(company=entity['@name'], description=rtype)
                    # add location
                    address = ', '.join((
                        # street address
                        self._enum_ref(resp.json[rtype]['streetAddress']['line'])[-1]['$'].title(),
                        # city
                        resp.json[rtype]['city']['$'].title(),
                        # state, postal code or country
                        '%s %s' % (resp.json[rtype]['iso3166-2']['$'].upper(), resp.json[rtype]['postalCode']['$']) if 'iso3166-2' in resp.json[rtype] else resp.json[rtype]['iso3166-1']['name']['$'].title(),
                    )).strip()
                    self.output('Location: %s' % (address))
                    self.add_locations(street_address=address)
                    # add netblocks
                    url = 'http://whois.arin.net/rest/%s/%s/nets' % (rtype, entity['@handle'])
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
                    url = 'http://whois.arin.net/rest/%s/%s/pocs' % (rtype, entity['@handle'])
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
        if any(x in resp.text for x in strs) or ref not in resp.json[grp]:
            self.output('No %s found.' % (grp.upper()))
            return []
        return self._enum_ref(resp.json[grp][ref])

    def _enum_ref(self, ref):
        if type(ref) == list:
            objs = [x for x in ref]
        else:
            objs = [ref]
        return objs
