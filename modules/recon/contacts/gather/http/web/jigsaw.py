import framework
# unique to module
from cookielib import CookieJar
import urllib
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.register_option('keywords', None, 'no', 'additional keywords to identify company')
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from Jigsaw.com and updates the \'contacts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        self.cookiejar = CookieJar()
        company_id = self.get_company_id()
        if company_id:
            contact_ids = self.get_contact_ids(company_id)
            if contact_ids:
                self.get_contacts(contact_ids)

    def test(self, var1):
        import math
        var_str = "" + str(var1)
        var_arr = [int(x) for x in list(var_str)]
        LastDig = var_arr[-1]
        var_arr.sort()
        minDig  = sorted(var_arr)[0]
        subvar1 = (2*(var_arr[2]))+(var_arr[1]*1)
        subvar2 = str(2*var_arr[2])+str(var_arr[1])
        my_pow  = int(math.pow(((var_arr[0]*1)+2),var_arr[1]))
        x       = (var1*3+subvar1)*1
        y       = int(math.cos(math.pi*int(subvar2)))
        answer  = x*y
        answer -= my_pow*1
        answer += (minDig*1)-(LastDig*1)
        answer  = str(answer)+subvar2
        return answer

    def get_headers(self, content):
        Challenge = int(re.search('Challenge=(\d*);', content).group(1))
        ChallengeId = int(re.search('ChallengeId=(\d*);', content).group(1))
        y = self.test(Challenge)
        headers = {}
        headers['X-AA-Challenge-ID'] = ChallengeId
        headers['X-AA-Challenge-Result'] = y
        headers['X-AA-Challenge'] = Challenge
        headers['Content-Type'] = 'text/plain'
        headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:23.0) Gecko/20100101 Firefox/23.0'
        return headers

    def get_company_id(self):
        self.output('Gathering Company IDs...')
        company_name = self.options['company']['value']
        keywords = self.options['keywords']['value']
        all_companies = []
        page_cnt = 1
        params = ' '.join([x for x in [company_name, keywords] if x])
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
            resp = self.request(url, payload=payload, cookiejar=self.cookiejar)
            content = resp.text
            if 'use of automated scripts to access jigsaw.com is prohibited' in content:
                self.verbose('Fetching BotMitigationCookie...')
                headers = self.get_headers(content)
                temp_url = '%s?%s' % (url, urllib.urlencode(payload))
                resp = self.request(temp_url, method='POST', headers=headers, cookiejar=self.cookiejar)
                self.cookiejar = resp.cookiejar
                continue
            if 'Refresh' in resp.headers:
                continue
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
            content = self.request(url, payload=payload, cookiejar=self.cookiejar).text
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
