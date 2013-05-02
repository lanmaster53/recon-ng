import framework
# unique to module
import urllib
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.register_option('keywords', '', 'no', 'additional keywords to identify company')
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from Jigsaw.com and updates the \'contacts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        company_id = self.get_company_id()
        if company_id:
            contact_ids = self.get_contact_ids(company_id)
            if contact_ids:
                self.get_contacts(contact_ids)

    def get_company_id(self):
        self.output('Gathering Company IDs...')
        company_name = self.options['company']['value']
        all_companies = []
        page_cnt = 1
        params = '%s %s' % (company_name, self.options['keywords']['value'])
        url = 'http://www.jigsaw.com/FreeTextSearchCompany.xhtml'
        payload = {'opCode': 'search', 'freeText': params}
        while True:
            self.verbose('Query: %s?%s' % (url, urllib.urlencode(payload)))
            resp = self.request(url, payload=payload, redirect=False)
            if resp.status_code == 301:
                header = resp.headers['location']
                company_id = re.search('\/(\d+?)\/', resp.headers['location']).group(1)
                self.output('Unique Company Match Found: %s' % company_id)
                return company_id
            content = resp.text
            pattern = "href=./id(\d+?)/.+?>(.+?)<.+?\n.+?title='([\d,]+?)'"
            companies = re.findall(pattern, content)
            if not companies: break
            for company in companies:
                all_companies.append((company[0], company[1], company[2]))
            page_cnt += 1
            payload['rpage'] = str(page_cnt)
        if len(all_companies) == 0:
            self.output('No Company Matches Found.')
            return False
        else:
            id_len = len(max([str(x[0]) for x in all_companies], key=len))
            for company in all_companies:
                self.output('[%s] %s (%s contacts)' % (str(company[0]).ljust(id_len), company[1], company[2]))
            company_id = raw_input('Enter Company ID from list [%s - %s]: ' % (all_companies[0][1], all_companies[0][0]))
            if not company_id: company_id = all_companies[0][0]
            return company_id

    def get_contact_ids(self, company_id):
        self.output('Gathering Contact IDs for Company \'%s\'...' % (company_id))
        page_cnt = 1
        contact_ids = []
        url = 'http://www.jigsaw.com/SearchContact.xhtml'
        payload = {'companyId': company_id, 'opCode': 'showCompDir'}
        while True:
            payload['rpage'] = str(page_cnt)
            self.verbose('Query: %s?%s' % (url, urllib.urlencode(payload)))
            content = self.request(url, payload=payload).text
            pattern = "showContact\('(\d+?)'\)"
            contacts = re.findall(pattern, content)
            if not contacts: break
            contact_ids.extend(contacts)
            page_cnt += 1
        return contact_ids

    def get_contacts(self, contact_ids):
        self.output('Gathering Contacts...')
        cnt, tot = 0, 0
        for contact_id in contact_ids:
            url = 'http://www.jigsaw.com/BC.xhtml'
            payload = {'contactId': contact_id}
            content = self.request(url, payload=payload).text
            if 'Contact Not Found' in content: continue
            fname = self.html_unescape(re.search('<span id="firstname">(.+?)</span>', content).group(1))
            lname = self.html_unescape(re.search('<span id="lastname">(.+?)</span>', content).group(1))
            title = self.html_unescape(re.search('<span id="title" title=".*?">(.*?)</span>', content).group(1))
            city = self.html_unescape(re.search('<span id="city">(.+?)</span>', content).group(1)).title()
            state = re.search('<span id="state">(.+?)</span>', content)
            if state: state = self.html_unescape(state.group(1)).upper()
            region = []
            for item in [city, state]:
                if item: region.append(item)
            region = ', '.join(region)
            country = self.html_unescape(re.search('<span id="country">(.+?)</span>', content).group(1)).title()
            self.output('[%s] %s %s - %s (%s - %s)' % (contact_id, fname, lname, title, region, country))
            tot += 1
            cnt += self.add_contact(fname=fname, lname=lname, title=title, region=region, country=country)
        self.output('%d total contacts found.' % (tot))
        if cnt: self.alert('%d NEW contacts found!' % (cnt))
