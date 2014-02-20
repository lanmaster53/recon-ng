import module
# unique to module
from cookielib import CookieJar
import urllib
import re
import hashlib
import time
import random

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.info = {
                     'Name': 'Netcraft Hostname Enumerator',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Harvests hosts from Netcraft.com and updates the \'hosts\' table of the database with the results.',
                     }

    def module_run(self):
        domain = self.options['domain']
        url = 'http://searchdns.netcraft.com/'        
        payload = {'restriction': 'site+ends+with', 'host': domain}
        pattern = '<td align\=\"left\">\s*<a href=\"http://(.*?)/"'
        subs = []
        cnt = 0

        cookiejar = CookieJar()
        resp = self.request(url, payload=payload, cookiejar=cookiejar)
        cookiejar = resp.cookiejar
        for cookie in cookiejar:
            if cookie.name == 'netcraft_js_verification_challenge':
                challenge = cookie.value
                response = hashlib.sha1(urllib.unquote(challenge)).hexdigest()
                cookiejar.set_cookie(self.make_cookie('netcraft_js_verification_response', '%s' % response, '.netcraft.com'))
                break

        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no Next Page is available
        while True:
            self.verbose('URL: %s?%s' % (url, urllib.urlencode(payload)))
            resp = self.request(url, payload=payload, cookiejar=cookiejar)
            content = resp.text

            sites = re.findall(pattern, content)
            # create a unique list
            sites = list(set(sites))
            
            # add subdomain to list if not already exists
            for site in sites:
                if site not in subs:
                    subs.append(site)
                    self.output('%s' % (site))
                    cnt += self.add_host(site)
            
            # Verifies if there's more pages to look while grabbing the correct 
            # values for our payload...
            link = re.findall(r'(\blast\=\b|\bfrom\=\b)(.*?)&', content)
            if not link:
                break
            else:
                payload['last'] = link[0][1]
                payload['from'] = link[1][1]
                self.verbose('Next page available! Requesting again...' )
                # sleep script to avoid lock-out
                self.verbose('Sleeping to Avoid Lock-out...')
                time.sleep(random.randint(5,15))

        self.verbose('Final Query String: %s?%s' % (url, urllib.urlencode(payload)))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
