import _cmd
import __builtin__
# unique to module
import urllib
import re

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'company': __builtin__.company,
                        'key_words': '',
                        'verbose': False
                        }

    def do_info(self, params):
        print ''
        print 'Harvests contacts from Jigsaw.com.'
        print ''

    def do_run(self, params):
        company_id = self.get_company_id()
        if company_id: self.get_contacts(company_id)

    def get_company_id(self):
        company_name = self.options['company']
        all_companies = []
        page_cnt = 1
        params = '%s %s' % (company_name, self.options['key_words'])
        base_url = 'http://www.jigsaw.com/FreeTextSearchCompany.xhtml?opCode=search&freeText=%s' % (urllib.quote_plus(params))
        url = base_url
        while True:
            if self.options['verbose']: print '[Query] %s' % url
            try:
                content = urllib.urlopen(url).read()
            except KeyboardInterrupt:
                break
            pattern = "href=./id(\d+?)/.+?>(.+?)<.+?\n.+?title='([\d,]+?)'"
            companies = re.findall(pattern, content)
            if not companies:
                if content.find('did not match any results') == -1 and page_cnt == 1:
                    pattern_id = '<a href="/id(\d+?)/.+?">'
                    pattern_name = 'pageTitle.>(.+?)<'
                    pattern_cnt = 'contactCount.+>\s+(\d+)\sContacts'
                    if content.find('Create a wiki') != -1:
                        pattern_id = '<a href="/.+?companyId=(\d+?)">'
                    company_id = re.findall(pattern_id, content)[0]
                    company_name = re.findall(pattern_name, content)[0]
                    contact_cnt = re.findall(pattern_cnt, content)[0]
                    all_companies.append((company_id, company_name, contact_cnt))
                break
            for company in companies:
                all_companies.append((company[0], company[1], company[2]))
            page_cnt += 1
            url = base_url + '&rpage=%d' % (page_cnt)
        if len(all_companies) == 0:
            print '[!] No Company Matches Found.'
            return False
        else:
            for company in all_companies:
                print '[Company] %s %s (%s contacts)' % (company[0], company[1], company[2])
            if len(all_companies) > 1:
                try: company_id = raw_input('Enter Company ID from list [%s]: ' % (all_companies[0][0]))
                except KeyboardInterrupt:
                    sys.stdout.write('\n')
                    company_id = ''
                if not company_id: company_id = all_companies[0][0]
            else:
                company_id = all_companies[0][0]
                print '[-] Unique Company Match Found: %s' % company_id
            return company_id

    def get_contacts(self, company_id):
        verbose = self.options['verbose']
        page_cnt = 1
        base_url = 'http://www.jigsaw.com/SearchContact.xhtml?companyId=%s&opCode=showCompDir' % (company_id)
        url = base_url
        while True:
            url = base_url + '&rpage=%d' % (page_cnt)
            if verbose: print '[Query] %s' % url
            try: content = urllib.urlopen(url).read()
            except KeyboardInterrupt: break
            pattern = "<span.+?>(.+?)</span>.+?\n.+?href.+?\('(\d+?)'\)>(.+?)<"
            contacts = re.findall(pattern, content)
            if not contacts: break
            for contact in contacts:
                title = contact[0]
                contact_id = contact[1]
                if contact[2].find('...') != -1:
                    url = 'http://www.jigsaw.com/BC.xhtml?contactId=%s' % contact_id
                    try: content = urllib.urlopen(url).read()
                    except KeyboardInterrupt: break
                    pattern = '<span id="firstname">(.+?)</span>.*?<span id="lastname">(.+?)</span>'
                    names = re.findall(pattern, content)
                    fname = self.unescape(names[0][0])
                    lname = self.unescape(names[0][1])
                else:
                    fname = self.unescape(contact[2].split(',')[1].strip())
                    lname = self.unescape(contact[2].split(',')[0].strip())
                print '[Contact] %s %s - %s' % (fname, lname, title)
                self.add_contact(fname, lname, title)
            page_cnt += 1