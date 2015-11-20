from recon.core.module import BaseModule
from lxml.html import fromstring
import re
import sys

class Module(BaseModule):

    meta = {
        'name': 'Indeed Resume Crawl',
        'author': 'Tyler Rosonke (tyler@zonksec.com)',
        'description': 'Crawls Indeed.com for contacts and resumes. Adds name, title, and location to the contacts table and a link to the resume in the profiles table. Can only harvest the first 1,000 results. Result set changes, so running the same crawl mutiple times can produce new contacts. If the PAST_EMPS option is set to true, the module will crawl both current and past employees. Given a keyword, the module will only harvest contacts whose resumes contain the keyword. (e.g. Linux Admin)',
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
        'options': (
            ('past_emps', False, True, 'include past employees'),
            ('keyword', None, False, 'keyword to filter resumes'),
        ),
    }

    def module_run(self, companies):
        # step through all the companies
        for company in companies:
            # set up parameters
            past_emps = self.options['past_emps']
            self.keyword = self.options['keyword']
            self.company_flag = 'company' if past_emps else 'anycompany'
            # get count of resumes found and set cap if needed
            self.output('Crawling Indeed.com for \'%s\'...' % (company))
            base_url = 'http://www.indeed.com/resumes'
            payload = {'q':'%s:("%s")' % (self.company_flag, company)}
            if self.keyword:
                payload['q'] = '"%s" %s' % (self.keyword, payload['q'])
                self.output('Filtering for keyword "%s"' % (self.keyword))
            resp = self.request(base_url, method='GET', payload=payload)
            tree = fromstring(resp.text)
            while True:
                self.parse_page(tree)
                next_link = tree.find_class('instl confirm-nav next')
                if next_link:
                    next_url = base_url + next_link[0].attrib['href']
                    resp = self.request(next_url)
                    tree = fromstring(resp.text)
                    continue
                break

    def parse_page(self, tree):
        resultlist = tree.find_class('sre-content')
        for result in resultlist:
            fullname = result.find_class('app_link')[0].text.encode('ascii', 'ignore')
            firstname, middlename, lastname = self.parse_name(fullname)
            resumeurl = 'http://www.indeed.com' + result.find_class('app_link')[0].attrib['href']
            try:
                title = result.find_class('experience')[0].text_content()
            except:
                title = ''
            try:
                location = result.find_class('location')[0].text[2:]
            except: 
                location = ''
            # add results to contacts and profiles tables
            self.output('%s - %s' % (fullname, title))
            self.add_contacts(first_name=firstname, middle_name=middlename, last_name=lastname, title=title, region=location)
            self.add_profiles(username=fullname, resource='Indeed', url=resumeurl, category='resume')
