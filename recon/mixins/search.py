from lxml.html import fromstring
from cookielib import CookieJar
import os
import re
import tempfile
import urllib
import webbrowser

class GoogleWebMixin(object):

    cookiejar = CookieJar()
    user_agent = 'Lynx/2.8.8dev.3 libwww-FM/2.14 SSL-MM/1.4.1'

    def search_google_web(self, query, limit=0, start_page=1):
        # parsing logic based on https://github.com/maurosoria/s3arch
        url = 'https://www.google.com/search'
        num = 100
        page = start_page
        set_page = lambda x: (x - 1) * num
        payload = {'q':query, 'start':set_page(page), 'num':num, 'complete':0}
        results = []
        self.verbose('Searching Google for: %s' % (query))
        while True:
            resp = self.request(url, payload=payload, redirect=False, cookiejar=self.cookiejar, agent=self.user_agent)
            # detect and handle captchas
            # results = 200, first visit = 302, actual captcha = 503
            count = 0
            if resp.status_code != 200:
                if resp.status_code == 302:
                    self.error('Google CAPTCHA triggered. No bypass available.')
                else:
                    self.error('Google encountered an unknown error.')
                break
            tree = fromstring(resp.text)
            links = tree.xpath('//a/@href')
            regmatch = re.compile('^/url\?q=[^/]')
            for link in links:
                if regmatch.match(link) != None and 'http://webcache.googleusercontent.com' not in link:
                    results.append(urllib.unquote_plus(link[7:link.find('&')]))
            # check limit
            if limit == page:
                break
            page += 1
            payload['start'] = set_page(page)
            # check for more pages
            if '>Next</' not in resp.text:
                break
        return results
