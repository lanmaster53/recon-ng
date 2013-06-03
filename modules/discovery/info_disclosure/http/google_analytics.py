import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('url', '', 'yes', 'The URL of the website with the Analytics code.')
        self.info = {
                     'Name': 'Google Analytics Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Provide this module with a URL (or domain) and it will visit that page and look for a Google Analytics "UA-#####" number in the page source. Then it will look up other sites that use that same UA-###### code. This can show you sites that may be administered or coded by a single group.',
                     'Comments': []
                     }
   
    def module_run(self):
        # Visit Target URL and scrape for UA- code
        url_target_site = self.options['url']['value']
        if re.search('^https*://', url_target_site):
            self.verbose('Retrieving source for: %s' % url_target_site)
            resp = self.request(url_target_site)
            content = resp.text
            code = re.search('["\'](UA-\d+)', content)
            if code:
                self.alert('Found Analytics Code: %s' % code.group(1))
                # Now go look up the code in the ewhois site and scrape results
                ewhois_url = 'http://www.ewhois.com/analytics-id/%s/' % code.group(1)
                self.verbose('Searching %s for other domains' % ewhois_url)
                ewhois_resp = self.request(ewhois_url)
                ewhois_content = ewhois_resp.text
                domains = re.findall('<div class="row"><a[^>]*>(.+?)</a>', ewhois_content)
                domains.sort()
                for domain in domains:
                    self.alert(domain)        
            else:
                self.output('No Google Analytics code found in target URL source.')
        else:
            self.output('The URL parameter (%s) is not a recognized URL. Please re-enter one in the "http[s]://example.com" format.' % url_target_site)