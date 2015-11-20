from recon.core.module import BaseModule
from recon.utils.linkedin import parse_username, parse_company, parse_also_viewed, perform_login
from lxml.html import fromstring
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
        cookiej = None
        for url in urls:
            cookiej =  self.get_info(companies, url, urls_queued, num_urls, cookiej)
            num_urls -= 1

    def get_info(self, companies, url, urls_queued, num_urls, cookiej):
        temp_urls = [url]
        while 0 < len(temp_urls):
            temp_url = temp_urls.pop(0)
            urls_remaining = num_urls + len(temp_urls) + 1
            self.verbose('{0} URLs remaining.'.format(urls_remaining))
            time.sleep(0.333)
            self.verbose('Crawling \'%s\'...' % (temp_url))
            retries = 5
            resp = None
            resp_text = None
            while 0 < retries:
                try:
                    retries -= 1
                    resp = self.request(temp_url, cookiejar=cookiej)
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
                continue
            tree = fromstring(resp_text)
            for company in companies:
                company_found = parse_company(tree, resp_text, company, self.options['previous'])
                if company_found is not None:
                    break
            if company_found is None:
                self.error('No company matches found on the page or person is not a current employee')
                continue
            # output the results
            self.alert('Probable match: %s' % temp_url)
            username = parse_username(temp_url) or 'unknown'
            self.add_profiles(username=username, url=temp_url, resource='linkedin', category='social', notes=company_found)
            try:
                for parsed_url in parse_also_viewed(tree):
                    if (parsed_url not in temp_urls) and (parsed_url not in urls_queued):
                        temp_urls.append(parsed_url)
                        urls_queued.append(parsed_url)
            except IndexError:
                continue
        return cookiej
