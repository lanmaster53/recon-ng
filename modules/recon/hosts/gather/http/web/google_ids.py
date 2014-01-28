import framework
# unique to module
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('url', None, 'yes', 'the URL of the website with the Analytics/AdSense code')
        self.info = {
                     'Name': 'Google Analytics/AdSense Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Provide this module with a URL (or domain) and it will visit that page and look for a Google Analytics "UA-#####" and Google AdSense "pub-####" ID in the page source. Then it will look up other sites that use that same code. This can show you sites that may be administered or coded by a single group.',
                     'Comments': []
                     }
                     
    def lookup_ewhois(self, val, key):
        self.alert('Found Code: %s' % val)
        # use the ewhois AJAX API to look up the vals
        #http://www.ewhois.com/ajax/reverse/?key=email&val=makeuseof.com%40domainsbyproxy.com
        #http://www.ewhois.com/ajax/reverse/?key=analytics&val=UA-730874
        #http://www.ewhois.com/ajax/reverse/?key=adsense&val=pub-5700237260308472
        url = 'http://www.ewhois.com/ajax/reverse/?key=%s&val=%s' % (key, val)
        self.verbose('Searching \'%s\' for other domains...' % url)
        resp = self.request(url)
        content = resp.json['html']
        # pagination not implemented
        # not sure if the below portion would even work
        multi_pages = re.search('page:2', content)
        if multi_pages:
            self.error("More than one page of results returned on the %s site." % url)
            self.error("Please visit manually to retrieve other entries.")
        return re.findall('<div class="row"><a[^>]*>(.+?)</a>', content)
   
    def module_run(self):
        results = []
        # visit target URL and scrape for codes
        url_target_site = self.options['url']
        if re.search('^https*://', url_target_site):
            self.verbose('Retrieving source for: %s' % url_target_site)
            resp = self.request(url_target_site)
            content = resp.text
            code_an = re.findall('["\'](UA-\d+)', content)          # Analytics ID
            code_ad = re.findall('["\'](?:ca-)*(pub-\d+)', content) # AdSense ID
            if any((code_an, code_ad)):
                for code in set(code_an):
                    results += self.lookup_ewhois(code, 'analytics')
                for code in set(code_ad):
                    results += self.lookup_ewhois(code, 'adsense')
                results = set([x.lower() for x in results])
                cnt = 0
                new = 0
                for domain in results:
                    self.alert(domain)
                    cnt += 1
                    new += self.add_host(domain)
                self.output('%d total hosts found.' % (cnt))
                if new: self.alert('%d NEW hosts found!' % (new))
            else:
                self.output('No Google Analytics or AdSense ID found in target URL source.')
        else:
            self.error('The URL parameter (%s) is not a recognized URL. Please re-enter one in the "http[s]://example.com" format.' % url_target_site)
