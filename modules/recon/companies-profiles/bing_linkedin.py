from recon.core.module import BaseModule
from io import StringIO
from lxml.html import fromstring
import re
import time

class Module(BaseModule):
    meta = {
        'name': 'Bing Linkedin Profile Harvester',
        'author':'Mike Larch and Brian Fehrman (@fullmetalcache)',
        'description': 'Harvests contacts from linkedin.com by querying Bing for Linkedin pages related to the given companies, parsing the profiles, and adding them to the \'profiles\' table',
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL ORDER BY company',
        'options': ( 
            ('limit', 2, False, 'number of pages to use from bing search'),
            ('previous', False, True, 'include previous employees'),
        ),
    }

    def module_run(self, companies):
        for company in companies:
            self.heading(company, level=0)
            urls = self.get_urls(company)
            
            num_urls = len(urls)
            for url_curr in urls:
                self.verbose('{0} URLs remaining.'.format(num_urls))
                self.get_info(company, url_curr)
                num_urls -= 1
    
    def get_urls(self, company):
        limit = self.options['limit']
        urls = []
        results = []
        
        base_query = 'site:linkedin.com instreamset:(url):"pub" -instreamset:(url):"dir" '
        
        query = base_query + '"' + company + '"'
        
        results = self.search_bing_api(query, limit)

        # iterate through results and add new urls
        for result in results:
            url = result['Url']
            if url not in urls:
                urls.append(url)
            
        return urls

    def get_info(self, company, url):
        time.sleep(1)
        self.verbose('Parsing \'%s\'...' % (url))
        
        resp = self.request(url)
            
        tree = fromstring(resp.text)
        
        company_found = self.parse_company(tree, resp.text, company)
        
        if company_found is None:
            self.error('No company found on profile page.')
            return

        # output the results
        self.alert('Probable match: %s' % url)
        
        username = self.get_username(url)
        
        if username is None:
            username = 'unknown'
        
        self.add_profiles(username=username, url=url, resource='linkedin', category='social', notes=company_found)
        
    def get_username(self, url):
        username = None
        
        try:
            url = url.split('/pub/')[1]
            username = url.split('/')[0]
        except IndexError:
            return None
            
        return username
                
    def parse_company(self, tree, resp, company):
        company_found = self.parse_company_exp(resp, company)
        
        if company_found is None:
            company_found = self.parse_company_tree(tree, company)
            
        return company_found
        

    def parse_company_exp(self, resp, company):
        company_found = None
        experiences = None
        previous = self.options['previous']
        try:
            experiences = resp.split('<div id="experience-', 1)[1]
            experiences = experiences.split('-view">', 1)[1]
            experiences = experiences.split('</div></div>')
            
        except IndexError:
            return None
            
        total = len(experiences)
        for idx, experience in enumerate(experiences):
            if idx == (total - 1):
                break
                
            experience = experience.split("</span>", 1)[0]
            exp_lower = experience.lower()
            if company.lower() in exp_lower:
                if 'present' in exp_lower or previous:
                    company_found = company
                    break
                        
        return company_found

    def parse_company_tree(self, tree, company):
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
        
        if company_found is not None:
            if company.lower() not in company_found.lower():
                company_found = None
        
        return company_found
