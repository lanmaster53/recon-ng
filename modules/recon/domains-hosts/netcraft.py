from recon.core.module import BaseModule
from recon.utils.requests import encode_payload
from cookielib import CookieJar
import urllib
import re
import hashlib
import time
import random

class Module(BaseModule):

    meta = {
        'name': 'Netcraft Hostname Enumerator',
        'author': 'thrapt (thrapt@gmail.com)',
        'description': 'Harvests hosts from Netcraft.com. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        url = 'http://searchdns.netcraft.com/'
        pattern = '<td align\=\"left\">\s*<a href=\"http://(.*?)/"'
        # answer challenge cookie
        cookiejar = CookieJar()
        payload = {'restriction': 'site+ends+with', 'host': 'test.com'}
        resp = self.request(url, payload=payload, cookiejar=cookiejar)
        cookiejar = resp.cookiejar
        for cookie in cookiejar:
            if cookie.name == 'netcraft_js_verification_challenge':
                challenge = cookie.value
                response = hashlib.sha1(urllib.unquote(challenge)).hexdigest()
                cookiejar.set_cookie(self.make_cookie('netcraft_js_verification_response', '%s' % response, '.netcraft.com'))
                break
        for domain in domains:
            self.heading(domain, level=0)
            payload['host'] = domain
            subs = []
            # execute search engine queries and scrape results storing subdomains in a list
            # loop until no Next Page is available
            while True:
                self.verbose('URL: %s?%s' % (url, encode_payload(payload)))
                resp = self.request(url, payload=payload, cookiejar=cookiejar)
                content = resp.text
                sites = re.findall(pattern, content)
                # create a unique list
                sites = list(set(sites))
                # add subdomain to list if not already exists
                for site in sites:
                    if site not in subs:
                        subs.append(site)
                        self.add_hosts(site)
                # verifies if there's more pages to look while grabbing the correct 
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
            if not subs:
                self.output('No results found.')
