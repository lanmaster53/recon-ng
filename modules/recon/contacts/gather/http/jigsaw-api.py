import framework
# unique to module
import urllib
import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.register_option('keywords', '', 'no', 'additional keywords to identify company')
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from the Jigsaw.com API and updates the \'contacts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        self.api_key = self.manage_key('jigsaw_key', 'Jigsaw API Key')
        if not self.api_key: return
        company_id = self.get_company_id()
        if company_id:
            self.get_contacts(company_id)

    def get_company_id(self):
        self.output('Gathering Company IDs...')
        company_name = self.options['company']['value']
        all_companies = []
        cnt = 0
        size = 50
        params = '%s %s' % (company_name, self.options['keywords']['value'])
        url = 'https://www.jigsaw.com/rest/searchCompany.json'
        while True:
            payload = {'token': self.api_key, 'name': params, 'offset': cnt, 'pageSize': size}
            self.verbose('Query: %s?%s' % (url, urllib.urlencode(payload)))
            try: resp = self.request(url, payload=payload, redirect=False)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            jsonobj = resp.json
            if jsonobj['totalHits'] == 0:
                self.output('No Company Matches Found.')
                return
            else:
                companies = jsonobj['companies']
                for company in companies:
                    if company['activeContacts'] > 0:
                        location = '%s, %s, %s' % (company['city'], company['state'], company['country'])
                        all_companies.append((company['companyId'], company['name'], company['activeContacts'], location))
                cnt += size
                if cnt > jsonobj['totalHits']: break
                # jigsaw rate limits requests per second to the api
                time.sleep(.25)
        if len(all_companies) == 1:
            company_id = all_companies[0][0]
            self.output('Unique Company Match Found: %s' % company_id)
            return company_id
        id_len = len(max([str(x[0]) for x in all_companies], key=len))
        for company in all_companies:
            self.output('%s %s - %s (%s contacts)' % (str(company[0]).ljust(id_len), company[1], company[3], company[2]))
        try:
            company_id = raw_input('Enter Company ID from list [%s - %s]: ' % (all_companies[0][1], all_companies[0][0]))
            if not company_id: company_id = all_companies[0][0]
            return company_id
        except KeyboardInterrupt:
            print ''
            return

    def get_contacts(self, company_id):
        self.output('Gathering Contacts...')
        tot = 0
        cnt = 0
        new = 0
        size = 100
        url = 'https://www.jigsaw.com/rest/searchContact.json'
        while True:
            payload = {'token': self.api_key, 'companyId': company_id, 'offset': cnt, 'pageSize': size}
            try: resp = self.request(url, payload=payload, redirect=False)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            jsonobj = resp.json
            for contact in jsonobj['contacts']:
                fname = contact['firstname']
                lname = contact['lastname']
                title = self.unescape(contact['title'])
                city = contact['city']
                state = contact['state']
                region = []
                for item in [city, state]:
                    if item: region.append(item.title())
                region = ', '.join(region)
                country = contact['country']
                self.output('%s %s - %s (%s - %s)' % (fname, lname, title, region, country))
                new += self.add_contact(fname=fname, lname=lname, title=title, region=region, country=country)
                tot += 1
            cnt += size
            if cnt > jsonobj['totalHits']: break
            # jigsaw rate limits requests per second to the api
            time.sleep(.25)
        self.output('%d total contacts found.' % (tot))
        if cnt: self.alert('%d NEW contacts found!' % (new))
