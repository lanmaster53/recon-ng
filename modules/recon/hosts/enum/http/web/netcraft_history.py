import framework
# unique to module
from cookielib import CookieJar
import re
import hashlib
import urllib
import time
import random

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Hosting History',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Checks Netcraft.com for the hosting history of the given target(s).',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                  ]
                     }

    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')

        cookiejar = CookieJar()
        url = 'http://toolbar.netcraft.com/site_report?url=www.google.com'
        resp = self.request(url, cookiejar=cookiejar)
        cookiejar = resp.cookiejar
        for cookie in cookiejar:
            if cookie.name == 'netcraft_js_verification_challenge':
                challenge = cookie.value
                response = hashlib.sha1(urllib.unquote(challenge)).hexdigest()
                cookiejar.set_cookie(self.make_cookie('netcraft_js_verification_response', '%s' % response, '.netcraft.com'))
                break

        for host in hosts:
            url = 'http://toolbar.netcraft.com/site_report?url=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url, cookiejar=cookiejar)
            content = resp.text

            # instantiate history list
            history = []            
            section = re.findall(r'<section.*?id="history_table">(?:\s|.)+?<\/section>', content)
            rows = re.findall(r'<tr class="T\wtr\d*">(?:\s|.)+?<\/tr>', section[0])

            for row in rows:
                cell = re.findall(r'>(.*?)<', row)
                raw  = [cell[0], cell[1], cell[2], cell[3], cell[4]]
                history.append([x.strip() for x in raw])

            if len(history) > 0:
                header = ['OS', 'Server', 'Last Changed', 'IP Address', 'Owner']
                history.insert(0, header)
                self.table(history, True)
            else:
                self.output('No results found')

            if len(hosts) > 1:
                # sleep script to avoid lock-out
                self.verbose('Sleeping to Avoid Lock-out...')
                time.sleep(random.randint(5,15))
