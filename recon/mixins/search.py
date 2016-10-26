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
            #resp = None
            # google errors out at > 2061 characters not including the protocol
            # 21 (resource-proto) + 1 (?) + 8 (num) + 11 (complete) + 7 + len(start) + 3 + len(encoded(query))
            #max_len = 2061 - 21 - 1 - 8 - 11 - 7 - len(payload['start']) - 3
            #if len(urllib.quote_plus(query)) > max_len: query = query[:max_len]
            resp = self.request(url, payload=payload, redirect=False, cookiejar=self.cookiejar, agent=self.user_agent)
            # detect and handle captchas until answered correctly
            # first visit = 302, actual captcha = 503
            # follow the redirect to the captcha
            count = 0
            while resp.status_code == 302:
                redirect = resp.headers['location']
                # request the captcha page
                resp = self.request(redirect, redirect=False, cookiejar=self.cookiejar, agent=self.user_agent)
                count += 1
                # account for the possibility of infinite redirects
                if count == 20:
                    break
            # handle the captcha
            # check needed because the redirect could result in an error
            # will properly exit the loop and fall to the error check below
            if resp.status_code == 503:
                resp = self._solve_google_captcha(resp)
                continue
            # handle error conditions
            if resp.status_code != 200:
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

    def _solve_google_captcha(self, resp):
        # set up the captcha page markup for parsing
        tree = fromstring(resp.text)
        # extract and request the captcha image
        resp = self.request('https://ipv4.google.com' + tree.xpath('//img/@src')[0], redirect=False, cookiejar=self.cookiejar, agent=self.user_agent)
        # store the captcha image to the file system
        with tempfile.NamedTemporaryFile(suffix='.jpg') as fp:
            fp.write(resp.raw)
            fp.flush()
            # open the captcha image for viewing in gui environments
            w = webbrowser.get()
            w.open('file://' + fp.name)
            self.alert(fp.name)
            _payload = {'captcha':raw_input('[CAPTCHA] Answer: ')}
            # temporary captcha file removed on close
        # extract the form elements for the capctah answer request
        form = tree.xpath('//form[@action="index"]')[0]
        for x in ['q', 'continue', 'submit']:
            _payload[x] = form.xpath('//input[@name="%s"]/@value' % (x))[0]
        # send the captcha answer
        return self.request('https://ipv4.google.com/sorry/index', payload=_payload, cookiejar=self.cookiejar, agent=self.user_agent)
