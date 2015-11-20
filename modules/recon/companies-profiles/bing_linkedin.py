from recon.core.module import BaseModule
from recon.utils.linkedin import parse_username, parse_company, perform_login
from lxml.html import fromstring
import time

class Module(BaseModule):

    meta = {
        'name': 'Bing Linkedin Profile Harvester',
        'author':'Mike Larch and Brian Fehrman (@fullmetalcache)',
        'description': 'Harvests profiles from linkedin.com by querying Bing for Linkedin pages related to the given companies, parsing the profiles, and adding them to the \'profiles\' table.',
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
        'options': ( 
            ('limit', 2, True, 'number of pages to use from bing search (0 = unlimited)'),
            ('previous', False, True, 'include previous employees'),
        ),
    }

    def module_run(self, companies):
        for company in companies:
            self.heading(company, level=0)
            urls = self.get_urls(company)
            num_urls = len(urls)
            cookiej = None
            for url in urls:
                self.verbose('{0} URLs remaining.'.format(num_urls))
                cookiej = self.get_info(company, url, cookiej)
                num_urls -= 1

    def get_urls(self, company):
        urls = []
        results = []
        base_query = 'site:linkedin.com instreamset:(url):"pub" -instreamset:(url):"dir"'
        query = '%s "%s"' % (base_query, company)
        results = self.search_bing_api(query, self.options['limit'])
        # iterate through results and add new urls
        for result in results:
            url = result['Url']
            if url not in urls:
                urls.append(url)
        return urls

    def get_info(self, company, url, cookiej):
        time.sleep(0.333)
        self.verbose('Parsing \'%s\'...' % (url))
        retries = 5
        resp = None
        resp_text = None
        while 0 < retries:
            try:
                retries -= 1
                resp = self.request(url, cookiejar=cookiej)
                resp_text = resp.text
                if 'D8E90337EA is the' in resp_text:
                    self.verbose('Linkedin is limiting profile views, try logging in or re-login with a new account')
                    cookiej = perform_login()
                    retries += 1
                    continue
                break
            except Exception as e:
                self.error('{0}, {1} retries left'.format(e, retries))
        if resp_text is None:
            return cookiej
        tree = fromstring(resp_text)
        company_found = parse_company(tree, resp_text, company, self.options['previous'])
        if company_found is None:
            self.error('No company found on profile page.')
            return cookiej
        # output the results
        self.alert('Probable match: %s' % url)
        username = parse_username(url) or 'unknown'
        self.add_profiles(username=username, url=url, resource='linkedin', category='social', notes=company_found)
        return cookiej
