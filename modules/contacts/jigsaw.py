import framework
# unique to module
import urllib
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.register_option('keywords', '', 'no', 'additional keywords to identify company')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Classification': '%s Reconnaissance' % (self.classify.title()),
                     'Description': 'Harvests contacts from Jigsaw.com. This module updates the \'contacts\' table of the database with the results.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
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
            if self.options['verbose']['value']: self.output('Query: %s?%s' % (url, urllib.urlencode(payload)))
            try: content = self.request(url, payload=payload).text
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                break
            pattern = "href=./id(\d+?)/.+?>(.+?)<.+?\n.+?title='([\d,]+?)'"
            companies = re.findall(pattern, content)
            if not companies:
                if not 'did not match any results' in content and page_cnt == 1:
                    pattern_id = '<a href="/id(\d+?)/.+?">'
                    if 'Create a wiki' in content:
                        pattern_id = '<a href="/.+?companyId=(\d+?)">'
                    pattern_name = 'pageTitle.>(.+?)<'
                    pattern_cnt = 'contactCount.+>\s+([,\d]+)\sContacts'
                    company_id = re.findall(pattern_id, content)[0]
                    company_name = re.findall(pattern_name, content)[0]
                    contact_cnt = re.findall(pattern_cnt, content)[0]
                    all_companies.append((company_id, company_name, contact_cnt))
                break
            for company in companies:
                all_companies.append((company[0], company[1], company[2]))
            page_cnt += 1
            payload['rpage'] = str(page_cnt)
        if len(all_companies) == 0:
            self.output('No Company Matches Found.')
            return False
        else:
            for company in all_companies:
                self.output('%s %s (%s contacts)' % (company[0], company[1], company[2]))
            if len(all_companies) > 1:
                try:
                    company_id = raw_input('Enter Company ID from list [%s]: ' % (all_companies[0][0]))
                    if not company_id: company_id = all_companies[0][0]
                except KeyboardInterrupt:
                    print ''
                    company_id = ''
            else:
                company_id = all_companies[0][0]
                self.output('Unique Company Match Found: %s' % company_id)
            return company_id

    def get_contact_ids(self, company_id):
        self.output('Gathering Contact IDs for Company \'%s\'...' % (company_id))
        page_cnt = 1
        contact_ids = []
        url = 'http://www.jigsaw.com/SearchContact.xhtml'
        payload = {'companyId': company_id, 'opCode': 'showCompDir'}
        while True:
            payload['rpage'] = str(page_cnt)
            if self.options['verbose']['value']: self.output('Query: %s?%s' % (url, urllib.urlencode(payload)))
            try: content = self.request(url, payload=payload).text
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                break
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
            try: content = self.request(url, payload=payload).text
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                break
            if 'Contact Not Found' in content: continue
            pattern = '<span id="firstname">(.+?)</span>.*?<span id="lastname">(.+?)</span>'
            names = re.findall(pattern, content)
            fname = self.unescape(names[0][0])
            lname = self.unescape(names[0][1])
            pattern = '<span id="title" title=".*?">(.*?)</span>'
            title = self.unescape(re.findall(pattern, content)[0])
            self.output('%s %s - %s' % (fname, lname, title))
            tot += 1
            cnt += self.add_contact(fname, lname, title)
        self.output('%d total contacts found.' % (tot))
        if cnt: self.alert('%d NEW contacts found!' % (cnt))