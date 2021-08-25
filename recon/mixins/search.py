from lxml.html import fromstring
from http.cookiejar import CookieJar
from recon.core import framework
import os
import re
import time
import urllib.parse
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
        headers = {'user-agent': self.user_agent}
        results = []
        self.verbose(f"Searching Google for: {query}")
        while True:
            resp = self.request('GET', url, params=payload, headers=headers, allow_redirects=False, cookies=self.cookiejar)
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
            regmatch = re.compile(r'^/url\?q=[^/]')
            for link in links:
                if regmatch.match(link) != None and 'http://webcache.googleusercontent.com' not in link:
                    results.append(urllib.parse.unquote_plus(link[7:link.find('&')]))
            # check limit
            if limit == page:
                break
            page += 1
            payload['start'] = set_page(page)
            # check for more pages
            if '>Next</' not in resp.text:
                break
        return results


class GoogleAPIMixin(object):

    def search_google_api(self, query, limit=0):
        api_key = self.get_key('google_api')
        cse_id = self.get_key('google_cse')
        url = 'https://www.googleapis.com/customsearch/v1'
        payload = {'alt': 'json', 'prettyPrint': 'false', 'key': api_key, 'cx': cse_id, 'q': query}
        results = []
        cnt = 0
        self.verbose(f"Searching Google API for: {query}")
        while True:
            resp = self.request('GET', url, params=payload)
            if resp.json() == None:
                raise framework.FrameworkException(f"Invalid JSON response.{os.linesep}{resp.text}")
            # add new results
            if 'items' in resp.json():
                results.extend(resp.json()['items'])
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # check for more pages
            if not 'nextPage' in resp.json()['queries']:
                break
            payload['start'] = resp.json()['queries']['nextPage'][0]['startIndex']
        return results


class BingAPIMixin(object):

    def search_bing_api(self, query, limit=0):
        url = 'https://api.bing.microsoft.com/v7.0/search'
        payload = {'q': query, 'count': 50, 'offset': 0, 'responseFilter': 'WebPages'}
        headers = {'Ocp-Apim-Subscription-Key': self.get_key('bing_api')}
        results = []
        cnt = 0
        self.verbose(f"Searching Bing API for: {query}")
        while True:
            resp = self.request('GET', url, params=payload, headers=headers)
            if resp.json() == None:
                raise framework.FrameworkException(f"Invalid JSON response.{os.linesep}{resp.text}")
            #elif 'error' in resp.json():
            elif resp.status_code == 401:
                error = resp.json()['error']
                raise framework.FrameworkException(f"({error['code']}) {error['message']}")
            # add new results, or if there's no more, return what we have...
            if 'webPages' in resp.json():
                results.extend(resp.json()['webPages']['value'])
            else:
                return results
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # check for more pages
            # https://msdn.microsoft.com/en-us/library/dn760787.aspx
            if payload['offset'] > (resp.json()['webPages']['totalEstimatedMatches'] - payload['count']):
                break
            # set the payload for the next request
            payload['offset'] += payload['count']
        return results


class ShodanAPIMixin(object):

    def search_shodan_api(self, query, limit=0):
        api_key = self.get_key('shodan_api')
        url = 'https://api.shodan.io/shodan/host/search'
        payload = {'query': query, 'key': api_key}
        results = []
        cnt = 0
        page = 1
        self.verbose(f"Searching Shodan API for: {query}")
        while True:
            time.sleep(1)
            resp = self.request('GET', url, params=payload)
            if resp.json() == None:
                raise framework.FrameworkException(f"Invalid JSON response.{os.linesep}{resp.text}")
            if 'error' in resp.json():
                raise framework.FrameworkException(resp.json()['error'])
            if not resp.json()['matches']:
                break
            # add new results
            results.extend(resp.json()['matches'])
            # increment and check the limit
            cnt += 1
            if limit == cnt:
                break
            # next page
            page += 1
            payload['page'] = page
        return results
