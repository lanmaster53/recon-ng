from recon.core.module import BaseModule
from io import StringIO
from lxml.html import fromstring
import re
import time

class Module(BaseModule):
    
    meta = {
        'name': 'Linkedin Profile Crawler',
        'author': 'Mike Larch and Brian Fehrman (@fullmetalcache)',
        'description': 'Harvests profiles from linkedin.com by visting known profiles, crawling the "Viewers of this profile also viewed", parsing the pages, and adding new profiles to the \'profiles\' table.',
        'query': 'SELECT DISTINCT url FROM profiles WHERE url IS NOT NULL AND resource LIKE \'linkedin\'',
        'options': (
            ('previous', False, True, 'include previous employees'),
        ),
    }
        
    def module_run(self, urls):
        query = 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL'
        companies = [x[0] for x in self.query(query)]
        
        if companies is None:
            self.error('No companies found in \'companies\' table')
            return
        
        num_urls = len(urls)
        urls_queued = urls[:]
        for url_curr in urls:
            self.get_info(companies, url_curr, urls_queued, num_urls)
            num_urls -= 1

    def get_info(self, companies, url, urls_queued, num_urls):
        temp_urls = [url]

        while 0 < len(temp_urls): 
            temp_url = temp_urls.pop(0)
            urls_remaining = num_urls + len(temp_urls) + 1
            self.verbose('{0} URLs remaining.'.format(urls_remaining))
            time.sleep(1)
            self.verbose('Crawling \'%s\'...' % (temp_url))
            
            retries = 5
            resp = None
            
            while 0 < retries:
                try:
                    retries -= 1
                    resp = self.request(temp_url)
                    break
                except Exception as e:
                    self.error('{0}, {1} retries left'.format(e, retries))
            
            if resp is None:
                continue
                
            tree = fromstring(resp.text)
            
            company_found = self.parse_company(tree, resp.text, companies)
            
            if company_found is None:
                self.error('No company matches found on the page or person is not a current employee')
                continue

            # output the results
            self.alert('Probable match: %s' % temp_url)
            
            username = self.get_username(temp_url)
            
            if username is None:
                username = 'unknown'
            
            self.add_profiles(username=username, url=temp_url, resource='linkedin', category='social', notes=company_found)
            
            parsed_urls = None
            try:
                parsed_urls = tree.xpath('//li[@class="with-photo"]/a/@href')
                if not parsed_urls:
                    parsed_urls = tree.xpath('//div[@class="insights-browse-map"]/ul/li/a/@href')
                    new_urls = [x for x in parsed_urls]
                    
                    for idx, url_splt in enumerate(new_urls):
                        new_urls[idx] = url_splt.split('?',1)[0]
                        
                    for new_url in new_urls:
                        if (new_url not in temp_urls) and (new_url not in urls_queued):
                            temp_urls.append(new_url)
                            urls_queued.append(new_url)
            except IndexError:
                continue
        
    def get_username(self, url):
        username = None
        
        try:
            url = url.split('/pub/')[1]
            username = url.split('/')[0]
        except IndexError:
            return None
            
        return username
                
    def parse_company(self, tree, resp, companies):
        company_found = self.parse_company_exp(resp, companies)
        
        if company_found is None:
            company_found = self.parse_company_tree(tree, companies)
            
        return company_found

    def parse_company_exp(self, resp, companies):
        company_found = None
        experiences = None
        previous = self.options['previous']
        try:
            experiences = resp.split('<div id="experience-', 1)[1]
            experiences = experiences.split('-view">', 1)[1]
            experiences = experiences.split('<script>', 1)[0]
            experiences = experiences.split('</div></div>')
        except IndexError:
            return None
            
        total = len(experiences)
        for idx, experience in enumerate(experiences):
            if idx == (total - 1):
                break
                
            try:
                time_exp = experience.split('date-locale',1)[1]
                time_exp = time_exp.split('</span>', 1)[0]
            except IndexError:
                continue

            time_exp = time_exp.lower()
            experience = experience.lower()

            for company in companies:
                if (company.lower() in experience) or (company.replace(" ","").lower() in experience):
                    if 'present' in time_exp or previous:
                        self.verbose(company)
                        company_found = company
                        break
                        
            if company_found is not None:
                break
                        
        return company_found

    def parse_company_tree(self, tree, companies):
        company_found = None
        
        try: company_found = tree.xpath('//ul[@class="current"]/li/a/span[@class="org summary"]/text()')[0]
        except IndexError:
            try: company_found = tree.xpath('//ul[@class="current"]/li/text()')[1].strip()
            except IndexError:
                try: company_found = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip().split(" at ",1)[1]
                except IndexError:
                    try: company_found = tree.xpath('//p[@class="title "]/text()')[0].strip().split(" at ",1)[1]
                    except IndexError:
                        try: company_found = tree.xpath('//tr[@id="overview-summary-current"]/td/ol/li/a/text()')[0]
                        except:
                            pass
                            
        isFound = False
        
        if (company_found is not None):
            for company in companies:
                if company.lower() in company_found.lower():
                    isFound = True
                    break
        
        if isFound == False:
            company_found = None                
        
        return company_found
