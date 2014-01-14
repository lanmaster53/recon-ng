import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('url', None, 'yes', 'the URL of the website with the Analytics/AdSense code')
        self.info = {
                     'Name': 'Google Analytics/AdSense Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Provide this module with a URL (or domain) and it will visit that page and look for a Google Analytics "UA-#####" and Google AdSense "pub-####" ID in the page source. Then it will look up other sites that use that same code. This can show you sites that may be administered or coded by a single group.',
                     'Comments': []
                     }
                     
    def lookup_ewhois(self, code):
        self.alert('Found Code: %s' % code)
        # Now go look up the code in the ewhois site and scrape results
        if code.startswith("UA"):
            ewhois_url = 'http://www.ewhois.com/analytics-id/%s/' % code ### Analytics
        else:
            ewhois_url = 'http://www.ewhois.com/adsense-id/%s/' % code   ### AdSense
        self.verbose('Searching %s for other domains' % ewhois_url)
        ewhois_resp = self.request(ewhois_url)
        ewhois_content = ewhois_resp.text
        multi_pages = re.search('page:2', ewhois_content)
        if multi_pages:
            self.error("More than one page of results returned on the %s site." % ewhois_url)
            self.error("Please visit manually to retrieve other entries.")
        return re.findall('<div class="row"><a[^>]*>(.+?)</a>', ewhois_content)
   
    def module_run(self):
        results_ana = results_ad = set()
        # Visit Target URL and scrape for codes
        url_target_site = self.options['url']
        if re.search('^https*://', url_target_site):
            self.verbose('Retrieving source for: %s' % url_target_site)
            resp = self.request(url_target_site)
            content = resp.text
            
            code_ana = re.findall('["\'](UA-\d+)', content) ### Analytics ID
            code_ad  = re.search('["\'](pub-\d+)', content) ### AdSense ID
            if code_ana:
                for code in code_ana:
                    results_ana = results_ana.union(self.lookup_ewhois(code))
            if code_ad:  results_ad  = set(self.lookup_ewhois(code_ad.group(1)))
            if not code_ana and not code_ad:
                self.output('No Google Analytics or AdSense ID found in target URL source.')
            else:
                total_results = results_ana.union(results_ad)
                for domain in sorted(total_results):
                    self.alert(domain)
        else:
            self.error('The URL parameter (%s) is not a recognized URL. Please re-enter one in the "http[s]://example.com" format.' % url_target_site)
